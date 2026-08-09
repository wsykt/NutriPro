"""营养分析 Agent

依赖统一服务层：知识库检索走 services/retrieval_service.py
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
"""

from agent.base import BaseAgent

NUTRITION_ANALYSIS_PROMPT = """你是营养分析评估Agent。

输入：用户人群标签、年龄性别身高体重、当日摄入营养数据、当日活动量。

任务：分析营养摄入是否达标，给出改进建议。

输出要求：严格输出以下JSON结构，不要输出任何其他内容（不要输出markdown代码块标记、不要输出解释文字）：

{"analysis_type":"daily_nutrition","nutrition_score":85,"summary":"整体营养评估总结","energy_score":80,"protein_score":85,"fat_score":70,"carbs_score":75,"nutrition_ratio":"三大营养素比例分析","recommendations":[{"suggestion":"建议1","priority":"high"}],"risk_items":["风险项1"],"tips":["提示1"]}

评分规则：
- 各项评分0-100分
- 钠摄入超过2000mg需在risk_items中标注
- 膳食纤维低于25g需在tips中提示

Few-Shot 示例：
输入：用户档案：{"age":30,"gender":"男","weight":75,"height":175,"crowd_type":"健身"}，当日营养摄入：{"calories":2800,"protein":120,"fat":70,"carb":350,"fiber":20,"sodium":1800}
输出：{"analysis_type":"daily_nutrition","nutrition_score":78,"summary":"蛋白质摄入充足（120g，推荐120g），碳水偏高（350g，推荐300g），纤维摄入不足（20g，推荐25-30g）。","energy_score":82,"protein_score":90,"fat_score":75,"carbs_score":65,"nutrition_ratio":"蛋白质17%、脂肪22%、碳水61%，碳水比例偏高。","recommendations":[{"suggestion":"适当减少碳水摄入，控制在300g左右","priority":"high"},{"suggestion":"增加膳食纤维（蔬菜、粗粮）","priority":"medium"}],"risk_items":[],"tips":["膳食纤维摄入不足（20g，推荐25-30g）","建议增加蔬菜摄入"]}

输入：用户档案：{"age":60,"gender":"女","weight":65,"height":160,"crowd_type":"老年"}，当日营养摄入：{"calories":1500,"protein":45,"fat":30,"carb":200,"fiber":15,"sodium":2500}
输出：{"analysis_type":"daily_nutrition","nutrition_score":55,"summary":"蛋白质摄入不足（45g，推荐72g），钠摄入超标（2500mg，推荐<2000mg），热量偏低。","energy_score":60,"protein_score":40,"fat_score":65,"carbs_score":55,"nutrition_ratio":"蛋白质12%、脂肪18%、碳水70%，蛋白质不足。","recommendations":[{"suggestion":"增加优质蛋白质（鸡蛋、牛奶、瘦肉），目标每天72g","priority":"high"},{"suggestion":"减少钠摄入，食盐控制在5g/天以内","priority":"high"}],"risk_items":["钠摄入超过2000mg（2500mg）"],"tips":["膳食纤维摄入不足（15g，推荐25-30g）","建议老年人群食物细软易消化"]}"""


class NutritionAnalysisAgent(BaseAgent):

    @staticmethod
    def analyze(user_profile: dict, daily_nutrition: dict = None, daily_exercise: dict = None) -> dict:
        crowd_type = user_profile.get("crowd_type", "")
        kb_context = NutritionAnalysisAgent.get_kb_context(f"{crowd_type} 营养分析 蛋白质 脂肪 碳水")

        prompt = NUTRITION_ANALYSIS_PROMPT + "\n\n"
        prompt += f"用户档案：{user_profile}\n"
        prompt += f"当日营养摄入：{daily_nutrition}\n"
        prompt += f"当日活动量：{daily_exercise}\n"
        prompt += kb_context

        messages = [
            {"role": "system", "content": "你是一个专业的营养分析专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        parsed = NutritionAnalysisAgent.chat_json(messages)

        if not parsed:
            raise ValueError("JSON解析失败")

        sodium = daily_nutrition.get("sodium", 0) if daily_nutrition else 0
        fiber = daily_nutrition.get("fiber", 0) if daily_nutrition else 0
        risk_items = parsed.get("risk_items", [])
        tips = parsed.get("tips", [])

        if sodium > 2000 and "钠摄入过量" not in "".join(risk_items):
            risk_items.append(f"钠摄入过量（{sodium}mg，推荐<2000mg）")
        if fiber < 25 and fiber > 0:
            msg = f"膳食纤维摄入不足（{fiber}g，推荐25-30g）"
            if msg not in tips:
                tips.append(msg)

        return {
            "analysis_type": parsed.get("analysis_type", "daily_nutrition"),
            "nutrition_score": parsed.get("nutrition_score", 0),
            "summary": parsed.get("summary", ""),
            "energy_score": parsed.get("energy_score", 0),
            "protein_score": parsed.get("protein_score", 0),
            "fat_score": parsed.get("fat_score", 0),
            "carbs_score": parsed.get("carbs_score", 0),
            "nutrition_ratio": parsed.get("nutrition_ratio", ""),
            "recommendations": parsed.get("recommendations", []),
            "risk_items": risk_items,
            "tips": tips,
        }


agent = NutritionAnalysisAgent()
