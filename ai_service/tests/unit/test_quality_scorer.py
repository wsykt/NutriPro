"""QualityScorer 单元测试 — 覆盖评分、违规检测、幻觉检测、免责声明"""
import pytest


class TestQualityScorerBasic:
    """基础评分逻辑"""

    def test_perfect_answer_scores_100(self, scorer):
        """完美回答（含免责声明、无违规）应得满分"""
        result = scorer.score(
            "苹果的热量是多少？",
            "苹果每100g约52千卡，属于低热量水果。富含膳食纤维和维生素C。【温馨提示：本内容为膳食科普参考，不构成医疗建议。】",
            kb_used=True,
        )
        assert result["score"] == 100
        assert result["has_disclaimer"] is True
        assert result["has_diagnosis"] is False

    def test_short_answer_deducted(self, scorer):
        """回答过短（<30字）应扣分"""
        result = scorer.score("苹果热量？", "约52千卡。", kb_used=True)
        assert result["score"] < 100
        assert any("过短" in w for w in result["warnings"])

    def test_no_disclaimer_deducted(self, scorer):
        """缺少免责声明应扣5分"""
        result = scorer.score(
            "苹果热量？",
            "苹果每100g约52千卡，属于低热量水果，富含膳食纤维。",
            kb_used=True,
        )
        assert result["has_disclaimer"] is False
        assert result["score"] <= 95


class TestMedicalDiagnosisDetection:
    """医疗诊断违规检测"""

    def test_diagnosis_detected(self, scorer):
        """包含诊断性语言应被标记"""
        result = scorer.score(
            "我头痛吃什么药？",
            "根据你的症状，诊断为偏头痛，建议服用药物治疗布洛芬每次200mg。",
        )
        assert result["has_diagnosis"] is True
        assert result["score"] < 100
        assert any("医疗" in i for i in result["issues"])

    def test_normal_answer_no_diagnosis(self, scorer):
        """正常科普不应触发诊断标记"""
        result = scorer.score(
            "头痛吃什么食物好？",
            "头痛时可以尝试富含镁的食物如香蕉、坚果。【温馨提示：仅供参考】",
        )
        assert result["has_diagnosis"] is False


class TestHallucinationDetection:
    """幻觉/虚假断言检测"""

    def test_absolute_claim_detected(self, scorer):
        """绝对化表述应被标记为幻觉"""
        result = scorer.score(
            "喝醋能治癌症吗？",
            "据我所知，喝醋绝对可以治愈癌症，肯定有效。",
        )
        assert result["has_hallucination"] is True
        assert result["score"] < 100

    def test_normal_answer_no_hallucination(self, scorer):
        """正常回答不触发幻觉"""
        result = scorer.score(
            "喝醋健康吗？",
            "适量饮用醋有助于消化，但不建议过量。【温馨提示：仅供参考】",
        )
        assert result["has_hallucination"] is False


class TestNutrientRangeDetection:
    """营养数值范围检测"""

    def test_out_of_range_nutrient(self, scorer):
        """营养数值超出正常范围应报警告"""
        result = scorer.score(
            "苹果热量？",
            "苹果热量为9999kcal/100g。",
        )
        assert result["has_nutrient_error"] is True
        assert any("超出" in w for w in result["warnings"])

    def test_normal_nutrient_no_warning(self, scorer):
        """正常营养数值不报警告"""
        result = scorer.score(
            "苹果热量？",
            "苹果热量约为52kcal/100g。【温馨提示：仅供参考】",
        )
        assert result["has_nutrient_error"] is False


class TestResponseStructure:
    """返回结构完整性"""

    def test_return_keys(self, scorer):
        """返回应包含所有必要字段"""
        result = scorer.score("测试", "测试回答")
        expected_keys = {"score", "issues", "warnings", "has_diagnosis",
                         "has_nutrient_error", "has_hallucination",
                         "has_disclaimer", "response_length", "kb_used"}
        assert set(result.keys()) == expected_keys

    def test_score_range(self, scorer):
        """分数应在 0-100 之间"""
        result = scorer.score("测试", "测试回答")
        assert 0 <= result["score"] <= 100

    def test_response_length_accurate(self, scorer):
        """response_length 应准确反映文本长度"""
        text = "这是一段测试文本"
        result = scorer.score("测试", text)
        assert result["response_length"] == len(text)
