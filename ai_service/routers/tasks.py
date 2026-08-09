"""异步长任务 API 路由

由原 main.py 拆分而来，对应"新增：通用异步任务接口（阶段一·举措5）"业务域：
- GET  /api/v1/tasks           最近任务列表
- POST /api/v1/tasks/submit    提交后台长任务
- GET  /api/v1/tasks/{task_id} 查询任务状态与结果
- 后台任务实现 _task_article / _task_diet / _task_food_recommend /
  _task_exercise / _task_nutrition / _task_ollama_pull 与 TASK_HANDLERS 注册表
"""

from fastapi import APIRouter

# 全局编排器
from agent.orchestrator import orchestrator

# Ollama 管理：模型拉取走线程池
from services.ollama_manager import pull_model_sync

# 异步任务服务
from services.async_task_service import async_task_service

# 统一响应包装
from utils.response_utils import success_response, error_response

router = APIRouter()


def _task_article(payload: dict):
    """后台任务：科普文章生成（RAG 模式）"""
    return orchestrator.process(
        "article", payload.get("topic", ""), payload.get("target_crowd", "")
    )


def _task_diet(payload: dict):
    """后台任务：一日饮食方案"""
    return orchestrator.process(
        "diet", payload.get("user_profile", {}), payload.get("goal", ""),
        high_performance=payload.get("high_performance", False),
        today_diet=payload.get("today_diet", []),
        today_diet_total=payload.get("today_diet_total", {}),
        recent_exercise=payload.get("recent_exercise", {}),
        today_body_metrics=payload.get("today_body_metrics", {}),
    )


def _task_food_recommend(payload: dict):
    """后台任务：食材菜谱推荐"""
    return orchestrator.process(
        "food_recommend", payload.get("ingredients", []),
        payload.get("crowd_type", "普通人"), payload.get("goal", "健康饮食"),
        high_performance=payload.get("high_performance", False),
        user_profile=payload.get("user_profile", {}),
        today_diet=payload.get("today_diet", []),
        today_diet_total=payload.get("today_diet_total", {}),
        recent_exercise=payload.get("recent_exercise", {}),
        today_body_metrics=payload.get("today_body_metrics", {}),
    )


def _task_exercise(payload: dict):
    """后台任务：个性化运动方案"""
    return orchestrator.process(
        "exercise", payload.get("user_profile", {}), payload.get("goal", "保持健康"),
        payload.get("preferences", ""), payload.get("chronic_diseases", []),
        high_performance=payload.get("high_performance", False),
        today_diet=payload.get("today_diet", []),
        today_diet_total=payload.get("today_diet_total", {}),
        recent_exercise=payload.get("recent_exercise", {}),
        today_body_metrics=payload.get("today_body_metrics", {}),
    )


def _task_nutrition(payload: dict):
    """后台任务：营养分析"""
    return orchestrator.process(
        "nutrition", payload.get("user_profile", {}),
        payload.get("daily_nutrition", {}), payload.get("daily_exercise", {}),
    )


def _task_ollama_pull(payload: dict):
    """后台任务：拉取 Ollama 模型（耗时较长，走线程池避免阻塞事件循环）"""
    return pull_model_sync(payload.get("model", ""))


# 后台任务类型注册表（与 orchestrator agent 名对齐）
TASK_HANDLERS = {
    "article": _task_article,
    "diet": _task_diet,
    "food_recommend": _task_food_recommend,
    "exercise": _task_exercise,
    "nutrition": _task_nutrition,
    "ollama_pull": _task_ollama_pull,
}


@router.get("/api/v1/tasks")
async def task_list(limit: int = 20):
    """最近异步任务列表（按提交时间倒序，用于演示看板）"""
    return success_response(data={"tasks": async_task_service.list_recent(min(max(limit, 1), 50))})


@router.post("/api/v1/tasks/submit")
async def task_submit(data: dict):
    """提交后台长任务，立即返回 task_id，前端轮询 /api/v1/tasks/{task_id} 获取进度

    输入:
    {
        "task_type": "article | diet | food_recommend | exercise | nutrition",
        "payload": { ...对应端点的请求体... }
    }
    """
    task_type = data.get("task_type", "")
    payload = data.get("payload") or {}
    handler = TASK_HANDLERS.get(task_type)
    if handler is None:
        return error_response(
            message=f"不支持的任务类型: {task_type}，可选: {list(TASK_HANDLERS.keys())}",
            code=400, detail="UNSUPPORTED_TASK_TYPE",
        )
    task_id = async_task_service.submit(task_type, handler, payload)
    return success_response(
        data={"task_id": task_id, "status": "PENDING"},
        message=f"任务已提交后台执行，请轮询 GET /api/v1/tasks/{task_id} 获取进度",
    )


@router.get("/api/v1/tasks/{task_id}")
async def task_status(task_id: str):
    """查询异步任务状态与结果

    status: PENDING / RUNNING / SUCCESS / FAILED；成功时携带 result 完整结果
    """
    task = async_task_service.get(task_id)
    if task is None:
        return error_response(message="任务不存在或已过期清理", code=404, detail="TASK_NOT_FOUND")
    return success_response(data=task)
