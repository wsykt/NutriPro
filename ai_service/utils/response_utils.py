"""统一 API 响应包装器

提供标准化的成功/错误/分页响应格式，集中管理响应结构。
"""

from typing import Any, Optional

from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "success", **kwargs) -> dict:
    """统一成功响应

    {"success": true, "code": 200, "message": "...", "data": {...}, ...}

    自动附加本次请求的 LLM token 消耗明细（区分本地 Ollama / 云端 DeepSeek），
    字段名 tokens：{"local": {...}, "cloud": {...}, "total": N}。仅当本请求
    真实调用过大模型时才附加（total > 0），无调用（纯检索/纯数据处理）不附加。
    """
    response = {"success": True, "code": 200, "message": message}
    if data is not None:
        response["data"] = data
    response.update(kwargs)
    # 附加请求级 token 明细：延迟导入 llm.router 避免循环依赖
    try:
        from llm.router import llm as _llm_router
        tokens = _llm_router._token_tracker.drain_request_tokens()
        if tokens.get("total"):
            if data is None:
                response["data"] = {}
            elif not isinstance(response["data"], dict):
                response["data"] = {"value": response["data"]}
            response["data"]["tokens"] = tokens
    except Exception:
        pass  # token 统计失败不影响主响应
    return response


def error_response(
    message: str = "服务器内部错误",
    code: int = 500,
    detail: Optional[str] = None,
) -> JSONResponse:
    """统一错误响应

    {"success": false, "code": 500, "message": "...", "detail": "..."}
    """
    content = {"success": False, "code": code, "message": message}
    if detail is not None:
        content["detail"] = detail
    return JSONResponse(status_code=code, content=content)


def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """分页响应"""
    return {
        "success": True,
        "code": 200,
        "message": "success",
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items,
    }
