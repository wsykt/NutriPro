"""LLM 路由模块

原有代码保留所有功能，新增：
1. LLM 异常分类（超时/密钥失效/限流/未知）
2. chat() 增加 timeout 参数 + 递增间隔重试
3. Token 用量记录
4. 支持 Ollama 本地后端（通过 LLM_MODE=local 切换）
"""

import json
import re
import time
import logging
from typing import Optional
import requests
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger(__name__)


# ============================================================
# LLM 异常分类
# ============================================================

class LLMTimeoutError(Exception):
    """LLM 请求超时"""
    pass

class LLMAuthError(Exception):
    """API 密钥失效"""
    pass

class LLMRateLimitError(Exception):
    """请求频率限制"""
    pass

class LLMUnknownError(Exception):
    """其他 LLM 异常"""
    pass


# ============================================================
# Token 用量追踪
# ============================================================

class TokenTracker:
    """Token 用量追踪——记录每日消耗与缓存命中，超限自动切换"""

    def __init__(self, db_path: str = None):
        self._db_path = db_path or settings.TOKEN_USAGE_DB
        self._init_db()
        self._daily_total = self._load_today()
        self._daily_cached = self._load_today("cached_tokens")

    def _init_db(self):
        from utils.sqlite_utils import init_db
        init_db(
            self._db_path,
            ddl_statements=["""
                CREATE TABLE IF NOT EXISTS token_usage (
                    date TEXT PRIMARY KEY,
                    total_tokens INTEGER DEFAULT 0,
                    cached_tokens INTEGER DEFAULT 0
                )
            """],
            indexes=[],
        )
        # 兼容旧表：早期版本没有 cached_tokens 列，动态补列（幂等）
        try:
            from utils.sqlite_utils import get_conn
            conn = get_conn(self._db_path)
            cursor = conn.cursor()
            cursor.execute(
                "ALTER TABLE token_usage ADD COLUMN cached_tokens INTEGER DEFAULT 0")
            conn.commit()
            conn.close()
        except Exception:
            pass  # 列已存在则忽略

    def _load_today(self, column: str = "total_tokens") -> int:
        from utils.sqlite_utils import get_conn
        today = time.strftime("%Y-%m-%d")
        conn = get_conn(self._db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"SELECT {column} FROM token_usage WHERE date=?", (today,))
            row = cursor.fetchone()
        finally:
            conn.close()
        return row[0] if row else 0

    def record(self, tokens: int, cached_tokens: int = 0):
        """记录本次消耗。cached_tokens 为上下文缓存命中的输入 token 数（DeepSeek 自动管理）"""
        from utils.sqlite_utils import get_conn
        today = time.strftime("%Y-%m-%d")
        self._daily_total += tokens
        self._daily_cached += cached_tokens
        conn = get_conn(self._db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO token_usage (date, total_tokens, cached_tokens) "
            "VALUES (?, "
            "COALESCE((SELECT total_tokens FROM token_usage WHERE date=?), 0) + ?, "
            "COALESCE((SELECT cached_tokens FROM token_usage WHERE date=?), 0) + ?)",
            (today, today, tokens, today, cached_tokens)
        )
        conn.commit()
        conn.close()

    @property
    def is_over_limit(self) -> bool:
        return self._daily_total >= settings.LLM_DAILY_TOKEN_LIMIT

    @property
    def cache_hit_rate(self) -> float:
        """今日缓存命中率：命中缓存 token / 今日总 token（0~1，无消耗为 0）"""
        if self._daily_total <= 0:
            return 0.0
        return round(min(self._daily_cached / self._daily_total, 1.0), 4)

    def log_cache_stats(self):
        """输出今日缓存命中统计（调试观测用，可接日志）"""
        logger.info(
            "TokenTracker 今日 total=%s cached=%s hit_rate=%.2f%%",
            self._daily_total, self._daily_cached, self.cache_hit_rate * 100,
        )


# ============================================================
# LLM 路由主类
# ============================================================

class LLMRouter:

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._token_tracker = TokenTracker()
        self._mode = settings.LLM_MODE  # cloud / local
        self._ollama_available = None   # None=未检测, bool=检测结果
        self._ollama_real_model = settings.OLLAMA_MODEL  # 实际可用模型名

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY is not configured")
            self._client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_API_BASE,
                timeout=settings.LLM_TIMEOUT,
            )
        return self._client

    def _ollama_check(self) -> bool:
        """检测 Ollama 服务是否可用（结果缓存）

        Ollama 的 /api/tags 返回的模型名通常带 :latest 后缀，
        这里做容错匹配：配置名是无后缀的短名时也能命中。
        """
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            resp = requests.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                # 精确匹配 OR 短名前缀匹配（应对 :latest 后缀）
                target = settings.OLLAMA_MODEL
                matched = target in models or any(
                    m.startswith(target + ":") for m in models)
                if matched:
                    # 记录实际可用的完整模型名，供 _ollama_chat 使用
                    self._ollama_real_model = next(
                        (m for m in models if m == target or m.startswith(target + ":")),
                        target)
                    self._ollama_available = True
                    logger.info(f"Ollama 可用，模型: {self._ollama_real_model}")
                else:
                    self._ollama_available = False
                    logger.warning(
                        f"Ollama 运行中但模型 {target} 不存在，"
                        f"可用: {models}")
            else:
                self._ollama_available = False
        except Exception as e:
            self._ollama_available = False
            logger.warning(f"Ollama 不可用: {e}")
        return self._ollama_available

    def _ollama_chat(self, messages: list) -> str:
        """Ollama 本地对话（保持与云端 chat() 接口一致）"""
        # 模型不可用时给出明确错误，由上层降级处理
        if not self._ollama_check():
            raise LLMUnknownError(
                f"Ollama 服务不可用或模型 {settings.OLLAMA_MODEL} 未加载")

        # 使用实际匹配到的完整模型名（可能带 :latest 后缀）
        real_model = getattr(self, "_ollama_real_model", settings.OLLAMA_MODEL)
        # 本地模式使用独立超时（OLLAMA_TIMEOUT，默认180s大值观察实际耗时）
        # 不与云端 LLM_TIMEOUT（默认30s）共享，避免复杂prompt超时
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": real_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": settings.OLLAMA_TEMPERATURE,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                },
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        if resp.status_code != 200:
            raise LLMUnknownError(
                f"Ollama 响应错误 {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        # 记录 token 用量（Ollama 返回 eval_count / prompt_eval_count）
        usage = data.get("usage", {}) or {}
        total = usage.get("total_tokens") or (
            usage.get("prompt_eval_count", 0) + usage.get("eval_count", 0))
        if total:
            self._token_tracker.record(total)
        return content or ""
    def _classify_exception(self, e: Exception) -> Exception:
        """将 OpenAI 原生异常分类为项目内部异常"""
        error_msg = str(e).lower()
        if "timeout" in error_msg or "timed out" in error_msg:
            return LLMTimeoutError(f"LLM 请求超时（{settings.LLM_TIMEOUT}s）: {e}")
        if "auth" in error_msg or "key" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
            return LLMAuthError(f"API 密钥失效: {e}")
        if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
            return LLMRateLimitError(f"请求频率限制: {e}")
        return LLMUnknownError(f"LLM 未知异常: {e}")

    def _extract_cache_hit(self, usage) -> int:
        """从 usage 提取上下文缓存命中 token 数。

        兼容两种字段：Chat Completions 的 prompt_tokens_details.cached_tokens，
        Responses API 的 input_tokens_details.cached_tokens（DeepSeek 自动管理缓存）。
        """
        try:
            details = (
                getattr(usage, "prompt_tokens_details", None)
                or getattr(usage, "input_tokens_details", None)
            )
            if details and getattr(details, "cached_tokens", None):
                return int(details.cached_tokens)
        except Exception:
            pass
        return 0

    @staticmethod
    def _messages_to_responses_input(messages: list):
        """把 Chat Completions 的 messages 转换为 Responses API 的 instructions + input。

        - 第一条 system 消息提升为 instructions（Responses API 约定）
        - 其余 system 消息保留为 system 角色 input item
        - user / assistant 消息原样保留
        """
        instructions = None
        items = []
        for m in messages or []:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                if instructions is None:
                    instructions = content
                else:
                    items.append({"role": "system", "content": content})
            else:
                items.append({"role": role, "content": content})
        return instructions, items

    def _call_responses_api(self, messages: list, model_name: str, req_timeout: int,
                            temperature: Optional[float], json_mode: bool = False) -> str:
        """Responses API 单次调用（非流式），统一由 chat() 外层循环负责重试。

        json_mode=True 时通过 text.format 声明式约束输出为合法 JSON（方案4），
        从源头消除 chat_json 的"生成→正则修复→重试"链路。
        """
        instructions, input_items = self._messages_to_responses_input(messages)
        request_kwargs = dict(
            model=model_name or settings.RESPONSES_MODEL,
            instructions=instructions or "You are a helpful assistant.",
            input=input_items,
            temperature=temperature if temperature is not None else 0.7,
            timeout=req_timeout,
        )
        if json_mode:
            # 实测支持 json_object / json_schema / strict 三种写法；用最通用的 json_object
            request_kwargs["text"] = {"type": "json_object"}
        resp = self.client.responses.create(**request_kwargs)
        # 记录 Token 用量 + 缓存命中
        if hasattr(resp, "usage") and resp.usage:
            self._token_tracker.record(
                resp.usage.total_tokens,
                cached_tokens=self._extract_cache_hit(resp.usage),
            )
        return resp.output_text if hasattr(resp, "output_text") else ""

    def _chat_stream_responses(self, messages: list, model: Optional[str],
                               timeout: Optional[int]):
        """Responses API 语义化流式（方案1）。

        事件语义：output_text.delta 增量 → completed / incomplete / failed 明确结束态。
        调用方（routers/chat.py）据此区分"正常完成 / 被截断 / 失败"，无需再猜 DONE。
        """
        instructions, input_items = self._messages_to_responses_input(messages)
        try:
            stream = self.client.responses.create(
                model=model or settings.RESPONSES_MODEL,
                instructions=instructions or "You are a helpful assistant.",
                input=input_items,
                temperature=0.7,
                stream=True,
                timeout=timeout if timeout is not None else settings.LLM_TIMEOUT,
            )
            for event in stream:
                etype = getattr(event, "type", "")
                if etype == "response.output_text.delta":
                    delta = getattr(event, "delta", None)
                    if delta:
                        yield delta
                elif etype == "response.completed":
                    # 结束态：完整 response 挂载在 event.response，读取 usage 记录缓存命中
                    resp_obj = getattr(event, "response", None)
                    usage = getattr(resp_obj, "usage", None) if resp_obj else None
                    if usage:
                        self._token_tracker.record(
                            usage.total_tokens,
                            cached_tokens=self._extract_cache_hit(usage),
                        )
                elif etype in ("response.incomplete", "response.failed"):
                    yield f"\n\n[响应未完成: {etype}]"
                    return
        except Exception as e:
            yield f"\n\n[流式响应异常: {self._classify_exception(e)}]"

    def chat(self, messages: list, model: Optional[str] = None, max_retries: int = 2,
             timeout: Optional[int] = None, temperature: Optional[float] = None,
             mode: Optional[str] = None, json_mode: bool = False) -> str:
        """带超时和重试的对话方法

        根据 LLM_MODE 分流：
        - cloud：调用 DeepSeek 云端 API（原有逻辑）
        - local：调用 Ollama 本地大模型

        timeout 参数：单次请求覆盖全局超时（如高性能演示模式可放宽），默认用 settings.LLM_TIMEOUT

        mode 参数：本次调用临时指定 local/cloud，仅本次生效，不修改全局 self._mode
        （None 时使用 self._mode，与原有行为完全一致）。用于消除并发线程间
        直接改写共享 _mode 导致的本地/云端调用串台。

        json_mode 参数：仅对云端 Responses API 生效（方案4）——通过 text.format
        声明式约束输出为合法 JSON，供 chat_json 使用；本地 Ollama 路径忽略该参数。

        重试策略：
        - 超时/限流：2 次递增间隔重试（1s, 2s）
        - 密钥失效：不重试，直接抛出 AuthError
        - 其他异常：重试 1 次
        """
        # Token 超限检查
        if self._token_tracker.is_over_limit:
            raise LLMRateLimitError(f"今日 Token 用量已达上限（{settings.LLM_DAILY_TOKEN_LIMIT}）")

        # 本地模式分流（mode 参数局部生效，不修改 self._mode）
        effective_mode = mode or self._mode
        if effective_mode == "local":
            return self._ollama_chat(messages)

        # 云端模式（原有逻辑 / Responses API 开关分流）
        model_name = model or settings.DEEPSEEK_MODEL
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                req_timeout = timeout if timeout is not None else settings.LLM_TIMEOUT
                if settings.RESPONSES_API_ENABLED:
                    # 方案1：Responses API（仅 deepseek-v4-flash），语义化结束态
                    # 方案4：json_mode 时声明式约束 JSON 输出
                    content = self._call_responses_api(
                        messages, model_name, req_timeout, temperature,
                        json_mode=json_mode)
                else:
                    resp = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=temperature if temperature is not None else 0.7,
                        timeout=req_timeout,
                    )
                    content = resp.choices[0].message.content
                    # 记录 Token 用量 + 缓存命中
                    if hasattr(resp, 'usage') and resp.usage:
                        self._token_tracker.record(
                            resp.usage.total_tokens,
                            cached_tokens=self._extract_cache_hit(resp.usage),
                        )
                return content if content else ""
            except Exception as e:
                classified = self._classify_exception(e)
                last_exception = classified

                # 密钥失效——不重试，立即抛出
                if isinstance(classified, LLMAuthError):
                    raise classified

                # 超时/限流——递增间隔重试
                if attempt < max_retries:
                    delay = (attempt + 1) * 1.0
                    time.sleep(delay)
                    continue

        raise last_exception

    def chat_stream(self, messages: list, model: Optional[str] = None, timeout: Optional[int] = None):
        """流式对话（增强：增加超时 + 异常捕获）"""
        if settings.RESPONSES_API_ENABLED:
            # 方案1：Responses API 语义化流式（事件自带结束态，无需猜 DONE）
            yield from self._chat_stream_responses(messages, model, timeout)
            return

        model_name = model or settings.DEEPSEEK_MODEL
        try:
            stream = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                stream=True,
                timeout=timeout if timeout is not None else settings.LLM_TIMEOUT,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            yield f"\n\n[流式响应异常: {self._classify_exception(e)}]"

    def classify_difficulty(self, query: str) -> str:
        """（保持原有逻辑）"""
        score = 0
        high_kw = ["严重", "紧急", "异常", "报错", "无法", "卡死", "崩溃", "泄漏"]
        mid_kw = ["维修", "更换", "安装", "调试", "检查", "清洗", "保养", "校准"]
        low_kw = ["查询", "查看", "说明", "解释", "什么是", "如何", "步骤", "方法"]

        q = query.lower()
        for kw in high_kw:
            if kw in q:
                score += 3
        for kw in mid_kw:
            if kw in q:
                score += 2
        for kw in low_kw:
            if kw in q:
                score += 1
        if len(query) > 100:
            score += 2
        elif len(query) > 50:
            score += 1

        if score >= 6:
            return "high"
        elif score >= 3:
            return "medium"
        return "low"

    def safe_parse_json(self, text: str) -> dict:
        """（保持原有 JSON 解析逻辑）"""
        if not text or not isinstance(text, str):
            return {}

        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # ---- 新增：把字符串内部的多行未转义字符先转义（Ollama qwen2.5 常见问题） ----
        escaped = self._escape_newlines_in_json_strings(text)
        if escaped and escaped != text:
            try:
                return json.loads(escaped)
            except json.JSONDecodeError:
                pass

        try:
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                candidate = match.group()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # 也尝试对候选做字符串内换行转义
                    cand_esc = self._escape_newlines_in_json_strings(candidate)
                    if cand_esc and cand_esc != candidate:
                        try:
                            return json.loads(cand_esc)
                        except json.JSONDecodeError:
                            pass
                    fixed = self._fix_json(candidate)
                    if fixed:
                        return fixed
        except (json.JSONDecodeError, re.error):
            pass

        try:
            match = re.search(r'\[[\s\S]*\]', text)
            if match:
                candidate = match.group()
                try:
                    return {"items": json.loads(candidate)}
                except json.JSONDecodeError:
                    cand_esc = self._escape_newlines_in_json_strings(candidate)
                    if cand_esc and cand_esc != candidate:
                        try:
                            parsed = json.loads(cand_esc)
                            return {"items": parsed} if isinstance(parsed, list) else parsed
                        except json.JSONDecodeError:
                            pass
                    fixed = self._fix_json(candidate)
                    if fixed:
                        return {"items": fixed} if isinstance(fixed, list) else fixed
        except (json.JSONDecodeError, re.error):
            pass

        return {}

    def _escape_newlines_in_json_strings(self, text: str) -> str:
        """把 JSON 字符串字面量内部的换行/Tab/回车/未转义斜体引号等转义成合法的 JSON 转义序列。
        典型场景：qwen2.5 本地模型返回的 answer 里包含真实换行，导致 JSON 解析失败。
        """
        if not text:
            return text
        out = []
        in_string = False
        escape = False
        i = 0
        n = len(text)
        while i < n:
            ch = text[i]
            if not in_string:
                out.append(ch)
                if ch == '"' and not escape:
                    in_string = True
                escape = (ch == '\\' and not escape)
                i += 1
                continue
            # ---- in_string == True ----
            if escape:
                # 已经是转义字符，直接保留
                out.append(ch)
                escape = False
                i += 1
                continue
            if ch == '\\':
                out.append(ch)
                escape = True
                i += 1
                continue
            if ch == '"':
                # 字符串结束
                out.append(ch)
                in_string = False
                i += 1
                continue
            # 字符串内部：遇到控制字符转义
            if ch == '\n':
                out.append('\\n')
                i += 1
                continue
            if ch == '\r':
                # \r\n 合并成 \n
                if i + 1 < n and text[i + 1] == '\n':
                    out.append('\\n')
                    i += 2
                else:
                    out.append('\\n')
                    i += 1
                continue
            if ch == '\t':
                out.append('\\t')
                i += 1
                continue
            # 其他普通字符
            out.append(ch)
            i += 1
        return ''.join(out)

    def _fix_json(self, text: str):
        """尝试修复常见的 JSON 格式问题"""
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        text = re.sub(r'"\s*:\s*"', '": "', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def chat_json(self, messages: list, max_retries: int = 2, timeout: Optional[int] = None,
                  temperature: Optional[float] = None, mode: Optional[str] = None) -> dict:
        """带重试机制的 JSON 对话（复用 chat 的异常分类）

        mode 参数：本次调用临时指定 local/cloud，仅本次生效，不修改全局 self._mode
        （None 时使用全局模式，与原有行为完全一致）。

        方案4：当 RESPONSES_API_ENABLED 开启时自动启用 text.format json_object 约束，
        从源头保证合法 JSON；解析失败仍走原有"修复→重试"兜底。
        """
        for attempt in range(max_retries + 1):
            try:
                result = self.chat(messages, timeout=timeout, temperature=temperature,
                                   mode=mode, json_mode=settings.RESPONSES_API_ENABLED)
            except Exception:
                return {}

            parsed = self.safe_parse_json(result)

            if parsed:
                return parsed

            if attempt < max_retries:
                messages = messages + [
                    {"role": "assistant", "content": result},
                    {"role": "user", "content": "你上面的回复不是合法的JSON格式。请严格按照要求的JSON结构输出，不要包含任何markdown标记、解释文字或代码块标记，只输出纯JSON。"},
                ]

        return {}


llm = LLMRouter()
