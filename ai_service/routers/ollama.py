"""Ollama 管理 API 路由

由原 main.py 拆分而来，对应"新增：Ollama 管理接口（阶段一·举措6）"业务域：
- GET  /api/v1/ollama/status              健康检查
- GET  /api/v1/ollama/models              模型列表
- POST /api/v1/ollama/models/load         加载模型
- POST /api/v1/ollama/models/unload       卸载模型
- POST /api/v1/ollama/models/pull         异步拉取模型
- GET  /api/v1/ollama/context-window      查询 num_ctx
- POST /api/v1/ollama/context-window      运行时调整 num_ctx
"""

from fastapi import APIRouter

from config.settings import settings

# Ollama 管理接口
from services.ollama_manager import ollama_manager, pull_model_sync, OllamaError

# 异步任务服务
from services.async_task_service import async_task_service

# 统一响应包装
from utils.response_utils import success_response, error_response

router = APIRouter()


@router.get("/api/v1/ollama/status")
async def ollama_status():
    """Ollama 健康检查：服务可用性、版本、LLM 模式与生效配置"""
    return success_response(data=ollama_manager.health())


@router.get("/api/v1/ollama/models")
async def ollama_models():
    """已安装模型 + 当前已加载（驻留内存）模型列表"""
    try:
        return success_response(data={
            "installed": ollama_manager.list_models(),
            "running": ollama_manager.running_models(),
        })
    except OllamaError as e:
        return error_response(message=str(e), code=503, detail="OLLAMA_UNAVAILABLE")


@router.post("/api/v1/ollama/models/load")
async def ollama_load(data: dict):
    """加载模型到内存并驻留（keep_alive=30m），num_ctx 可选覆盖"""
    try:
        model = data.get("model") or settings.OLLAMA_MODEL
        num_ctx = data.get("num_ctx")
        result = ollama_manager.load_model(model, num_ctx=num_ctx)
        return success_response(data=result, message=f"模型 {model} 加载指令已下发")
    except OllamaError as e:
        return error_response(message=str(e), code=503, detail="OLLAMA_UNAVAILABLE")


@router.post("/api/v1/ollama/models/unload")
async def ollama_unload(data: dict):
    """卸载模型，释放显存（keep_alive=0）"""
    try:
        model = data.get("model") or settings.OLLAMA_MODEL
        result = ollama_manager.unload_model(model)
        return success_response(data=result, message=f"模型 {model} 卸载指令已下发")
    except OllamaError as e:
        return error_response(message=str(e), code=503, detail="OLLAMA_UNAVAILABLE")


@router.post("/api/v1/ollama/models/pull")
async def ollama_pull(data: dict):
    """异步拉取模型（后台任务，前端轮询 /api/v1/tasks/{task_id} 获取进度）"""
    model = data.get("model", "")
    if not model:
        return error_response(message="缺少 model 参数", code=400, detail="MISSING_MODEL")
    task_id = async_task_service.submit("ollama_pull", pull_model_sync, model)
    return success_response(
        data={"task_id": task_id, "status": "PENDING", "model": model},
        message=f"模型 {model} 拉取任务已提交后台执行，请轮询 GET /api/v1/tasks/{task_id}",
    )


@router.get("/api/v1/ollama/context-window")
async def ollama_context_window_get():
    """查询当前生效的上下文窗口（num_ctx）"""
    return success_response(data={
        "num_ctx": ollama_manager.effective_num_ctx,
        "runtime_override": ollama_manager.num_ctx_override is not None,
    })


@router.post("/api/v1/ollama/context-window")
async def ollama_context_window_set(data: dict):
    """运行时调整上下文窗口 num_ctx（内存级覆盖，重启后以 .env 为准）"""
    try:
        num_ctx = int(data.get("num_ctx", 0))
        result = ollama_manager.set_num_ctx(num_ctx)
        return success_response(data=result, message=f"上下文窗口已调整为 {num_ctx}")
    except (ValueError, TypeError):
        return error_response(message="num_ctx 必须为整数", code=400, detail="INVALID_NUM_CTX")
    except OllamaError as e:
        return error_response(message=str(e), code=400, detail="INVALID_NUM_CTX")
