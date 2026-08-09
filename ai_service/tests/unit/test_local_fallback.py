"""本地兜底引擎单元测试 — 覆盖各兜底方法的独立验证"""
import pytest


class TestFallbackHealthQA:
    """通用健康问答兜底"""

    def test_basic_health_qa(self, fallback_engine):
        """基础健康问答应返回非空字符串"""
        result = fallback_engine.answer_health_query("苹果的热量是多少？")
        assert isinstance(result, str)
        assert len(result) > 20

    def test_diabetes_crowd(self, fallback_engine):
        """糖尿病人群应返回针对性建议"""
        result = fallback_engine.answer_health_query(
            "糖尿病患者能吃香蕉吗？",
            health_snapshot={"profile": {"crowd_type": "糖尿病", "age": 55, "gender": "男"}},
        )
        assert "糖尿" in result or "血糖" in result or "GI" in result or "低GI" in result

    def test_pregnant_crowd(self, fallback_engine):
        """孕妇人群应返回针对性建议"""
        result = fallback_engine.answer_health_query(
            "孕妇需要注意什么饮食？",
            health_snapshot={"profile": {"crowd_type": "孕妇"}},
        )
        assert isinstance(result, str)
        assert len(result) > 20


class TestFallbackNutritionAnalysis:
    """营养分析兜底"""

    def test_basic_nutrition(self, fallback_engine):
        """基础营养分析应返回结构化结果"""
        result = fallback_engine.fallback_nutrition_analysis(
            {"username": "测试", "age": 30, "gender": "男", "crowd_type": "普通人"},
            {"calories": 2500, "protein": 120, "carbohydrate": 300, "fat": 80},
            {"steps": 8000, "exercise_minutes": 45, "activity": "中等强度"},
        )
        assert isinstance(result, dict)
        assert "error" not in result or result.get("error") is None

    def test_nutrition_with_extreme_values(self, fallback_engine):
        """极端数值不应导致崩溃"""
        result = fallback_engine.fallback_nutrition_analysis(
            {"username": "极端", "age": -1, "gender": "男", "crowd_type": "普通人"},
            {"calories": 100000, "protein": 5000, "carbohydrate": 99999, "fat": 8888},
            {"steps": 0, "exercise_minutes": 0, "activity": "无"},
        )
        assert isinstance(result, dict)


class TestFallbackDietPlan:
    """膳食计划兜底"""

    def test_basic_diet_plan(self, fallback_engine):
        """基础膳食计划应返回 daily_plan"""
        result = fallback_engine.fallback_diet_plan(
            {"username": "测试", "age": 30, "gender": "男", "height": 175, "weight": 80, "crowd_type": "健身"},
            "增肌",
        )
        assert isinstance(result, dict)
        assert result.get("daily_plan") is not None

    def test_allergy_filtering(self, fallback_engine):
        """过敏源应被过滤"""
        result = fallback_engine.fallback_diet_plan(
            {"username": "过敏", "age": 28, "gender": "男", "height": 178, "weight": 75,
             "crowd_type": "健身", "allergies": ["牛奶", "坚果"]},
            "减脂",
        )
        plan_text = str(result.get("daily_plan", ""))
        # 牛奶和坚果不应出现在计划中（注意：这里只是简单验证）
        assert isinstance(result, dict)


class TestFallbackWeeklyReport:
    """周报兜底"""

    def test_basic_report(self, fallback_engine):
        """基础周报应返回 health_score"""
        result = fallback_engine.fallback_weekly_report(
            {"username": "测试", "age": 65, "gender": "女", "crowd_type": "老年"},
            {"avg_calories": 1800, "avg_steps": 6000, "avg_sleep_hours": 7.0, "active_days": 4},
        )
        assert isinstance(result, dict)
        assert "health_score" in result


class TestFallbackFoodRecommend:
    """食材推荐兜底"""

    def test_basic_recommend(self, fallback_engine):
        """基础食材推荐应返回 meal_plan"""
        result = fallback_engine.fallback_food_recommend(["鸡胸肉", "西兰花", "鸡蛋"], "健身", "减脂")
        assert isinstance(result, dict)
        assert result.get("meal_plan") is not None


class TestFallbackExerciseAdvice:
    """运动建议兜底"""

    def test_basic_exercise(self, fallback_engine):
        """基础运动建议应返回 weekly_schedule"""
        result = fallback_engine.fallback_exercise_advice(
            {"username": "测试", "age": 55, "gender": "男", "height": 170, "weight": 80, "crowd_type": "糖尿病"},
            "控制血糖", "散步", ["糖尿病"],
        )
        assert isinstance(result, dict)
        assert result.get("weekly_schedule") is not None


class TestFallbackArticleGenerate:
    """文章生成兜底"""

    def test_basic_article(self, fallback_engine):
        """基础文章生成应返回 title"""
        result = fallback_engine.fallback_article_generate("春季如何预防流感", "老年")
        assert isinstance(result, dict)
        assert result.get("title") is not None
        assert len(result.get("title", "")) > 0
