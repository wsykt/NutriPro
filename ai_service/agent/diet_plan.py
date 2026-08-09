"""膳食计划 Agent

依赖统一服务层：知识库检索走 services/retrieval_service.py
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
"""

from agent.base import BaseAgent

DIET_PLAN_PROMPT = """你是个性化一日膳食方案Agent。

输入：用户人群标签、减脂/增肌/控糖目标、过敏食材列表、饮食禁忌偏好。

任务：生成早中晚结构化食谱，预估营养。

核心约束：
1. 过敏食材强制过滤：完全不出现用户过敏食物；
2. 饮食禁忌替换：用户不吃牛羊肉、素食等，自动替换对应食材；
3. 匹配人群膳食标准：糖尿病患者选择低GI食物，健身人群增加蛋白质；
4. 营养均衡：三餐营养搭配合理，符合中国居民膳食指南。

输出JSON：
{
  "goal": "增肌减脂",
  "total_calories": 2200,
  "daily_plan": {
    "早餐": [{"food": "燕麦", "portion": "80克"}, {"food": "鸡蛋", "portion": "1个"}, {"food": "牛奶", "portion": "250毫升"}],
    "午餐": [{"food": "鸡胸肉", "portion": "150克"}, {"food": "糙米", "portion": "100克"}, {"food": "西兰花", "portion": "200克"}],
    "晚餐": [{"food": "三文鱼", "portion": "120克"}, {"food": "杂粮饭", "portion": "80克"}, {"food": "菠菜", "portion": "150克"}],
    "加餐": [{"food": "香蕉", "portion": "1根"}, {"food": "酸奶", "portion": "200克"}]
  },
  "nutrition_breakdown": {"protein": 120, "carbohydrate": 200, "fat": 60},
  "tips": ["烹饪方式建议", "饮食时间建议"],
  "avoided_foods": [],
  "replaced_foods": []
}

附带免责提示。

Few-Shot 示例：
输入：用户档案：{"age":28,"gender":"男","weight":80,"height":178,"crowd_type":"健身","allergies":["海鲜"]}，健康目标：增肌减脂
输出：{"goal":"增肌减脂","total_calories":2500,"daily_plan":{"早餐":[{"food":"燕麦","portion":"80克"},{"food":"鸡蛋","portion":"3个"},{"food":"全麦面包","portion":"2片"}],"午餐":[{"food":"鸡胸肉","portion":"200克"},{"food":"糙米","portion":"150克"},{"food":"西兰花","portion":"200克"}],"晚餐":[{"food":"牛肉","portion":"150克"},{"food":"红薯","portion":"200克"},{"food":"菠菜","portion":"200克"}],"加餐":[{"food":"蛋白粉","portion":"30克"},{"food":"香蕉","portion":"1根"}]},"nutrition_breakdown":{"protein":150,"carbohydrate":280,"fat":55},"tips":["训练后30分钟内补充蛋白质","全天少量多次饮水，保持水分充足"],"avoided_foods":["虾仁","三文鱼"],"replaced_foods":[{"from":"虾仁","to":"鸡胸肉"}]}"""

ALLERGEN_SUBSTITUTES = {
    "牛奶": ["豆浆", "杏仁奶", "燕麦奶", "椰奶"],
    "鸡蛋": ["豆腐", "豆浆", "鹌鹑蛋", "鹰嘴豆"],
    "海鲜": ["鸡胸肉", "瘦牛肉", "鱼肉", "豆制品"],
    "花生": ["核桃", "杏仁", "腰果", "南瓜子"],
    "小麦": ["糙米", "燕麦", "玉米", "小米"],
    "大豆": ["豆腐", "豆浆", "鸡蛋", "鸡胸肉"],
    "坚果": ["种子类", "水果", "酸奶"],
}

DIETARY_RESTRICTIONS = {
    "素食": {
        "avoid": ["牛肉", "猪肉", "羊肉", "鸡肉", "鸭肉", "鱼肉", "虾仁", "鸡蛋", "鸭蛋"],
        "replace_with": ["豆腐", "豆浆", "燕麦", "坚果", "豆类", "蔬菜"],
    },
    "不吃牛肉": {
        "avoid": ["牛肉", "牛腩", "牛腱子"],
        "replace_with": ["鸡胸肉", "鱼肉", "虾仁", "瘦猪肉"],
    },
    "不吃猪肉": {
        "avoid": ["猪肉", "五花肉", "猪蹄", "回锅肉"],
        "replace_with": ["鸡胸肉", "牛肉", "鱼肉", "虾仁"],
    },
    "不吃羊肉": {
        "avoid": ["羊肉", "羊排", "羊腿"],
        "replace_with": ["鸡胸肉", "牛肉", "鱼肉"],
    },
    "不吃海鲜": {
        "avoid": ["虾", "虾仁", "三文鱼", "鱼肉", "蟹", "贝类"],
        "replace_with": ["鸡胸肉", "瘦牛肉", "豆腐", "鸡蛋"],
    },
    "低糖": {
        "avoid": ["蛋糕", "饼干", "奶茶", "可乐", "果汁", "蜂蜜"],
        "replace_with": ["无糖酸奶", "水果", "全麦面包", "燕麦"],
    },
    "低盐": {
        "avoid": ["咸菜", "腌制品", "加工肉"],
        "replace_with": ["新鲜蔬菜", "新鲜肉类"],
    },
}

DEFAULT_MEALS = {
    "早餐": [{"food": "燕麦", "portion": "80克"}, {"food": "鸡蛋", "portion": "1个"}],
    "午餐": [{"food": "鸡胸肉", "portion": "150克"}, {"food": "糙米", "portion": "100克"}, {"food": "西兰花", "portion": "200克"}],
    "晚餐": [{"food": "三文鱼", "portion": "120克"}, {"food": "杂粮饭", "portion": "80克"}, {"food": "菠菜", "portion": "150克"}],
    "加餐": [{"food": "香蕉", "portion": "1根"}, {"food": "酸奶", "portion": "200克"}],
}


class DietPlanAgent(BaseAgent):

    @staticmethod
    def _filter_allergens(items: list, allergies: list) -> tuple:
        filtered = []
        avoided = []
        for item in items:
            food = item.get("food", "")
            is_allergen = any(allergen in food for allergen in allergies)
            if is_allergen:
                avoided.append(food)
            else:
                filtered.append(item)
        return filtered, avoided

    @staticmethod
    def _apply_dietary_restrictions(items: list, restrictions: list) -> tuple:
        filtered = []
        avoided = []
        replaced = []

        for item in items:
            food = item.get("food", "")
            should_replace = False
            replacement = None

            for restriction in restrictions:
                if restriction in DIETARY_RESTRICTIONS:
                    rule = DIETARY_RESTRICTIONS[restriction]
                    if any(avoid in food for avoid in rule["avoid"]):
                        should_replace = True
                        replacement = rule["replace_with"][0] if rule["replace_with"] else None
                        avoided.append(food)
                        if replacement:
                            replaced.append({"from": food, "to": replacement})
                            item["food"] = replacement
                            filtered.append(item)
                        break

            if not should_replace:
                filtered.append(item)

        return filtered, avoided, replaced

    @staticmethod
    def _validate_plan(daily_plan: dict, allergies: list, restrictions: list) -> dict:
        validated = {}
        all_avoided = []
        all_replaced = []

        for meal_type, items in daily_plan.items():
            if not items:
                validated[meal_type] = []
                continue

            filtered, avoided = DietPlanAgent._filter_allergens(items, allergies)
            all_avoided.extend(avoided)

            if restrictions:
                filtered, avoided2, replaced = DietPlanAgent._apply_dietary_restrictions(filtered, restrictions)
                all_avoided.extend(avoided2)
                all_replaced.extend(replaced)

            validated[meal_type] = filtered

        return validated, list(set(all_avoided)), all_replaced

    @staticmethod
    def generate(user_profile: dict, goal: str = "") -> dict:
        allergies = user_profile.get("allergies", []) or []
        dietary_restrictions = user_profile.get("dietary_restrictions", []) or []

        if isinstance(allergies, str):
            allergies = [a.strip() for a in allergies.split(",") if a.strip()]
        if isinstance(dietary_restrictions, str):
            dietary_restrictions = [d.strip() for d in dietary_restrictions.split(",") if d.strip()]

        crowd_type = user_profile.get("crowd_type", "")
        kb_context = DietPlanAgent.get_kb_context(f"{crowd_type} {goal} 膳食方案")

        prompt = DIET_PLAN_PROMPT + "\n\n"
        prompt += f"用户档案：{user_profile}\n"
        prompt += f"健康目标：{goal}\n"
        prompt += f"过敏食材：{allergies}\n"
        prompt += f"饮食禁忌：{dietary_restrictions}\n"
        prompt += kb_context

        messages = [
            {"role": "system", "content": "你是一个专业膳食方案制定专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        parsed = DietPlanAgent.chat_json(messages)

        daily_plan = parsed.get("daily_plan", {})
        if not daily_plan:
            daily_plan = {k: list(v) for k, v in DEFAULT_MEALS.items()}

        validated_plan, avoided_foods, replaced_foods = DietPlanAgent._validate_plan(
            daily_plan, allergies, dietary_restrictions
        )

        for meal_type in DEFAULT_MEALS:
            if meal_type not in validated_plan or not validated_plan[meal_type]:
                items = list(DEFAULT_MEALS[meal_type])
                items, _ = DietPlanAgent._filter_allergens(items, allergies)
                if dietary_restrictions:
                    items, _, _ = DietPlanAgent._apply_dietary_restrictions(items, dietary_restrictions)
                validated_plan[meal_type] = items

        return {
            "goal": parsed.get("goal", goal),
            "total_calories": parsed.get("total_calories", 2200),
            "daily_plan": validated_plan,
            "nutrition_breakdown": parsed.get("nutrition_breakdown", {"protein": 120, "carbohydrate": 200, "fat": 60}),
            "tips": parsed.get("tips", []),
            "avoided_foods": avoided_foods,
            "replaced_foods": replaced_foods,
        }


agent = DietPlanAgent()
