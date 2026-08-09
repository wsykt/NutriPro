"""回答质量统计 API 路由

由原 main.py 拆分而来，对应"回答质量统计"业务域：
- POST /api/v1/quality/score   对一条 AI 回答进行质量评分
- GET  /api/v1/quality/stats   回答质量统计概览（真实数据）
"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()

_quality_records = []  # 质量评分记录（用于可视化）
_MAX_QUALITY_RECORDS = 100


@router.post("/api/v1/quality/score")
async def quality_score(data: dict):
    """对一条 AI 回答进行质量评分"""
    from utils.quality_scorer import scorer
    question = data.get("question", "")
    response = data.get("response", "")
    kb_used = data.get("kb_used", False)
    result = scorer.score(question, response, kb_used)
    # 记录
    _quality_records.append({
        "question_preview": question[:50],
        "score": result["score"],
        "issues": result["issues"],
        "warnings": result["warnings"],
        "has_diagnosis": result["has_diagnosis"],
        "timestamp": datetime.now().isoformat(),
    })
    if len(_quality_records) > _MAX_QUALITY_RECORDS:
        _quality_records.pop(0)
    return result


@router.get("/api/v1/quality/stats")
async def quality_stats():
    """回答质量统计概览（真实数据）"""
    if not _quality_records:
        return {"total_scores": 0, "avg_score": 0, "records": []}
    scores = [r["score"] for r in _quality_records]
    return {
        "total_scores": len(scores),
        "avg_score": round(sum(scores) / len(scores), 1),
        "min_score": min(scores),
        "max_score": max(scores),
        "issues_count": sum(1 for r in _quality_records if r["issues"]),
        "recent_records": _quality_records[-10:],
    }
