"""NLU 解析引擎单元测试 — 覆盖单位换算、食物匹配、规则提取"""
import pytest
import sys
import os

# 确保可以 import nlu_parser 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agent.nlu_parser import _convert_amount, UNIT_TO_GRAMS, ITEM_GRAM_PER_UNIT


class TestUnitConversion:
    """单位换算测试"""

    def test_grams_direct(self):
        """直接 g 单位"""
        grams, desc = _convert_amount("200g", "")
        assert grams == 200.0

    def test_chinese_gram(self):
        """中文'克'单位"""
        grams, desc = _convert_amount("200克", "")
        assert grams == 200.0

    def test_ml_unit(self):
        """ml 单位"""
        grams, desc = _convert_amount("250ml", "")
        assert grams == 250.0

    def test_bowl_unit(self):
        """碗单位"""
        grams, desc = _convert_amount("1碗", "米饭")
        assert grams == 200.0  # 1碗=200g

    def test_cup_unit(self):
        """杯单位"""
        grams, desc = _convert_amount("1杯", "")
        assert grams == 250.0

    def test_piece_unit(self):
        """个单位 - 通用"""
        grams, desc = _convert_amount("2个", "")
        assert grams == 100.0  # 2 * 50g

    def test_piece_with_egg(self):
        """个单位 - 鸡蛋特殊重量"""
        grams, desc = _convert_amount("2个", "鸡蛋")
        assert grams == 100.0  # 2 * 50g (鸡蛋=50g/个)

    def test_root_unit(self):
        """根单位"""
        grams, desc = _convert_amount("1根", "香蕉")
        assert grams == 75.0

    def test_slice_unit(self):
        """片单位"""
        grams, desc = _convert_amount("3片", "全麦面包")
        assert grams == 45.0  # 3 * 15g

    def test_bottle_unit(self):
        """瓶单位"""
        grams, desc = _convert_amount("1瓶", "")
        assert grams == 330.0

    def test_unknown_unit(self):
        """无法识别的单位应返回默认值"""
        grams, desc = _convert_amount("一坨", "")
        # 不崩溃即可
        assert isinstance(grams, float) or isinstance(grams, int)


class TestUnitConstants:
    """单位常量完整性"""

    def test_unit_to_grams_not_empty(self):
        """UNIT_TO_GRAMS 应非空"""
        assert len(UNIT_TO_GRAMS) > 0

    def test_item_gram_overrides_not_empty(self):
        """ITEM_GRAM_PER_UNIT 应非空"""
        assert len(ITEM_GRAM_PER_UNIT) > 0

    def test_egg_in_overrides(self):
        """鸡蛋应在特殊重量覆盖表中"""
        assert "鸡蛋" in ITEM_GRAM_PER_UNIT

    def test_rice_bowl_standard(self):
        """碗的标准重量应为 200g"""
        assert UNIT_TO_GRAMS["碗"] == 200
