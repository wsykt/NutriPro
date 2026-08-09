"""回答质检 + 健康反思 Agent

降级走 local_fallback_engine.py（由 orchestrator 统一处理）
免责声明走 services/disclaimer.py
"""

from agent.base import BaseAgent
from services.disclaimer import STANDARD_DISCLAIMER
from utils.quality_scorer import QualityScorer

# ============================================================
# AI 回答自动质检打分器（委托给 QualityScorer 统一实现）
# ============================================================

class QualityChecker:
    """AI 回答质量自动质检（兼容包装，实际委托给 QualityScorer）"""

    _scorer = QualityScorer()

    @classmethod
    def check(cls, question: str, response: str) -> dict:
        result = cls._scorer.score(question, response)
        return {
            "quality_score": result["score"],
            "level": "excellent" if result["score"] >= 90 else "good" if result["score"] >= 70 else "fair" if result["score"] >= 50 else "poor",
            "issues": [{"type": i, "severity": "critical", "detail": i} for i in result["issues"]] + [{"type": w, "severity": "minor", "detail": w} for w in result["warnings"]],
            "summary": f"AI回答质量评分: {result['score']}/100",
        }


quality_checker = QualityChecker()

HEALTH_REFLECTION_PROMPT = """你是AI回答反思分析Agent。

输入：完整对话历史、用户反馈评分+文字意见。

issue_type枚举：knowledge_gap / crowd_mismatch / wrong_suggest / format_error / other

输出JSON：
{
  "issue_type":"枚举取值",
  "analysis":"详细问题分析",
  "suggested_action":"优化方案"
}

仅输出JSON，禁止额外文字。

Few-Shot 示例：
输入：用户问题："糖尿病患者能吃香蕉吗？"，AI回答："香蕉GI值52，属于中GI水果，糖尿病患者可以适量食用，建议每次半根。"，评分：2，反馈意见："没告诉我能不能吃，回答了跟没回答一样"
输出：{"issue_type":"knowledge_gap","analysis":"用户期望得到一个明确的'能吃/不能吃'判断，但AI只给出了GI值数据，没有给出明确的饮食建议结论。","suggested_action":"回答中先给出明确结论'可以适量食用'，再用数据和食用建议支撑"}

输入：用户问题："我今年65岁了，吃什么对心脏好？"，AI回答："建议多运动、控制体重、少吃高脂食物"，评分：4，反馈意见："回答专业，但没有特别针对老年人"
输出：{"issue_type":"crowd_mismatch","analysis":"AI回答未针对老年人群给出特异性建议，缺少老年人心脏保护的具体饮食指南。","suggested_action":"根据用户年龄补充老年人心脏健康的具体饮食建议，如增加omega-3摄入、补充辅酶Q10等"}"""

HEALTH_STATUS_REFLECTION_PROMPT = """你是健康状况反思分析Agent。

输入：用户档案、健康数据、用户关注的健康问题。

任务：分析用户当前健康状况，识别潜在风险，生成改进计划。

输出JSON：
{
  "reflection_type": "health_status",
  "reflection": "健康状况综合分析，包括当前健康风险评估",
  "risk_level": "high / medium / low",
  "key_findings": ["发现1", "发现2"],
  "action_plan": ["行动计划1", "行动计划2", "行动计划3"],
  "tips": ["健康提示1", "健康提示2"]
}

约束：不提供医疗诊断，仅给出健康管理建议，附带免责声明。"""


class HealthReflectionAgent(BaseAgent):

    @staticmethod
    def reflect(question: str, response: str, rating: int = 3, reason: str = "") -> dict:
        messages = [
            {"role": "system", "content": "你是一个AI回答质量分析专家。只输出JSON。"},
            {"role": "user", "content": HEALTH_REFLECTION_PROMPT + f"\n\n用户问题：{question}\nAI回答：{response}\n评分：{rating}\n反馈意见：{reason}"},
        ]

        result = HealthReflectionAgent.chat_json(messages)
        if not result:
            raise ValueError("反思分析失败")

        return {
            "issue_type": result.get("issue_type", "other"),
            "analysis": result.get("analysis", ""),
            "suggested_action": result.get("suggested_action", ""),
        }

    @staticmethod
    def health_reflection(user_profile: dict, health_data: dict, concerns: list) -> dict:
        messages = [
            {"role": "system", "content": "你是一个专业健康状况分析专家。只输出JSON。"},
            {"role": "user", "content": HEALTH_STATUS_REFLECTION_PROMPT + f"\n\n用户档案：{user_profile}\n健康数据：{health_data}\n用户关注：{concerns}"},
        ]

        parsed = HealthReflectionAgent.chat_json(messages)
        if not parsed:
            raise ValueError("健康反思分析失败")

        reflection = parsed.get("reflection", "")
        reflection = HealthReflectionAgent.add_disclaimer(reflection)

        return {
            "reflection_type": parsed.get("reflection_type", "health_status"),
            "reflection": reflection,
            "risk_level": parsed.get("risk_level", "medium"),
            "key_findings": parsed.get("key_findings", []),
            "action_plan": parsed.get("action_plan", []),
            "tips": parsed.get("tips", []),
        }


agent = HealthReflectionAgent()
