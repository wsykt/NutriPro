# -*- coding: utf-8 -*-
"""校验组件单元测试：事实校验 / 数值检查 / 安全拦截 / 统一流水线 / orchestrator 集成

验证范围：
1. FactChecker：绝对化用语、无依据结论、LLM 异常降级
2. NumericChecker：JSON 数值区间、文本数值抽取、宏量营养素配比
3. SafetyInterceptor：高危模式 BLOCK、人群禁忌、免责声明缺失
4. ValidatorPipeline：三组件串联、blocked 决策
5. orchestrator._validate_and_guard 集成（Mock 方式）

使用 unittest（不依赖 pytest）。
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestFactChecker(unittest.TestCase):
    """事实校验组件"""

    def setUp(self):
        from agent.validators.fact_checker import FactChecker
        self.fc = FactChecker()

    def test_absolute_claim_detected(self):
        res = self.fc.check("这款产品100%有效，绝对安全无副作用")
        self.assertEqual(res["severity"], "medium")
        self.assertTrue(any(i["type"] == "absolute_claim" for i in res["issues"]))

    def test_clean_text_passes(self):
        res = self.fc.check("建议每天摄入25克膳食纤维，多吃蔬菜水果。")
        self.assertTrue(res["passed"])
        self.assertEqual(len(res["issues"]), 0)

    def test_unsupported_claim_with_kb(self):
        """结论性表述但知识库不含对应数字 → 提示 unsupported"""
        res = self.fc.check(
            "研究表明每日摄入87.5克蛋白质可显著降低血压",
            kb_context="中国居民膳食指南：蛋白质每日推荐摄入量60克。",
        )
        self.assertTrue(any(i["type"] == "unsupported_claim" for i in res["issues"]))

    def test_claim_supported_by_kb_numbers(self):
        """知识库含相同数字 → 不误报"""
        res = self.fc.check(
            "研究表明每日蛋白质摄入60克可维持健康",
            kb_context="中国居民膳食指南：蛋白质每日推荐摄入量60克。",
        )
        self.assertFalse(any(i["type"] == "unsupported_claim" for i in res["issues"]))

    def test_empty_text_passes(self):
        res = self.fc.check("")
        self.assertTrue(res["passed"])

    def test_json_result(self):
        res = self.fc.check_json({"tips": ["100%有效"]})
        self.assertEqual(res["severity"], "medium")

    def test_check_with_llm_exception_fallback(self):
        """LLM 校验异常 → 默认通过"""
        self.fc.llm = MagicMock()
        self.fc.llm.chat_json.side_effect = Exception("boom")
        res = self.fc.check_with_llm("内容")
        self.assertTrue(res["passed"])

    def test_check_with_llm_returns_issues(self):
        self.fc.llm = MagicMock()
        self.fc.llm.chat_json.return_value = {
            "passed": False,
            "issues": [{"type": "fact_error", "severity": "high", "message": "数据错误"}],
        }
        res = self.fc.check_with_llm("内容")
        self.assertFalse(res["passed"])
        self.assertEqual(res["severity"], "high")


class TestNumericChecker(unittest.TestCase):
    """数值检查组件"""

    def setUp(self):
        from agent.validators.numeric_checker import NumericChecker
        self.nc = NumericChecker()

    def test_valid_diet_plan_passes(self):
        d = {"total_calories": 1800,
             "nutrition_breakdown": {"protein": 70, "carbohydrate": 220, "fat": 55},
             "daily_plan": {"早餐": [{"food": "x"}], "午餐": [{"food": "y"}], "晚餐": [{"food": "z"}]}}
        res = self.nc.check_json(d, "diet_plan")
        self.assertTrue(res["passed"])
        self.assertEqual(len(res["issues"]), 0)

    def test_out_of_range_calories(self):
        d = {"total_calories": 9999,
             "nutrition_breakdown": {"protein": 70, "carbohydrate": 220, "fat": 55}}
        res = self.nc.check_json(d, "diet_plan")
        self.assertFalse(res["passed"])
        self.assertTrue(any("总热量" in i["message"] for i in res["issues"]))

    def test_rule_scoping_by_func_type(self):
        """food_recommend 不检查 diet_plan 的总热量规则"""
        d = {"total_calories": 1800}  # 对 diet_plan 有效，对 food 应用另一规则
        res = self.nc.check_json(d, "food_recommend")
        # total_calories 对 food 不适用（用 total_calories_food），无报错
        self.assertTrue(res["passed"])

    def test_food_recommend_rules(self):
        d = {"meal_plan": [
            {"meal_type": "早餐", "calories_estimate": 300, "protein_estimate": 20},
            {"meal_type": "午餐", "calories_estimate": 400, "protein_estimate": 25},
            {"meal_type": "晚餐", "calories_estimate": 350, "protein_estimate": 22},
        ], "total_calories": 1050, "total_protein": 67}
        res = self.nc.check_json(d, "food_recommend")
        self.assertTrue(res["passed"])

    def test_text_extraction(self):
        text = "建议每日食盐摄入量不超过8克，每周运动150分钟，饮水2000毫升。"
        res = self.nc.check_text(text, "qa")
        self.assertTrue(any("盐摄入" in i["message"] for i in res["issues"]))  # 8g > 6g

    def test_macro_balance(self):
        """蛋白/碳水/脂肪供能比失衡检测"""
        res = self.nc.check_macro_balance(protein=200, carb=50, fat=100)
        # 200*4=800, 50*4=200, 100*9=900 → total 1900
        # protein=42%, carb=10.5%, fat=47% → 均失衡
        self.assertFalse(res["passed"])
        self.assertEqual(res["severity"], "high")
        self.assertEqual(len(res["issues"]), 3)

    def test_macro_balance_ok(self):
        res = self.nc.check_macro_balance(protein=70, carb=240, fat=60)
        # 70*4=280, 240*4=960, 60*9=540 → total 1780
        # protein=15.7%, carb=53.9%, fat=30.3% → 基本达标
        self.assertTrue(res["passed"])

    def test_get_nested_wildcard(self):
        d = {"meal_plan": [
            {"meal_type": "早餐", "calories_estimate": 300},
            {"meal_type": "午餐", "calories_estimate": 9999},
        ]}
        values = self.nc._get_nested(d, "meal_plan.*.calories_estimate")
        self.assertIn(300, values)
        self.assertIn(9999, values)

    def test_exercise_rules(self):
        d = {"weekly_schedule": [
            {"day": "周一", "exercise_type": "快走", "duration": "30", "calories_burn_estimate": 200},
        ], "weekly_total_minutes": 400, "weekly_total_calories": 3000}
        res = self.nc.check_json(d, "exercise")
        self.assertFalse(res["passed"])  # 400 > 300 WHO 上限
        self.assertTrue(any("周运动总时长" in i["message"] for i in res["issues"]))


class TestSafetyInterceptor(unittest.TestCase):
    """安全风险拦截组件"""

    def setUp(self):
        from agent.validators.safety_interceptor import SafetyInterceptor
        self.si = SafetyInterceptor()

    def test_high_risk_blocks(self):
        res = self.si.check("建议断食3天排毒，效果绝对保证")
        self.assertEqual(res["level"], "block")
        self.assertFalse(res["passed"])

    def test_pregnant_crowd_ban(self):
        res = self.si.check("建议每日进行高强度冲刺跑训练", target_crowd="孕妇")
        self.assertFalse(res["passed"])

    def test_normal_advice_passes(self):
        res = self.si.check("建议每天步行30分钟，多吃蔬菜水果，保持心情愉快。")
        self.assertTrue(res["passed"])
        # 含"建议"但缺免责声明 → info（不阻断），正常建议本身不告警
        self.assertIn(res["level"], ("ok", "info"))

    def test_missing_disclaimer_detected(self):
        res = self.si.check("建议高血压患者每天坚持适量运动。")
        self.assertTrue(res["needs_disclaimer"])
        self.assertTrue(any(i["type"] == "missing_disclaimer" for i in res["issues"]))

    def test_disclaimer_present(self):
        res = self.si.check("建议每天适量运动。温馨提示：本内容仅供膳食科普参考，不构成医疗建议。")
        self.assertFalse(res["needs_disclaimer"])

    def test_medical_boundary_warn(self):
        res = self.si.check("我可以为你诊断糖尿病类型并给出处方剂量。")
        self.assertEqual(res["level"], "warn")
        self.assertTrue(res["passed"])
        self.assertTrue(any(i["type"] == "medical_boundary" for i in res["issues"]))

    def test_stop_medication_blocks(self):
        """停用降压药属于高危医疗越界 → 直接 BLOCK（比 WARN 更严格）"""
        res = self.si.check("建议立即停用降压药，改用自然疗法。")
        self.assertEqual(res["level"], "block")
        self.assertFalse(res["passed"])

    def test_json_result_scan(self):
        d = {"tips": ["建议断食2天排毒"], "precautions": []}
        res = self.si.check_json(d, "孕妇")
        self.assertEqual(res["level"], "block")

    def test_json_empty_passes(self):
        res = self.si.check_json({})
        self.assertEqual(res["level"], "ok")

    def test_build_safe_response_qa(self):
        res = self.si.build_safe_response("qa", "原内容", [{"severity": "block", "message": "危险"}])
        self.assertIn("拦截", res)

    def test_build_safe_response_structured(self):
        res = self.si.build_safe_response("diet_plan", {"x": 1}, [{"severity": "block", "message": "危险"}])
        self.assertTrue(res["blocked"])

    def test_chronic_disease_mapping(self):
        res = self.si.check("建议空腹进行高强度间歇训练", chronic_diseases=["糖尿病"])
        self.assertFalse(res["passed"])


class TestValidatorPipeline(unittest.TestCase):
    """统一校验流水线"""

    def setUp(self):
        from agent.validators.validator import ValidatorPipeline
        self.pipe = ValidatorPipeline()

    def test_clean_diet_plan_passes(self):
        d = {"total_calories": 1800,
             "nutrition_breakdown": {"protein": 70, "carbohydrate": 220, "fat": 55},
             "daily_plan": {"早餐": [{"food": "x"}], "午餐": [{"food": "y"}], "晚餐": [{"food": "z"}],
                            "加餐": [{"food": "w"}]},
             "tips": ["建议多喝水"]}
        v = self.pipe.validate("diet_plan", d, "普通人")
        self.assertEqual(v["level"], "ok")
        self.assertTrue(v["passed"])
        self.assertFalse(v["blocked"])

    def test_blocked_on_high_risk(self):
        d = {"tips": ["建议断食3天排毒"], "daily_plan": {}}
        v = self.pipe.validate("diet_plan", d, "普通人")
        self.assertEqual(v["level"], "block")
        self.assertTrue(v["blocked"])
        self.assertFalse(v["passed"])

    def test_warn_on_out_of_range(self):
        d = {"total_calories": 9999, "nutrition_breakdown": {}, "daily_plan": {}}
        v = self.pipe.validate("diet_plan", d)
        self.assertEqual(v["level"], "warn")
        self.assertTrue(v["passed"])  # 数值问题不阻断

    def test_disabled_pipeline(self):
        from agent.validators.validator import ValidatorPipeline
        pipe = ValidatorPipeline(enabled=False)
        v = pipe.validate("qa", "任何内容")
        self.assertEqual(v["level"], "ok")
        self.assertTrue(v["passed"])

    def test_qa_text_flow(self):
        v = self.pipe.validate("qa", "建议每天食盐不超过5克，多吃蔬菜。", "高血压患者")
        # 高血压要点 + 免责声明缺失 → warn/info
        self.assertIn(v["level"], ("ok", "warn"))

    def test_issues_include_section_tag(self):
        d = {"total_calories": 9999, "nutrition_breakdown": {}, "daily_plan": {}}
        v = self.pipe.validate("diet_plan", d)
        if v["issues"]:
            self.assertTrue(all("section" in i for i in v["issues"]))


class TestOrchestratorValidationIntegration(unittest.TestCase):
    """orchestrator 校验集成（Mock 方式，不加载真实模型）"""

    def setUp(self):
        from agent.orchestrator import AgentOrchestrator
        self.orch = AgentOrchestrator()
        # 手动注入校验流水线（绕过 init 的真实依赖）
        from agent.validators.validator import ValidatorPipeline
        self.orch._validator = ValidatorPipeline()
        self.orch._retriever = MagicMock()
        self.orch._retriever.search.return_value = []

    def test_meta_validation_attached(self):
        """结构化结果附加 _meta.validation"""
        result = {"total_calories": 1800, "nutrition_breakdown": {"protein": 70, "carbohydrate": 220, "fat": 55},
                  "daily_plan": {"早餐": [{"food": "x"}], "午餐": [{"food": "y"}], "晚餐": [{"food": "z"}]}}
        out = self.orch._validate_and_guard(
            "diet_plan", "diet_plan", result, False, None,
            {"user_profile": {"crowd_type": "普通人"}, "goal": "减脂"},
        )
        self.assertIn("_meta", out)
        self.assertIn("validation", out["_meta"])
        self.assertIn("validator", out["_meta"]["validation"])

    def test_blocked_result_replaced(self):
        """高风险 diet_plan 被替换为安全响应"""
        result = {"tips": ["建议断食3天排毒"], "daily_plan": {}}
        out = self.orch._validate_and_guard(
            "diet_plan", "diet_plan", result, False, None,
            {"user_profile": {"crowd_type": "普通人"}},
        )
        self.assertTrue(isinstance(out, dict))
        self.assertTrue(out.get("blocked", False))

    def test_qa_text_guard(self):
        """qa 文本高风险 → 替换为安全响应"""
        out = self.orch._guard_qa_response("建议断食3天排毒，绝对保证有效")
        self.assertIn("拦截", out)

    def test_qa_text_normal_preserved(self):
        out = self.orch._guard_qa_response("建议每天步行30分钟，多吃蔬菜。")
        self.assertIn("步行", out)

    def test_extract_validation_context(self):
        crowd, chronic = self.orch._extract_validation_context(
            "qa", {"user_profile": {"crowd_type": "孕妇", "chronic_diseases": ["糖尿病"]}})
        self.assertEqual(crowd, "孕妇")
        self.assertIn("糖尿病", chronic)


if __name__ == "__main__":
    unittest.main(verbosity=2)
