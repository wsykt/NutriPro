"""统一 API 响应包装器

提供标准化的成功/错误/分页响应格式，集中管理响应结构。
"""

from typing import Any, Optional

from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "success", **kwargs) -> dict:
    """统一成功响应

    {"success": true, "code": 200, "message": "...", "data": {...}, ...}
    """
    response = {"success": True, "code": 200, "message": message}
    if data is not None:
        response["data"] = data
    response.update(kwargs)
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
