"""食材菜谱推荐 Agent

根据用户已有的食材、人群标签和饮食目标，生成三餐推荐食谱。
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
免责声明走 services/disclaimer.py
"""

from agent.base import BaseAgent

FOOD_RECOMMEND_PROMPT = """你是营养膳食推荐Agent。

输入：
1. 现有食材列表（必须全部使用）
2. 用户人群标签（普通人/健身/老年/孕妇/糖尿病）
3. 健康目标（减脂/增肌/维持健康/控糖）

任务：
1. 根据现有食材设计早餐、午餐、晚餐三顿饭的菜谱
2. 若食材不够，优先使用同类替代方案
3. 标注每道菜的热量估算和主要营养成分

输出JSON：
{
  "total_meals": 3,
  "meal_plan": [
    {
      "meal_type": "早餐",
      "name": "菜名",
      "ingredients": [{"name":"食材名","amount":"用量"}],
      "cook_method": "简易做法（1-2句话）",
      "calories_estimate": 300,
      "protein_estimate": 15,
      "tags": ["快手", "营养"]
    }
  ],
  "total_calories": 1800,
  "total_protein": 70,
  "tips": ["备餐建议1", "替代方案1"],
  "missing_ingredients": ["建议补充的食材"]
}

约束：
- 所有食材必须在用户提供的列表中
- 输出3餐（早/午/晚）
- 仅输出JSON，禁止额外文字"""

DEFAULT_RECOMMEND = {
    "total_meals": 3,
    "meal_plan": [
        {"meal_type": "早餐", "name": "燕麦鸡蛋", "ingredients": [{"name": "燕麦", "amount": "80克"}, {"name": "鸡蛋", "amount": "1个"}], "cook_method": "燕麦煮粥，鸡蛋煮熟", "calories_estimate": 350, "protein_estimate": 18, "tags": ["快手"]},
        {"meal_type": "午餐", "name": "鸡胸肉糙米饭", "ingredients": [{"name": "鸡胸肉", "amount": "150克"}, {"name": "糙米", "amount": "100克"}, {"name": "西兰花", "amount": "200克"}], "cook_method": "鸡胸肉煎熟，糙米蒸煮，西兰花焯水", "calories_estimate": 550, "protein_estimate": 40, "tags": ["高蛋白"]},
        {"meal_type": "晚餐", "name": "清蒸鱼配蔬菜", "ingredients": [{"name": "鱼肉", "amount": "120克"}, {"name": "菠菜", "amount": "150克"}], "cook_method": "鱼肉清蒸，菠菜焯水", "calories_estimate": 400, "protein_estimate": 30, "tags": ["低脂"]},
    ],
    "total_calories": 1300,
    "total_protein": 88,
    "tips": ["建议补充更多蔬菜水果", "注意烹饪方式少油少盐"],
    "missing_ingredients": [],
}


class FoodRecommendAgent(BaseAgent):

    @staticmethod
    def recommend(ingredients: list, crowd_type: str = "普通人", goal: str = "健康饮食") -> dict:
        ingredients_str = "、".join(ingredients) if isinstance(ingredients, list) else str(ingredients)

        # 知识库检索
        kb_context = FoodRecommendAgent.get_kb_context(f"{crowd_type} {goal} 食材菜谱推荐")

        prompt = FOOD_RECOMMEND_PROMPT + f"\n\n现有食材：{ingredients_str}\n人群标签：{crowd_type}\n目标：{goal}"
        if kb_context:
            prompt += f"\n{kb_context}"

        messages = [
            {"role": "system", "content": "你是一个专业营养膳食推荐专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        try:
            parsed = FoodRecommendAgent.chat_json(messages)
            if parsed and "meal_plan" in parsed:
                parsed["crowd_type"] = crowd_type
                parsed["goal"] = goal
                # 添加免责声明
                tips = parsed.get("tips", [])
                disclaimer = BaseAgent.add_disclaimer("")
                if disclaimer:
                    tips.append(disclaimer)
                    parsed["tips"] = tips
                return parsed
        except Exception:
            pass

        # LLM 失败时返回默认推荐方案
        DEFAULT_RECOMMEND["crowd_type"] = crowd_type
        DEFAULT_RECOMMEND["goal"] = goal
        DEFAULT_RECOMMEND["fallback"] = True
        return DEFAULT_RECOMMEND


agent = FoodRecommendAgent()
