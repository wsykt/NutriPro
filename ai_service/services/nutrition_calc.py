# -*- coding: utf-8 -*-
"""
完整营养素计算器（纯计算，无 I/O、不依赖 LLM、不连数据库）
=============================================================
食物数据库营养素字段固定为：
    热量(千卡 calorie)、蛋白质(g protein)、碳水(g carb)、脂肪(g fat)、
    膳食纤维(g diet_fiber)、GI值(gi_value)、钙(mg calcium)、
    叶酸(µg folic_acid)、DHA(mg dha)

提供能力：
    - calc_bmr / calc_bmi / bmi_level / calc_tdee
    - sum_nutrients / per_100g
    - daily_limits（参照《中国居民膳食指南2022》建议值）
    - check_intake（摄入达标/超标判定）

所有函数均为纯函数：只做数值计算，不读写文件、不访问网络。
"""

from __future__ import annotations
from typing import Dict, List, Union

# 营养素字段显示名（中文，用于判定结果展示）
NUTRIENT_NAMES: Dict[str, str] = {
    "calorie": "热量(千卡)",
    "protein": "蛋白质(g)",
    "carb": "碳水(g)",
    "fat": "脂肪(g)",
    "diet_fiber": "膳食纤维(g)",
    "gi_value": "GI值",
    "calcium": "钙(mg)",
    "folic_acid": "叶酸(µg)",
    "dha": "DHA(mg)",
}

# 活动系数（与体力活动水平对应）
ACTIVITY_FACTORS: Dict[str, float] = {
    "sedentary": 1.2,    # 久坐
    "light": 1.375,      # 轻度活动
    "moderate": 1.55,    # 中度活动
    "intense": 1.725,    # 高强度活动
}
ACTIVITY_ALIASES: Dict[str, str] = {
    "sedentary": "sedentary", "久坐": "sedentary",
    "light": "light", "轻度": "light",
    "moderate": "moderate", "中度": "moderate",
    "intense": "intense", "高强度": "intense", "heavy": "intense", "high": "intense",
}


def _normalize_gender(gender: str) -> str:
    """性别归一化：male/female（或 男/女）"""
    g = str(gender).strip().lower()
    if g in ("male", "男", "m"):
        return "male"
    if g in ("female", "女", "f"):
        return "female"
    raise ValueError(f"未知性别: {gender}，请使用 male/female 或 男/女")


def _validate_positive(value: Union[int, float], name: str) -> None:
    if value is None or value <= 0:
        raise ValueError(f"{name} 必须为正数，收到: {value!r}")


# ============================================================
# 一、基础代谢率 / BMI / 能量消耗
# ============================================================

def calc_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """基础代谢率 BMR（Mifflin-St Jeor 公式）

    男：10×体重 + 6.25×身高 − 5×年龄 + 5
    女：10×体重 + 6.25×身高 − 5×年龄 − 161
    """
    _validate_positive(weight_kg, "weight_kg")
    _validate_positive(height_cm, "height_cm")
    if age <= 0:
        raise ValueError("age 必须为正数")
    g = _normalize_gender(gender)
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if g == "male" else base - 161


def calc_bmi(weight_kg: float, height_cm: float) -> float:
    """体质指数 BMI = 体重(kg) / 身高(m)²"""
    _validate_positive(weight_kg, "weight_kg")
    _validate_positive(height_cm, "height_cm")
    return weight_kg / ((height_cm / 100.0) ** 2)


def bmi_level(bmi: float) -> str:
    """BMI 五档分级（阈值：<18.5 过低，<20 偏低，<=24 正常，<=28 偏高，>28 超高）"""
    if bmi < 18.5:
        return "过低"
    if bmi < 20:
        return "偏低"
    if bmi <= 24:
        return "正常"
    if bmi <= 28:
        return "偏高"
    return "超高"


def calc_tdee(bmr: float, activity_level: Union[str, float]) -> float:
    """每日总能量消耗 TDEE = BMR × 活动系数

    activity_level 接受档位名（sedentary 久坐 1.2 / light 轻度 1.375 /
    moderate 中度 1.55 / intense 高强度 1.725，支持中文别名），
    也可直接传入数值系数。
    """
    if isinstance(activity_level, (int, float)) and not isinstance(activity_level, bool):
        factor = float(activity_level)
    else:
        key = ACTIVITY_ALIASES.get(str(activity_level).strip().lower())
        if key is None:
            raise ValueError(
                f"未知活动水平: {activity_level}，可选: {list(ACTIVITY_FACTORS)}")
        factor = ACTIVITY_FACTORS[key]
    return bmr * factor


# ============================================================
# 二、多食物汇总 / 每100g折算
# ============================================================

def sum_nutrients(items: List[Dict]) -> Dict[str, float]:
    """汇总多食物营养素

    items: [{字段名: 数值}, ...]，字段名与 food 表一致；
    缺失字段按 0 处理，None 值跳过。
    """
    total: Dict[str, float] = {}
    for item in items:
        if not item:
            continue
        for key, value in item.items():
            if value is None:
                continue
            total[key] = total.get(key, 0.0) + float(value)
    return total


def per_100g(nutrients: Dict, weight_g: float) -> Dict[str, float]:
    """将某份食物的营养素折算为每 100g 含量

    注意：GI 值不随重量折算（GI 是食物固有属性，与摄入量无关），原样保留。
    """
    _validate_positive(weight_g, "weight_g")
    ratio = 100.0 / weight_g
    out: Dict[str, float] = {}
    for key, value in nutrients.items():
        if value is None:
            continue
        if key == "gi_value":
            out[key] = float(value)
        else:
            out[key] = float(value) * ratio
    return out


# ============================================================
# 三、每日参考摄入量 / 达标判定
# ============================================================

def daily_limits(gender: str, age: int) -> Dict[str, dict]:
    """每日参考摄入量（参照《中国居民膳食指南2022》），仅支持 18 岁及以上成人

    返回 {字段: {"min": ..., "max": ...}}：
    - calorie   : 各体力活动水平下的能量需要范围（千卡）
    - protein   : RNI 推荐摄入量（男 65g / 女 55g，18-49 岁轻体力）
    - carb/fat  : 按供能比 50-65% / 20-30% 由轻体力基准能量折算
    - diet_fiber: 25g（指南建议 25-30g，取下限）
    - calcium   : 18-49 岁 800mg，50 岁及以上 1000mg
    - folic_acid: 400µg DFE
    - dha       : 200mg（中国营养学会建议成人每日 200mg）
    """
    g = _normalize_gender(gender)
    if age <= 0:
        raise ValueError("age 必须为正数")
    if age < 18:
        raise ValueError("daily_limits 仅支持 18 岁及以上成人")

    if age <= 49:
        energy_base = 2250 if g == "male" else 1800   # 轻体力活动 EER
        energy_range = (1800, 3000) if g == "male" else (1500, 2400)
        calcium = 800
    elif age <= 64:
        energy_base = 2100 if g == "male" else 1750
        energy_range = (1700, 2800) if g == "male" else (1400, 2200)
        calcium = 1000
    else:
        energy_base = 2050 if g == "male" else 1700
        energy_range = (1600, 2400) if g == "male" else (1300, 2000)
        calcium = 1000

    # 供能比折算：碳水 50-65%（4kcal/g），脂肪 20-30%（9kcal/g）
    carb_lo = round(energy_base * 0.50 / 4)
    carb_hi = round(energy_base * 0.65 / 4)
    fat_lo = round(energy_base * 0.20 / 9)
    fat_hi = round(energy_base * 0.30 / 9)

    return {
        "calorie": {"min": energy_range[0], "max": energy_range[1]},
        "protein": {"min": 65 if g == "male" else 55},
        "carb": {"min": carb_lo, "max": carb_hi},
        "fat": {"min": fat_lo, "max": fat_hi},
        "diet_fiber": {"min": 25},
        "calcium": {"min": calcium},
        "folic_acid": {"min": 400},
        "dha": {"min": 200},
    }


def check_intake(nutrients: Dict, limits: Dict[str, dict]) -> Dict:
    """逐项判定摄入是否达标/超标

    返回 {"each": [{name, value, target, status}, ...]}：
    - status: "不足"（低于下限）/ "达标" / "超标"（高于上限）
    - 只判定 limits 中存在的字段（gi_value 等无参考值的字段跳过）
    """
    each = []
    for key, limit in limits.items():
        value = nutrients.get(key)
        if value is None:
            continue
        value = float(value)
        lo = limit.get("min")
        hi = limit.get("max")
        if lo is not None and value < lo:
            status = "不足"
        elif hi is not None and value > hi:
            status = "超标"
        else:
            status = "达标"
        each.append({
            "name": NUTRIENT_NAMES.get(key, key),
            "value": round(value, 2),
            "target": limit,
            "status": status,
        })
    return {"each": each}
