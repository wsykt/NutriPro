"""周报 Agent

依赖统一服务层：知识库检索走 services/retrieval_service.py
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
免责声明走 services/disclaimer.py
"""

from agent.base import BaseAgent
from services.disclaimer import STANDARD_DISCLAIMER

WEEKLY_REPORT_PROMPT = """你是健康周报文案生成Agent。

输入：用户一周营养统计、运动数据、人群标签。

任务：生成友好总结文案，包含本周亮点、风险、下周膳食建议。

输出JSON：
{
  "report_type": "weekly_health_report",
  "health_score": 85,
  "summary": "周报正文总结，包含本周整体健康状况评估",
  "highlights": ["本周亮点1", "本周亮点2"],
  "tips": ["小贴士1", "小贴士2"],
  "suggestions": ["建议1", "建议2"]
}

约束：禁止编造数据，文末附带膳食免责声明。

Few-Shot 示例：
输入：用户信息：{"crowd_type":"健身"}，本周统计：{"avg_calories":2600,"avg_protein":130,"avg_steps":10000,"active_days":5,"exercise_minutes":300}
输出：{"report_type":"weekly_health_report","health_score":88,"summary":"本周整体健康状况良好！运动天数达标（5天），蛋白质摄入充足（130g/天），步数活跃度优秀。建议下一周保持运动节奏，适当增加蔬菜和膳食纤维摄入。","highlights":["运动天数达标（5天）","日均步数10000步","运动时长300分钟，超额完成"],"tips":["日均饮水建议1500-1700ml","每餐保持一份蔬菜","训练后30分钟内补充蛋白质"],"suggestions":["继续保持高强度运动节奏","增加深绿色蔬菜摄入","保证充足睡眠7-8小时/天"]}"""


class WeeklyReportSummaryAgent(BaseAgent):

    @staticmethod
    def generate(user_profile: dict, weekly_stats: dict) -> dict:
        crowd_type = user_profile.get("crowd_type", "")
        kb_context = WeeklyReportSummaryAgent.get_kb_context(f"{crowd_type} 健康周报建议", top_k=2)

        prompt = WEEKLY_REPORT_PROMPT + "\n\n"
        prompt += f"用户信息：{user_profile}\n"
        prompt += f"本周统计：{weekly_stats}\n"
        prompt += kb_context

        messages = [
            {"role": "system", "content": "你是一个健康周报生成专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        parsed = WeeklyReportSummaryAgent.chat_json(messages)

        summary = parsed.get("summary", "")
        summary = WeeklyReportSummaryAgent.add_disclaimer(summary)

        return {
            "report_type": parsed.get("report_type", "weekly_health_report"),
            "health_score": parsed.get("health_score", 80),
            "summary": summary,
            "highlights": parsed.get("highlights", []),
            "tips": parsed.get("tips", []),
            "suggestions": parsed.get("suggestions", []),
        }


agent = WeeklyReportSummaryAgent()
