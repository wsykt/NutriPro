"""本地离线规则引擎

不依赖 DeepSeek 云端 API，纯本地规则生成回答。
用于 LLM API 失效、网络断开、离线演示场景下的全场景兜底。

覆盖场景：
1. 通用健康问答（BMI、饮食、人群建议、GI值、食物热量）
2. 膳食计划（结构化三餐模板）
3. 周报（基于人群标签的简易结构周报）
4. 食材审核（基础热量估算 + 营养标签）
5. 语音解析（量词匹配基础结果）
"""

import re
import datetime
import random
from typing import Optional, List, Dict, Any


# ============================================================
# 人群名称规范化
# ============================================================
# 用户档案(crowd_type/crowdType)与知识库/规则引擎存在长短名混用：
#   前端/档案: "糖尿病患者"、"健身人群"、"老年人"
#   规则引擎:  "糖尿病"、"健身"、"老年"
# 统一规范化到短名（内部），再映射到各层需要的名称。
CROWD_ALIASES = {
    "糖尿病患者": "糖尿病", "糖尿病": "糖尿病", "糖尿病人": "糖尿病", "糖友": "糖尿病", "2型糖尿病": "糖尿病",
    "健身人群": "健身", "健身": "健身", "运动人群": "健身", "增肌人群": "健身",
    "老年人": "老年", "老年": "老年", "老人": "老年", "长者": "老年", "中老年": "老年",
    "普通人": "普通人", "普通人群": "普通人", "大众": "普通人", "一般人群": "普通人", "": "普通人",
    "孕妇": "孕妇", "孕妈妈": "孕妇", "妊娠期": "孕妇", "孕期": "孕妇",
    "青少年": "青少年", "未成年": "青少年", "未成年人": "青少年", "学生": "青少年",
    "通用": "通用",
}


def canonical_crowd(raw) -> str:
    """把任意写法的人群标签规范化为短名（普通人/健身/老年/孕妇/青少年/糖尿病/通用）。
    无法识别时原样返回；空值默认普通人。"""
    if not raw:
        return "普通人"
    key = str(raw).strip()
    return CROWD_ALIASES.get(key, key)


# 短名 -> 向量知识库 metadata 中使用的长名（用于 where 精确过滤）
CROWD_KB_NAMES = {
    "普通人": "普通人", "健身": "健身人群", "老年": "老年人", "孕妇": "孕妇",
    "青少年": "青少年", "糖尿病": "糖尿病患者", "通用": "通用",
}


def crowd_kb_name(crowd: str) -> str:
    """规范化短名 -> 知识库长名；用于 ChromaDB where 过滤"""
    return CROWD_KB_NAMES.get(canonical_crowd(crowd), canonical_crowd(crowd))


# 短名 -> 展示给大模型的友好名称
CROWD_DISPLAY_NAMES = {
    "普通人": "普通人", "健身": "健身人群", "老年": "老年人", "孕妇": "孕妇",
    "青少年": "青少年", "糖尿病": "糖尿病患者", "通用": "普通人群",
}


def crowd_display_name(crowd: str) -> str:
    """规范化短名 -> 大模型可读的友好名称"""
    return CROWD_DISPLAY_NAMES.get(canonical_crowd(crowd), canonical_crowd(crowd))


# ============================================================
# 内置膳食标准数据
# ============================================================

BMI_STANDARD = {
    "underweight": {"range": "< 18.5", "label": "偏瘦", "advice": "建议增加热量摄入，适当增加主食和优质蛋白质"},
    "normal": {"range": "18.5-23.9", "label": "正常", "advice": "体重正常，继续保持均衡饮食和规律运动"},
    "overweight": {"range": "24-27.9", "label": "超重", "advice": "建议控制总热量摄入，增加运动量，减少高脂高糖食物"},
    "obese": {"range": ">= 28", "label": "肥胖", "advice": "建议调整饮食结构，严格控热量，每周至少150分钟运动"},
}

CROWD_DIET_ADVICE = {
    "普通人": "均衡饮食，每餐主食一拳头、蛋白质一掌、蔬菜两拳。每天饮水1500-1700ml。",
    "健身": "高蛋白饮食，蛋白质1.6-2.2g/kg体重/天。训练后30分钟内补充蛋白质20-30g。",
    "老年": "高蛋白（1.2-1.4g/kg/天），充足钙和维D，少食多餐，食物细软易消化。",
    "孕妇": "补充叶酸400μg/天，钙1000mg/天，铁27mg/天。避免生冷食物。",
    "青少年": "充足热量和蛋白质（1.2-1.5g/kg/天），足量钙和维D，规律三餐不节食。",
    "糖尿病": "低GI饮食，控制碳水总量，少食多餐。主食粗细搭配，每餐主食不超过一拳头。",
}

DAILY_REFERENCE = {
    "calories": ("成年男性每天2250kcal，女性1800kcal。",),
    "protein": ("男性65g/天，女性55g/天。",),
    "fat": ("占总能量20-30%，烹调用油25-30g/天。",),
    "carbs": ("占总能量50-65%",),
    "fiber": ("25-30g/天",),
    "water": ("1500-1700ml/天",),
    "calcium": ("800mg/天（老年/孕妇1000-1200mg）",),
    "folic_acid": ("400μg/天",),
}

# kcal/100g
FOOD_CALORIES_TABLE = {
    "米饭": 116, "面条": 110, "馒头": 221, "燕麦": 367, "糙米": 111,
    "鸡胸肉": 133, "鸡腿": 181, "鸡蛋": 144, "瘦猪肉": 143, "瘦牛肉": 106,
    "三文鱼": 139, "虾仁": 48, "豆腐": 81, "豆浆": 31, "牛奶": 54,
    "酸奶": 72, "西兰花": 34, "菠菜": 23, "西红柿": 18, "黄瓜": 15,
    "苹果": 52, "香蕉": 89, "橙子": 47, "西瓜": 30, "葡萄": 69,
    "红薯": 86, "玉米": 96, "土豆": 76, "橄榄油": 884, "花生油": 884,
    "白米饭": 116, "白馒头": 221, "全麦面包": 246, "荞麦": 316,
    "羊肉": 203, "鸭肉": 240, "胡萝卜": 41, "白菜": 17, "茄子": 21,
    "柠檬": 26, "火龙果": 55,
}

HIGH_GI_FOODS = {"白米饭": 73, "白馒头": 88, "白面包": 70, "糯米": 71, "西瓜": 72}
MEDIUM_GI_FOODS = {"糙米": 56, "香蕉": 52, "玉米": 55, "全麦面包": 50, "荞麦": 54}
LOW_GI_FOODS = {"燕麦": 42, "苹果": 36, "梨": 36, "酸奶": 36, "牛奶": 27, "鸡蛋": 14}

# 量词映射（用于语音解析兜底）
QUANTIFIER_MAP = {
    "个": "个", "碗": "碗", "盘": "盘", "杯": "杯", "勺": "勺",
    "克": "g", "毫升": "ml", "升": "L", "斤": "斤",
}

# ============================================================
# 引擎主类
# ============================================================

class LocalFallbackEngine:
    """本地离线兜底引擎——全场景规则回答"""

    # ---- 通用健康问答 ----

    def answer_health_query(self, question: str, health_snapshot: dict = None) -> str:
        """通用健康问答，自动检测问题类型并返回规则回答"""
        q = question.lower()
        answers = []

        # 1. BMI 相关
        if any(kw in q for kw in ["bmi", "体重", "胖", "瘦", "肥胖", "标准体重"]):
            answers.append(self._answer_bmi(health_snapshot))

        # 2. 饮食/营养相关
        if any(kw in q for kw in ["吃", "饮食", "营养", "热量", "减肥", "减脂", "摄入"]):
            answers.append(self._answer_diet(question, health_snapshot))

        # 3. 人群建议
        if any(kw in q for kw in ["我该", "建议", "注意", "怎么吃", "吃什么", "怎么办"]):
            answers.append(self._answer_crowd_advice(health_snapshot))

        # 4. GI 值相关
        if any(kw in q for kw in ["gi", "血糖", "糖尿病", "升糖"]):
            answers.append(self._answer_gi(question))

        # 5. 食物热量
        food_match = self._match_food(question)
        if food_match:
            answers.append(self._answer_food_calories(food_match))

        if not answers:
            return self._default_answer()

        return "\n\n".join(answers) + "\n\n【温馨提示：本内容仅为膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。】"

    def _answer_bmi(self, snapshot: dict = None) -> str:
        if not snapshot:
            return "BMI = 体重(kg) ÷ 身高(m)的平方。中国标准：<18.5偏瘦，18.5-23.9正常，24-27.9超重，≥28肥胖。"
        profile = snapshot.get("profile", {})
        weight = profile.get("weight_kg", 0)
        height = profile.get("height_cm", 0)
        if height <= 0 or weight <= 0:
            return "请先录入身高体重数据，才能计算 BMI。"
        bmi = round(weight / ((height / 100) ** 2), 1)
        if bmi < 18.5:
            s = BMI_STANDARD["underweight"]
        elif bmi < 24:
            s = BMI_STANDARD["normal"]
        elif bmi < 28:
            s = BMI_STANDARD["overweight"]
        else:
            s = BMI_STANDARD["obese"]
        return f"您的 BMI 为 {bmi}（{s['range']}），属于{s['label']}。{s['advice']}。"

    def _answer_diet(self, question: str, snapshot: dict = None) -> str:
        lines = ["【饮食参考】"]
        if snapshot:
            total = snapshot.get("today_diet_total", {})
            if total.get("total_calories_kcal"):
                cal = total["total_calories_kcal"]
                lines.append(f"今日已摄入 {cal} kcal。")
                if cal > 2500:
                    lines.append("⚠️ 今日热量偏高，建议控制后续饮食。")
                elif cal < 800:
                    lines.append("⚠️ 今日热量偏低，建议适当增加进食。")
        lines.append(f"每日参考：{DAILY_REFERENCE['calories'][0]}")
        lines.append(f"蛋白质：{DAILY_REFERENCE['protein'][0]}")
        lines.append(f"膳食纤维：{DAILY_REFERENCE['fiber'][0]}")
        lines.append(f"饮水：{DAILY_REFERENCE['water'][0]}")
        return "\n".join(lines)

    def _answer_crowd_advice(self, snapshot: dict = None) -> str:
        if not snapshot:
            return "保持均衡饮食，规律运动，充足睡眠。建议每天摄入12种以上食物。"
        crowd = canonical_crowd(snapshot.get("profile", {}).get("crowdType", "普通人"))
        crowd_display = crowd_display_name(crowd)
        advice = CROWD_DIET_ADVICE.get(crowd, CROWD_DIET_ADVICE["普通人"])
        return f"【{crowd_display}膳食建议】{advice}"

    def _answer_gi(self, question: str) -> str:
        lines = [
            "【GI 值参考】",
            "低GI（<55）：燕麦、苹果、梨、酸奶、牛奶、鸡蛋、绝大多数蔬菜",
            "中GI（55-70）：糙米、香蕉、玉米、全麦面包",
            "高GI（>70）：白米饭、白馒头、白面包、糯米、西瓜",
        ]
        for food, gi in LOW_GI_FOODS.items():
            if food in question:
                lines.append(f"\n{food} 的 GI 值为 {gi}，属于低GI食物。")
        for food, gi in MEDIUM_GI_FOODS.items():
            if food in question:
                lines.append(f"\n{food} 的 GI 值为 {gi}，属于中GI食物。")
        for food, gi in HIGH_GI_FOODS.items():
            if food in question:
                lines.append(f"\n{food} 的 GI 值为 {gi}，属于高GI食物，糖尿病患者建议少量食用。")
        return "\n".join(lines)

    def _match_food(self, question: str) -> Optional[str]:
        for food in FOOD_CALORIES_TABLE:
            if food in question:
                return food
        return None

    def _answer_food_calories(self, food: str) -> str:
        cal = FOOD_CALORIES_TABLE.get(food)
        if cal:
            return f"{food} 的热量约为 {cal} kcal/100g。"
        return ""

    def _default_answer(self) -> str:
        return (
            "你好！我是 AI 健康助手（离线模式）。\n\n"
            "目前 AI 服务暂时不可用，以下是一些通用的健康建议：\n"
            "1️⃣ 均衡饮食：食物多样，谷类为主，每天摄入12种以上食物\n"
            "2️⃣ 吃动平衡：每周至少运动150分钟\n"
            "3️⃣ 少盐少油：每天盐<5g，油25-30g\n"
            "4️⃣ 足量饮水：每天1500-1700ml\n"
            "5️⃣ 保持良好作息：每天睡眠7-8小时\n\n"
            "如需更精准的建议，请等待 AI 服务恢复后重试。"
        )

    # ---- 结构化场景兜底 ----

    def fallback_diet_plan(self, user_profile: dict, goal: str = "") -> dict:
        """膳食计划兜底——返回标准化三餐模板"""
        crowd = canonical_crowd(user_profile.get("crowd_type") or user_profile.get("crowdType") or "普通人")
        crowd_display = crowd_display_name(crowd)
        total_cal = 2200
        if crowd == "健身":
            total_cal = 2500
        elif crowd == "老年":
            total_cal = 1800
        elif crowd == "糖尿病":
            total_cal = 1800

        plan = {
            "早餐": [{"food": "全麦面包", "portion": "2片"}, {"food": "鸡蛋", "portion": "1个"}, {"food": "牛奶", "portion": "250ml"}],
            "午餐": [{"food": "糙米饭", "portion": "150g"}, {"food": "鸡胸肉", "portion": "120g"}, {"food": "西兰花", "portion": "200g"}],
            "晚餐": [{"food": "红薯", "portion": "150g"}, {"food": "三文鱼", "portion": "100g"}, {"food": "菠菜", "portion": "200g"}],
            "加餐": [{"food": "苹果", "portion": "1个"}, {"food": "酸奶", "portion": "200g"}],
        }

        if crowd == "糖尿病":
            plan["早餐"] = [{"food": "燕麦", "portion": "50g"}, {"food": "鸡蛋", "portion": "1个"}]
            plan["午餐"] = [{"food": "糙米饭", "portion": "100g"}, {"food": "鸡胸肉", "portion": "100g"}, {"food": "芹菜", "portion": "200g"}]
            plan["晚餐"] = [{"food": "荞麦面", "portion": "80g"}, {"food": "豆腐", "portion": "150g"}, {"food": "青菜", "portion": "200g"}]
            plan["加餐"] = [{"food": "无糖酸奶", "portion": "200g"}]
        elif crowd == "健身":
            plan["早餐"] = [{"food": "燕麦", "portion": "80g"}, {"food": "鸡蛋", "portion": "3个"}, {"food": "香蕉", "portion": "1根"}]
            plan["午餐"] = [{"food": "糙米饭", "portion": "200g"}, {"food": "鸡胸肉", "portion": "200g"}, {"food": "西兰花", "portion": "250g"}]
            plan["晚餐"] = [{"food": "红薯", "portion": "200g"}, {"food": "牛肉", "portion": "150g"}, {"food": "菠菜", "portion": "200g"}]
            plan["加餐"] = [{"food": "蛋白粉", "portion": "30g"}, {"food": "酸奶", "portion": "200g"}]

        return {
            "goal": goal or "均衡饮食",
            "total_calories": total_cal,
            "daily_plan": plan,
            "nutrition_breakdown": {"protein": 80, "carbohydrate": 250, "fat": 60},
            "tips": [f"[离线模式] 以上为{crowd_display}标准膳食模板", "建议搭配蔬菜水果，保证膳食纤维摄入"],
            "avoided_foods": [],
            "replaced_foods": [],
        }

    def fallback_weekly_report(self, user_profile: dict, weekly_stats: dict = None) -> dict:
        """周报兜底——基于人群标签的简易结构周报"""
        weekly_stats = weekly_stats or {}
        crowd = user_profile.get("crowd_type", "普通人")
        name = user_profile.get("username", "用户")

        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())
        week_end = week_start + datetime.timedelta(days=6)

        highlights = [f"本周（{week_start} - {week_end}）为您生成了{crowd}健康周报"]
        if crowd == "健身":
            highlights.append("建议维持高蛋白饮食和规律训练")
        elif crowd == "糖尿病":
            highlights.append("建议坚持低GI饮食，定期监测血糖")
        else:
            highlights.append("继续保持均衡饮食和规律作息")

        summary = (
            f"您好{name}！这是您的{CROWD_DIET_ADVICE.get(crowd, '')[:40]}周报。"
            f"受限于 AI 服务暂不可用，以上为基于{crowd}标准的通用建议。"
        )

        return {
            "report_type": "weekly_health_report",
            "health_score": 75,
            "summary": summary + "【温馨提示：本内容仅为膳食科普参考，不构成医疗建议。】",
            "highlights": highlights,
            "tips": ["每日饮水1500-1700ml", "每周运动至少150分钟"],
            "suggestions": ["保持规律作息", CROWD_DIET_ADVICE.get(crowd, "均衡饮食")],
        }

    def fallback_food_audit(self, food_data: dict) -> dict:
        """食材审核兜底——基础热量估算 + 营养标签"""
        food_name = food_data.get("food_name", "未知食物")
        portion_str = str(food_data.get("portion", "100g"))

        # 解析份量
        portion_g = 100
        import re as _re
        match = _re.search(r'(\d+\.?\d*)', portion_str)
        if match:
            portion_g = float(match.group(1))

        # 热量估算
        calories = self._estimate_calories(food_name, portion_g)
        protein = round(calories * 0.15 / 4, 1)
        fat = round(calories * 0.25 / 9, 1)
        carb = round(calories * 0.6 / 4, 1)

        nutrition_tags = []
        if calories > 500:
            nutrition_tags.append("高热量")
        if fat > 20:
            nutrition_tags.append("高脂肪")
        if carb > 60:
            nutrition_tags.append("高碳水")
        if protein > 20:
            nutrition_tags.append("高蛋白")

        return {
            "status": "pass",
            "calories": round(calories, 1),
            "protein": protein,
            "fat": fat,
            "carbohydrate": carb,
            "nutrition_tags": nutrition_tags,
            "advice": f"（离线审核）{food_name}约{portion_g}g，热量约{round(calories, 1)}kcal。建议适量食用。",
            "audit_level": "pass",
            "risk_desc": "",
            "duplicate_info": {"is_duplicate": False, "similar_names": []},
            "is_system_food": False,
            "category_mismatch": False,
            "category_suggestion": "",
        }

    def _estimate_calories(self, food_name: str, portion_g: float) -> float:
        """估测食物热量"""
        for kw, cal_per_100 in sorted(FOOD_CALORIES_TABLE.items(), key=lambda x: -len(x[0])):
            if kw in food_name:
                return cal_per_100 * portion_g / 100
        # 默认按一般食材估算
        return 120 * portion_g / 100

    def fallback_voice_parse(self, text: str) -> dict:
        """语音解析兜底——量词匹配基础结果"""
        items = []
        # 简单按长度拆分为假想条目
        for segment in re.split(r'[，,。.；;]', text):
            segment = segment.strip()
            if not segment:
                continue
            food_name = segment
            qty = "1份"
            # 尝试提取量词
            for q_word in QUANTIFIER_MAP:
                if q_word in segment:
                    food_name = re.sub(rf'\d*{q_word}.*$', '', segment).strip()
                    qty = f"1{q_word}"
                    break
            items.append({"food_name": food_name, "quantity": qty})
            if len(items) >= 5:
                break

        if not items:
            items = [{"food_name": text[:10], "quantity": "1份"}]

        return {"items": items}


    # ---- 新增：营养分析兜底 ----

    def fallback_nutrition_analysis(self, user_profile: dict, daily_nutrition: dict, daily_exercise: dict) -> dict:
        """营养分析兜底 — 标准化结构返回"""
        crowd = user_profile.get("crowd_type", "普通人")
        age = user_profile.get("age", 30)
        gender = user_profile.get("gender", "男")
        weight = user_profile.get("weight", 70)
        height = user_profile.get("height", 170)

        # BMR 计算
        if gender == "男":
            bmr = round(10 * weight + 6.25 * height - 5 * age + 5, 1)
        else:
            bmr = round(10 * weight + 6.25 * height - 5 * age - 161, 1)

        cal = daily_nutrition.get("calories", 0)
        protein = daily_nutrition.get("protein", 0)
        carb = daily_nutrition.get("carbohydrate", 0)
        fat = daily_nutrition.get("fat", 0)
        fiber = daily_nutrition.get("diet_fiber", 0)
        calcium = daily_nutrition.get("calcium", 0)
        folic = daily_nutrition.get("folic_acid", 0)
        dha = daily_nutrition.get("dha", 0)

        bmr_ratio = round(cal / bmr, 2) if bmr > 0 else 0
        if bmr_ratio < 0.8:
            bmr_status = "热量摄入不足"
        elif bmr_ratio < 1.2:
            bmr_status = "热量摄入适中"
        else:
            bmr_status = "热量摄入偏高"

        return {
            "fallback": True,
            "template_type": "nutrition_fallback",
            "user_profile": {"username": user_profile.get("username", "用户"), "crowd_type": crowd},
            "bmr": bmr,
            "bmr_ratio": bmr_ratio,
            "bmr_status": bmr_status,
            "daily_nutrition": {
                "calories": {"value": cal, "status": bmr_status},
                "protein": {"value": protein, "recommendation": "男性65g/天，女性55g/天"},
                "carbohydrate": {"value": carb, "recommendation": "占总能量50-65%"},
                "fat": {"value": fat, "recommendation": "占总能量20-30%"},
                "diet_fiber": {"value": fiber, "recommendation": "25-30g/天"},
                "calcium": {"value": calcium, "recommendation": "800mg/天"},
                "folic_acid": {"value": folic, "recommendation": "400μg/天"},
                "dha": {"value": dha, "recommendation": "200-500mg/天"},
            },
            "advantage_items": [],
            "disadvantage_items": [],
            "disease_risks": [],
            "summary": f"基础代谢率(BMR)={bmr}kcal，当前摄入{cal}kcal（{bmr_status}）。更多详细分析请等待AI服务恢复。",
        }

    # ---- 新增：科普文章生成兜底 ----

    def fallback_article_generate(self, topic: str, target_crowd: str = "") -> dict:
        """科普文章生成兜底 — 标准结构"""
        return {
            "fallback": True,
            "template_type": "article_fallback",
            "title": f"{topic} — 健康科普",
            "author": "AI健康助手",
            "publish_time": datetime.datetime.now().strftime("%Y-%m-%d"),
            "article_type": "科普",
            "target_crowd": target_crowd or "普通人",
            "content": f"# {topic}\n\n## 什么是{topic}\n\n{topic}是健康管理中的重要话题。以下是一些基础建议：\n\n## 核心建议\n\n1. **均衡饮食**：食物多样，谷类为主，每天摄入12种以上食物\n2. **适量运动**：每周至少150分钟中等强度运动\n3. **充足睡眠**：每天7-8小时\n4. **良好心态**：保持积极乐观\n\n## 注意事项\n\n- 具体方案因个体差异而异，建议咨询专业人士\n- 合理膳食、规律作息是健康的基础\n\n【温馨提示：本内容仅为健康科普参考，不构成医疗建议，慢性病请遵从执业医师指导。】",
            "keywords": [topic, "健康", "科普"],
            "summary": f"关于{topic}的健康科普文章（离线模式生成）。",
        }

    # ---- 新增：食材推荐兜底 ----

    def fallback_food_recommend(self, ingredients: list, crowd_type: str = "普通人", goal: str = "健康饮食") -> dict:
        """食材推荐兜底"""
        # 食材别名归一化：用户说"猪肉/瘦肉"→ 模板统一用"瘦猪肉"，避免同义词匹配不上
        ING_ALIASES = {
            "猪肉": "瘦猪肉", "猪肉(瘦)": "瘦猪肉", "瘦肉": "瘦猪肉", "猪里脊": "瘦猪肉",
            "鸡胸": "鸡胸肉", "番茄": "西红柿", "马铃薯": "土豆", "青椒": "尖椒",
        }
        raw_items = [i.strip() for i in ("、".join(ingredients) if isinstance(ingredients, list) else ingredients).replace("、", ",").split(",")]
        ing_set = set(ING_ALIASES.get(i, i) for i in raw_items if i)

        templates = {
            "鸡胸肉_鸡蛋_西兰花_糙米": {
                "meal_plan": [
                    {"meal_type": "早餐", "name": "水煮蛋+糙米粥", "ingredients": [{"name": "鸡蛋", "amount": "2个"}, {"name": "糙米", "amount": "50g"}], "cook_method": "糙米煮粥，鸡蛋煮熟", "calories_estimate": 250, "protein_estimate": 13, "tags": ["快手", "高蛋白"]},
                    {"meal_type": "午餐", "name": "香煎鸡胸+糙米饭", "ingredients": [{"name": "鸡胸肉", "amount": "150g"}, {"name": "糙米", "amount": "100g"}, {"name": "西兰花", "amount": "150g"}], "cook_method": "鸡胸肉腌制后煎至金黄，西兰花焯水", "calories_estimate": 450, "protein_estimate": 45, "tags": ["高蛋白", "减脂"]},
                    {"meal_type": "晚餐", "name": "鸡丝沙拉", "ingredients": [{"name": "鸡胸肉", "amount": "100g"}, {"name": "西兰花", "amount": "150g"}, {"name": "鸡蛋", "amount": "1个"}], "cook_method": "鸡胸肉撕丝，西兰花焯水，鸡蛋切片混合", "calories_estimate": 300, "protein_estimate": 35, "tags": ["低脂", "高蛋白"]},
                ],
                "total_calories": 1000, "total_protein": 93,
                "tips": ["鸡胸肉提前腌制更嫩", "西兰花焯水后过凉水保持翠绿"],
                "missing_ingredients": ["建议补充少许橄榄油或柠檬汁调味"],
            },
            "鸡蛋_西红柿_面条": {
                "meal_plan": [
                    {"meal_type": "早餐", "name": "水煮蛋+西红柿", "ingredients": [{"name": "鸡蛋", "amount": "1个"}, {"name": "西红柿", "amount": "1个"}], "cook_method": "鸡蛋煮熟，西红柿切片", "calories_estimate": 150, "protein_estimate": 7, "tags": ["快手", "低卡"]},
                    {"meal_type": "午餐", "name": "番茄鸡蛋面", "ingredients": [{"name": "面条", "amount": "150g"}, {"name": "鸡蛋", "amount": "2个"}, {"name": "西红柿", "amount": "2个"}], "cook_method": "西红柿炒出汁，鸡蛋炒熟，加水和面条煮", "calories_estimate": 450, "protein_estimate": 20, "tags": ["家常", "饱腹"]},
                    {"meal_type": "晚餐", "name": "番茄蛋花汤+拌面", "ingredients": [{"name": "面条", "amount": "100g"}, {"name": "鸡蛋", "amount": "1个"}, {"name": "西红柿", "amount": "1个"}], "cook_method": "西红柿煮汤淋蛋花，面条拌少量酱油", "calories_estimate": 350, "protein_estimate": 15, "tags": ["清淡", "快手"]},
                ],
                "total_calories": 950, "total_protein": 42,
                "tips": ["面条选荞麦面或全麦面更健康"],
                "missing_ingredients": ["建议补充绿叶蔬菜增加膳食纤维"],
            },
            "瘦猪肉_青椒_土豆": {
                "meal_plan": [
                    {"meal_type": "早餐", "name": "瘦肉粥+水煮蛋", "ingredients": [{"name": "瘦猪肉", "amount": "50g"}, {"name": "大米", "amount": "50g"}, {"name": "鸡蛋", "amount": "1个"}], "cook_method": "瘦猪肉切丝煮粥，鸡蛋煮熟", "calories_estimate": 320, "protein_estimate": 22, "tags": ["养胃", "高蛋白"]},
                    {"meal_type": "午餐", "name": "青椒土豆炒瘦肉", "ingredients": [{"name": "瘦猪肉", "amount": "120g"}, {"name": "青椒", "amount": "100g"}, {"name": "土豆", "amount": "150g"}], "cook_method": "瘦肉切片腌制滑炒，青椒土豆切丝快炒", "calories_estimate": 480, "protein_estimate": 35, "tags": ["家常", "高蛋白"]},
                    {"meal_type": "晚餐", "name": "瘦肉丸子汤+清炒时蔬", "ingredients": [{"name": "瘦猪肉", "amount": "80g"}, {"name": "土豆", "amount": "100g"}], "cook_method": "瘦肉剁碎做丸子煮汤，土豆蒸熟", "calories_estimate": 320, "protein_estimate": 26, "tags": ["清淡", "高蛋白"]},
                ],
                "total_calories": 1120, "total_protein": 83,
                "tips": ["瘦猪肉优先选猪里脊，脂肪含量更低", "少油快炒保留营养"],
                "missing_ingredients": ["建议搭配绿叶蔬菜补充膳食纤维"],
            },
        }

        best_match = None
        best_score = 0
        for template_key, template in templates.items():
            template_ings = set(template_key.split("_"))
            overlap = len(ing_set & template_ings)
            if overlap > best_score:
                best_score = overlap
                best_match = template

        if best_match and best_score >= 2:
            result = dict(best_match)
            result["crowd_type"] = crowd_type
            result["goal"] = goal
            result["fallback"] = True
            result["template_type"] = "food_recommend_fallback"
            return result

        return {
            "fallback": True, "template_type": "food_recommend_fallback",
            "meal_plan": [
                {"meal_type": "早餐", "name": "简单早餐", "ingredients": [{"name": "鸡蛋", "amount": "1个"}, {"name": "主食", "amount": "适量"}], "cook_method": "根据食材自由搭配", "calories_estimate": 300, "protein_estimate": 10, "tags": ["快手"]},
                {"meal_type": "午餐", "name": "营养午餐", "ingredients": [{"name": "蛋白质", "amount": "100g"}, {"name": "蔬菜", "amount": "200g"}, {"name": "主食", "amount": "150g"}], "cook_method": "蛋白质和蔬菜搭配烹饪", "calories_estimate": 500, "protein_estimate": 25, "tags": ["均衡"]},
                {"meal_type": "晚餐", "name": "清淡晚餐", "ingredients": [{"name": "蔬菜", "amount": "200g"}, {"name": "蛋白质", "amount": "50g"}], "cook_method": "轻烹饪，少油少盐", "calories_estimate": 350, "protein_estimate": 15, "tags": ["清淡"]},
            ],
            "total_calories": 1150, "total_protein": 50,
            "crowd_type": crowd_type, "goal": goal,
            "tips": ["食材有限建议补充更多蔬菜和蛋白质来源"],
            "missing_ingredients": ["绿叶蔬菜", "优质蛋白"],
        }

    # ---- 新增：运动建议兜底 ----

    def fallback_exercise_advice(self, user_profile: dict, goal: str = "保持健康", preferences: str = "", chronic_diseases: list = None) -> dict:
        """运动建议兜底"""
        if chronic_diseases is None:
            chronic_diseases = []
        bmi = user_profile.get("bmi", 0)

        return {
            "fallback": True, "template_type": "exercise_fallback",
            "goal": goal,
            "weekly_schedule": [
                {"day": "周一", "exercise_type": "快走或慢跑", "duration": "40分钟", "intensity": "中", "description": "心率控制在最大心率的60-70%", "calories_burn_estimate": 250},
                {"day": "周二", "exercise_type": "全身力量训练", "duration": "30分钟", "intensity": "中", "description": "深蹲3组×15次、俯卧撑3组×10次", "calories_burn_estimate": 200},
                {"day": "周三", "exercise_type": "休息或散步", "duration": "20分钟", "intensity": "低", "description": "轻松散步", "calories_burn_estimate": 80},
                {"day": "周四", "exercise_type": "间歇跑", "duration": "30分钟", "intensity": "高", "description": "快跑1分钟+慢走2分钟交替，重复10组", "calories_burn_estimate": 350},
                {"day": "周五", "exercise_type": "瑜伽或拉伸", "duration": "30分钟", "intensity": "低", "description": "全身拉伸和核心训练", "calories_burn_estimate": 120},
                {"day": "周六", "exercise_type": "有氧运动", "duration": "45分钟", "intensity": "中", "description": "游泳/骑行/跳绳", "calories_burn_estimate": 350},
                {"day": "周日", "exercise_type": "休息", "duration": "0", "intensity": "低", "description": "充分休息", "calories_burn_estimate": 0},
            ],
            "weekly_total_minutes": 195, "weekly_total_calories": 1350,
            "warm_up": "5-10分钟动态拉伸", "cool_down": "5-10分钟静态拉伸",
            "precautions": ["减脂需要配合饮食控制，创造300-500kcal热量缺口"],
            "progression_plan": "每2周增加5%运动量或强度",
        }

    # ---- 新增：健康反思兜底 ----

    def fallback_health_reflection(self, user_profile: dict, health_data: dict, concerns: list) -> dict:
        """健康反思兜底"""
        health_data = health_data or {}
        age = user_profile.get("age", 30)
        weight = user_profile.get("weight", 65)
        height = user_profile.get("height", 170)
        bmi = round(weight / ((height / 100) ** 2), 1) if height > 0 else 0

        key_findings = []
        action_plan = []
        risk_level = "low"

        if bmi > 28:
            key_findings.append(f"体重超标（BMI={bmi}）")
            action_plan.append("控制饮食，减少高热量食物摄入")
            risk_level = "high"
        elif bmi > 24:
            key_findings.append(f"超重（BMI={bmi}）")
            action_plan.append("适当控制饮食，保持热量平衡")
            risk_level = "medium"

        bp = health_data.get("recent_blood_pressure", {})
        if bp.get("systolic", 0) >= 140:
            key_findings.append(f"血压偏高（{bp.get('systolic')}/{bp.get('diastolic')}mmHg）")
            action_plan.append("减少盐分摄入，每日<5克")
            risk_level = "high"

        blood_sugar = health_data.get("recent_blood_sugar", 0)
        if blood_sugar > 6.1:
            key_findings.append(f"血糖偏高（{blood_sugar}mmol/L）")
            action_plan.append("控制碳水化合物摄入")
            risk_level = "medium"

        if not key_findings:
            key_findings = ["当前健康状况良好"]
        if not action_plan:
            action_plan = ["保持均衡饮食", "规律作息", "适度运动"]

        return {
            "fallback": True, "template_type": "health_reflection_fallback",
            "reflection_type": "health_status",
            "reflection": f"离线分析：{age}岁用户，BMI{bmi}，{'; '.join(key_findings)}。",
            "risk_level": risk_level,
            "key_findings": key_findings,
            "action_plan": action_plan,
            "tips": ["保持良好作息", "均衡饮食"],
        }


fallback_engine = LocalFallbackEngine()
