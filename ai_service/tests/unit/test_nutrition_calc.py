# -*- coding: utf-8 -*-
"""营养素计算器单测：BMR / BMI 分档 / TDEE / 汇总与折算 / 每日参考与达标判定"""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.nutrition_calc import (
    calc_bmr,
    calc_bmi,
    bmi_level,
    calc_tdee,
    sum_nutrients,
    per_100g,
    daily_limits,
    check_intake,
)


class TestBMR:
    def test_male_formula(self):
        # 男: 10*70 + 6.25*175 - 5*30 + 5 = 1648.75
        assert calc_bmr(70, 175, 30, "male") == pytest.approx(1648.75)

    def test_female_formula(self):
        # 女: 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
        assert calc_bmr(60, 165, 30, "female") == pytest.approx(1320.25)

    def test_gender_alias(self):
        assert calc_bmr(70, 175, 30, "男") == calc_bmr(70, 175, 30, "male")
        assert calc_bmr(60, 165, 30, "女") == calc_bmr(60, 165, 30, "female")

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            calc_bmr(70, 175, 30, "unknown")
        with pytest.raises(ValueError):
            calc_bmr(0, 175, 30, "male")


class TestBMI:
    def test_bmi_value(self):
        # 60kg / 165cm → 60 / 1.65² ≈ 22.04
        assert calc_bmi(60, 165) == pytest.approx(22.0386, abs=1e-3)

    def test_bmi_level_boundaries(self):
        # 五档边界：<18.5 过低；<20 偏低；<=24 正常；<=28 偏高；>28 超高
        assert bmi_level(18.4) == "过低"
        assert bmi_level(18.5) == "偏低"
        assert bmi_level(19.9) == "偏低"
        assert bmi_level(20.0) == "正常"
        assert bmi_level(24.0) == "正常"
        assert bmi_level(24.1) == "偏高"
        assert bmi_level(28.0) == "偏高"
        assert bmi_level(28.1) == "超高"


class TestTDEE:
    def test_all_factors(self):
        bmr = 1600.0
        assert calc_tdee(bmr, "sedentary") == pytest.approx(1920.0)
        assert calc_tdee(bmr, "light") == pytest.approx(2200.0)
        assert calc_tdee(bmr, "moderate") == pytest.approx(2480.0)
        assert calc_tdee(bmr, "intense") == pytest.approx(2760.0)

    def test_chinese_alias_and_numeric_factor(self):
        assert calc_tdee(1000.0, "久坐") == pytest.approx(1200.0)
        assert calc_tdee(1000.0, 1.55) == pytest.approx(1550.0)

    def test_invalid_level(self):
        with pytest.raises(ValueError):
            calc_tdee(1600.0, "extreme")


class TestSumAndPer100g:
    def test_sum_nutrients(self):
        items = [
            {"calorie": 100, "protein": 5.0},
            {"calorie": 150, "protein": 3.0, "fat": 2.0},
            {"calorie": None, "dha": 100},  # None 跳过
        ]
        total = sum_nutrients(items)
        assert total["calorie"] == pytest.approx(250.0)
        assert total["protein"] == pytest.approx(8.0)
        assert total["fat"] == pytest.approx(2.0)
        assert total["dha"] == pytest.approx(100.0)

    def test_per_100g(self):
        # 250g 食物含 500kcal、蛋白质 25g、GI 70 → 每100g: 200kcal/10g蛋白质
        out = per_100g({"calorie": 500, "protein": 25, "gi_value": 70}, 250)
        assert out["calorie"] == pytest.approx(200.0)
        assert out["protein"] == pytest.approx(10.0)
        assert out["gi_value"] == 70  # GI 不随重量折算

    def test_per_100g_invalid_weight(self):
        with pytest.raises(ValueError):
            per_100g({"calorie": 100}, 0)


class TestDailyLimitsAndCheck:
    def test_daily_limits_adult(self):
        lm = daily_limits("male", 30)
        assert lm["calorie"] == {"min": 1800, "max": 3000}
        assert lm["protein"]["min"] == 65
        assert lm["calcium"]["min"] == 800
        assert lm["folic_acid"]["min"] == 400
        assert lm["dha"]["min"] == 200

    def test_daily_limits_senior_calcium(self):
        assert daily_limits("female", 60)["calcium"]["min"] == 1000

    def test_check_intake_status(self):
        limits = daily_limits("male", 30)
        nutrients = {
            "calorie": 1500,     # < 1800 → 不足
            "protein": 80,       # >= 65 → 达标
            "carb": 500,         # > 上限 → 超标
            "diet_fiber": 25,    # 达标
            "calcium": 800,      # 达标
            "folic_acid": 300,   # < 400 → 不足
            "dha": 200,          # 达标
        }
        status = {e["name"]: e["status"] for e in check_intake(nutrients, limits)["each"]}
        assert status["热量(千卡)"] == "不足"
        assert status["蛋白质(g)"] == "达标"
        assert status["碳水(g)"] == "超标"
        assert status["膳食纤维(g)"] == "达标"
        assert status["钙(mg)"] == "达标"
        assert status["叶酸(µg)"] == "不足"
        assert status["DHA(mg)"] == "达标"

    def test_check_intake_skips_fields_without_reference(self):
        limits = daily_limits("female", 25)
        r = check_intake({"gi_value": 70}, limits)
        assert r["each"] == []
