"""Ollama 本地大模型管理接口（阶段一·举措6）

为 AI 服务提供统一的 Ollama 管理能力：
- 健康检查：服务是否可用、版本、当前模式与生效配置
- 模型列表：已安装模型（/api/tags）+ 已加载模型（/api/ps，含上下文窗口/显存）
- 模型加载/卸载：通过 keep_alive 控制（/api/generate）
- 上下文窗口：查询与运行时调整 num_ctx（内存级覆盖，.env 为持久化源）
- 拉取模型：走后台任务避免阻塞事件循环（/api/pull）

统一读取 config.settings，不硬编码连接信息。
"""

import time
from typing import Dict, List, Optional

import requests

from config.settings import settings
from utils.log_config import get_logger

logger = get_logger("ollama_manager")

# num_ctx 合理范围（Ollama 限制 512~65536，6G 显存实测最大约 13000）
NUM_CTX_MIN = 512
NUM_CTX_MAX = 32768
# 加载模型的驻留时长（默认 30 分钟，配合 /api/ps 观察加载状态）
KEEP_ALIVE_LOADED = "30m"


class OllamaError(Exception):
    """Ollama 服务不可用或接口调用失败"""


class OllamaManager:
    """Ollama 管理门面（全部经 Ollama 原生 HTTP API 与 config.settings 交互）"""

    def __init__(self) -> None:
        self._num_ctx_override: Optional[int] = None  # 运行时上下文窗口覆盖（None=用配置值）

    # ---------------- 配置属性 ----------------

    @property
    def base_url(self) -> str:
        return settings.OLLAMA_BASE_URL

    @property
    def effective_num_ctx(self) -> int:
        """当前生效的上下文窗口：运行时覆盖优先，否则取配置文件"""
        return self._num_ctx_override or settings.OLLAMA_NUM_CTX

    @property
    def num_ctx_override(self) -> Optional[int]:
        """运行时覆盖值（None 表示未覆盖，使用 .env 配置）"""
        return self._num_ctx_override

    # ---------------- 健康检查 ----------------

    def health(self) -> Dict:
        """Ollama 服务健康检查（不抛异常，返回可用性结果）"""
        try:
            resp = requests.get(f"{self.base_url}/api/version", timeout=3)
            if resp.status_code == 200:
                version = resp.json().get("version", "")
                return {
                    "available": True,
                    "version": version,
                    "base_url": self.base_url,
                    "llm_mode": settings.LLM_MODE,
                    "configured_model": settings.OLLAMA_MODEL,
                    "num_ctx": self.effective_num_ctx,
                    "temperature": settings.OLLAMA_TEMPERATURE,
                    "timeout_seconds": settings.OLLAMA_TIMEOUT,
                }
            return {"available": False, "base_url": self.base_url,
                    "status_code": resp.status_code, "error": "Ollama 返回非 200"}
        except requests.exceptions.RequestException as e:
            return {"available": False, "base_url": self.base_url, "error": str(e)}

    # ---------------- 模型列表 ----------------

    def list_models(self) -> List[Dict]:
        """已安装模型列表（/api/tags）"""
        data = self._get_json("/api/tags")
        models = []
        for m in data.get("models", []):
            details = m.get("details", {}) or {}
            models.append({
                "name": m.get("name", ""),
                "model": m.get("model", ""),
                "size": m.get("size", 0),
                "modified_at": m.get("modified_at", ""),
                "parameter_size": details.get("parameter_size", ""),
                "quantization_level": details.get("quantization_level", ""),
                "family": details.get("family", ""),
            })
        return models

    def running_models(self) -> List[Dict]:
        """当前已加载（驻留内存）的模型列表（/api/ps，含上下文窗口与显存占用）

        兼容 Ollama 新旧版本字段：
        - 旧版: context.num_ctx
        - 新版（≥0.3.x）: 顶层 context_length
        """
        data = self._get_json("/api/ps")
        running = []
        for m in data.get("models", []):
            details = m.get("details", {}) or {}
            # num_ctx 字段兼容新旧结构
            ctx = 0
            if isinstance(m.get("context"), dict):
                ctx = m["context"].get("num_ctx", 0)
            if not ctx:
                ctx = m.get("context_length", 0)
            running.append({
                "name": m.get("name", ""),
                "model": m.get("model", ""),
                "size_vram": m.get("size_vram", 0),
                "expires_at": m.get("expires_at", ""),
                "num_ctx": ctx,
                "parameter_size": details.get("parameter_size", ""),
                "quantization_level": details.get("quantization_level", ""),
                "processor": m.get("processor", ""),
            })
        return running

    # ---------------- 加载 / 卸载 ----------------

    def load_model(self, model: str, num_ctx: Optional[int] = None) -> Dict:
        """将模型加载进内存并驻留（keep_alive=30m）

        num_ctx 缺省时沿用当前生效的上下文窗口配置。
        """
        if not model:
            raise OllamaError("缺少模型名")
        ctx = num_ctx or self.effective_num_ctx
        # 空 prompt + keep_alive 即可触发加载，不产生推理
        data = self._post_json("/api/generate", {
            "model": model,
            "prompt": "",
            "stream": False,
            "keep_alive": KEEP_ALIVE_LOADED,
            "options": {"num_ctx": ctx},
        }, timeout=120)
        return {
            "model": model,
            "num_ctx": ctx,
            "keep_alive": KEEP_ALIVE_LOADED,
            "done": data.get("done", False),
            "load_state": "loading",
        }

    def unload_model(self, model: str) -> Dict:
        """将模型从内存卸载（keep_alive=0）"""
        if not model:
            raise OllamaError("缺少模型名")
        self._post_json("/api/generate", {
            "model": model,
            "prompt": "",
            "stream": False,
            "keep_alive": 0,
        }, timeout=120)
        return {"model": model, "load_state": "unloaded"}

    # ---------------- 上下文窗口 ----------------

    def set_num_ctx(self, num_ctx: int) -> Dict:
        """运行时调整上下文窗口（内存级覆盖，重启后以 .env 为准）

        写入 settings.OLLAMA_NUM_CTX 供 LLM 路由实时生效。
        """
        if not (NUM_CTX_MIN <= num_ctx <= NUM_CTX_MAX):
            raise OllamaError(f"num_ctx 需在 {NUM_CTX_MIN}~{NUM_CTX_MAX} 之间，当前输入: {num_ctx}")
        self._num_ctx_override = num_ctx
        settings.OLLAMA_NUM_CTX = num_ctx
        logger.info(f"上下文窗口已调整 num_ctx={num_ctx}（运行时覆盖，.env 持久值={settings.OLLAMA_NUM_CTX if self._num_ctx_override is None else '见 .env'}）")
        return {
            "num_ctx": num_ctx,
            "runtime_override": True,
            "note": "运行时生效；如需持久化请同步修改 .env 中 OLLAMA_NUM_CTX",
        }

    # ---------------- 内部 HTTP 封装 ----------------

    def _get_json(self, path: str, timeout: int = 5):
        try:
            resp = requests.get(f"{self.base_url}{path}", timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise OllamaError(f"无法连接 Ollama 服务（{self.base_url}）: {e}")
        if resp.status_code != 200:
            raise OllamaError(f"Ollama 接口错误 {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def _post_json(self, path: str, payload: Dict, timeout: int = 60):
        try:
            resp = requests.post(f"{self.base_url}{path}", json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            raise OllamaError(f"无法连接 Ollama 服务（{self.base_url}）: {e}")
        if resp.status_code != 200:
            raise OllamaError(f"Ollama 接口错误 {resp.status_code}: {resp.text[:200]}")
        return resp.json()


ollama_manager = OllamaManager()


def pull_model_sync(model: str) -> Dict:
    """同步拉取模型（耗时较长，应由后台任务调用）"""
    if not model:
        return {"success": False, "error": "缺少 model 参数"}
    logger.info(f"开始拉取 Ollama 模型: {model}")
    start = time.time()
    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/pull",
            json={"model": model, "stream": False},
            timeout=1800,
        )
        elapsed = round(time.time() - start, 1)
        if resp.status_code != 200:
            return {"success": False, "error": f"Ollama 拉取失败 {resp.status_code}: {resp.text[:200]}", "elapsed_seconds": elapsed}
        data = resp.json()
        logger.info(f"Ollama 模型拉取完成: {model}，耗时 {elapsed}s")
        return {"success": True, "model": model, "status": data.get("status", ""), "elapsed_seconds": elapsed}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"无法连接 Ollama: {e}", "elapsed_seconds": round(time.time() - start, 1)}
