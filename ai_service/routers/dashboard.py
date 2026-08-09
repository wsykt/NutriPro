"""可视化面板静态页面路由

由原 main.py 拆分而来，对应"可视化面板入口"业务域：
- GET /dashboard                     重定向到 /dashboard/
- GET /dashboard/{full_path:path}    提供可视化面板静态文件
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard", include_in_schema=False)
async def dashboard_page():
    """重定向到可视化面板"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/")


@router.get("/dashboard/{full_path:path}", include_in_schema=False)
async def serve_dashboard(full_path: str):
    """提供可视化面板静态文件"""
    import os as _os
    # 注：本模块位于 routers/ 子目录，dashboard 静态目录基准为 ai_service/（原 main.py 所在目录），
    # 因此路径基准需用 os.path.dirname(os.path.dirname(__file__)) 保持与原实现指向相同的真实目录。
    dashboard_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "dashboard")
    file_path = _os.path.join(dashboard_dir, full_path or "index.html")

    if not _os.path.exists(file_path) or not file_path.startswith(dashboard_dir):
        file_path = _os.path.join(dashboard_dir, "index.html")

    ext = _os.path.splitext(file_path)[1].lower()
    media_types = {".html": "text/html", ".js": "application/javascript", ".css": "text/css",
                   ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
                   ".json": "application/json"}

    from fastapi.responses import HTMLResponse, FileResponse
    if ext == ".html":
        with open(file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return FileResponse(file_path, media_type=media_types.get(ext, "application/octet-stream"))
