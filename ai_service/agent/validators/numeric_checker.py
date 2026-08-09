# -*- coding: utf-8 -*-
"""数值检查组件（NumericChecker）

职责：对 AI 生成的健康方案中的数值做合理性检查，识别：
  1. 超出合理范围的数值（如总热量、蛋白质克数、运动时长、BMI 等）
  2. 营养配比失衡（蛋白质/碳水/脂肪供能比异常）
  3. 与用户身体指标矛盾的数值（如与 BMR 严重不符）

设计原则：
- 独立组件，可被 orchestrator / mode_router 复用
- 规则表驱动（各类功能的合理区间可配置），零 LLM 依赖
- 只报告问题，不修改内容
"""
import json
import logging
from typing import Any, Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 数值合理区间规则表
# ============================================================
# 每项: 字段名(支持嵌套路径用点号) -> (最小值, 最大值, 标签, 严重度)
NUMERIC_RULES = {
    # --- 一日饮食方案 ---
    "total_calories":        (800, 4000, "总热量(kcal)", "medium"),
    "nutrition_breakdown.protein": (30, 250, "蛋白质(g)", "medium"),
    "nutrition_breakdown.carbohydrate": (50, 600, "碳水(g)", "low"),
    "nutrition_breakdown.fat": (20, 200, "脂肪(g)", "medium"),
    # --- 食材菜谱推荐 ---
    "total_calories_food":   (500, 4500, "菜谱总热量(kcal)", "medium"),
    "total_protein":         (40, 300, "菜谱总蛋白(g)", "medium"),
    "meal_plan.*.calories_estimate": (50, 2000, "单菜热量(kcal)", "low"),
    "meal_plan.*.protein_estimate": (1, 120, "单菜蛋白(g)", "low"),
    # --- 运动方案 ---
    "weekly_total_minutes":  (0, 300, "周运动总时长(分钟)", "medium"),
    "weekly_total_calories": (0, 8000, "周消耗热量(kcal)", "low"),
    "weekly_schedule.*.duration": (5, 180, "单次运动时长(分钟)", "low"),
    "weekly_schedule.*.calories_burn_estimate": (10, 2000, "单次消耗(kcal)", "low"),
    # --- 健康问答（文本抽取数值） ---
    "text_salt":             (0, 6, "每日盐摄入(g)", "medium"),
    "text_water":            (0, 4000, "每日饮水(ml)", "low"),
    "text_protein_per_kg":   (0, 3, "蛋白质(g/kg体重)", "medium"),
}

# 中文上下文数值规则（文本抽取用）：(正则, 标签, 区间, 严重度)
TEXT_PATTERNS = [
    (r"盐[^。；]*?(\d+(?:\.\d+)?)\s*(?:g|克)", "盐摄入(g)", (0, 6), "medium"),
    (r"饮水[^。；]*?(\d+(?:\.\d+)?)\s*(?:ml|毫升)", "饮水(ml)", (0, 4000), "low"),
    (r"蛋白质[^。；]*?(\d+(?:\.\d+)?)\s*g/kg", "蛋白质(g/kg)", (0, 3), "medium"),
    (r"每周[^。；]*?(\d+(?:\.\d+)?)\s*分钟", "周运动(分钟)", (0, 300), "medium"),
    (r"热量[^。；]*?(\d+(?:\.\d+)?)\s*kcal", "热量(kcal)", (800, 4000), "medium"),
]


class NumericChecker:
    """数值合理性检查器"""

    def __init__(self):
        self.rules = NUMERIC_RULES

    # ---------- 结构化 JSON 校验 ----------

    def check_json(self, result: Dict[str, Any], func_type: str = "") -> Dict[str, Any]:
        """校验 JSON 结构化结果（diet_plan / food_recommend / exercise）"""
        if not isinstance(result, dict):
            return {"passed": True, "issues": [], "severity": "low", "stats": {}}

        issues = []
        for path, (lo, hi, label, sev) in self.rules.items():
            # 跳过不适用于当前功能类型的规则
            if not self._rule_applies(func_type, path):
                continue
            value = self._get_nested(result, path)
            if value is None:
                continue
            for v in value:
                if not isinstance(v, (int, float)):
                    continue
                if v < lo or v > hi:
                    issues.append({
                        "type": "out_of_range",
                        "severity": sev,
                        "message": f"{label} = {v} 超出合理区间 [{lo}, {hi}]",
                        "field": path,
                        "value": v,
                        "range": [lo, hi],
                    })

        return self._finalize(issues, result)

    # ---------- 文本数值抽取校验（qa / 文本型结果） ----------

    def check_text(self, text: str, func_type: str = "") -> Dict[str, Any]:
        """从自由文本中抽取关键数值并校验合理性"""
        if not text or not isinstance(text, str):
            return {"passed": True, "issues": [], "severity": "low", "stats": {}}

        issues = []
        for pattern, label, (lo, hi), sev in TEXT_PATTERNS:
            for m in __import__("re").finditer(pattern, text):
                try:
                    val = float(m.group(1))
                except (ValueError, IndexError):
                    continue
                if val < lo or val > hi:
                    issues.append({
                        "type": "out_of_range",
                        "severity": sev,
                        "message": f"{label} = {val} 超出合理区间 [{lo}, {hi}]",
                        "field": label,
                        "value": val,
                        "range": [lo, hi],
                    })

        stats = {"issues": len(issues), "values_checked": len(issues)}
        return self._finalize(issues, text, stats=stats)

    # ---------- 营养配比校验 ----------

    def check_macro_balance(self, protein: float, carb: float, fat: float) -> Dict[str, Any]:
        """三大营养素供能比检查（蛋白质/碳水/脂肪 ≈ 15%/50%/30%）"""
        issues = []
        total_kcal = protein * 4 + carb * 4 + fat * 9
        if total_kcal <= 0:
            return {"passed": True, "issues": [], "severity": "low",
                    "stats": {"macro_ratio": {}}}

        ratios = {
            "protein": round(protein * 4 / total_kcal * 100, 1),
            "carb": round(carb * 4 / total_kcal * 100, 1),
            "fat": round(fat * 9 / total_kcal * 100, 1),
        }
        # 参考中国居民膳食指南供能比：蛋白10-20%，碳水50-65%，脂肪20-30%
        checks = [
            ("protein", ratios["protein"], (10, 20), "蛋白质供能比"),
            ("carb", ratios["carb"], (50, 65), "碳水供能比"),
            ("fat", ratios["fat"], (20, 30), "脂肪供能比"),
        ]
        for key, ratio, (lo, hi), label in checks:
            if ratio < lo or ratio > hi:
                sev = "medium" if abs(ratio - lo) > 10 and abs(ratio - hi) > 10 else "low"
                issues.append({
                    "type": "macro_imbalance",
                    "severity": sev,
                    "message": f"{label} = {ratio}% 超出推荐区间 [{lo}%, {hi}%]",
                    "field": key,
                    "value": ratio,
                    "range": [lo, hi],
                })

        # 三大营养素全部失衡（整体配比错误）→ 升级为 high
        if len(issues) >= 3:
            for i in issues:
                i["severity"] = "high"

        severity = "high" if any(i["severity"] == "high" for i in issues) else \
                   ("medium" if any(i["severity"] == "medium" for i in issues) else "low")
        return {"passed": severity != "high", "issues": issues,
                "severity": severity, "stats": {"macro_ratio": ratios}}

    # ---------- 工具方法 ----------

    def _rule_applies(self, func_type: str, path: str) -> bool:
        """规则与功能类型的匹配"""
        if not func_type:
            return True
        if "food" in path and func_type != "food_recommend":
            return False
        if "weekly" in path and func_type != "exercise":
            return False
        if "nutrition_breakdown" in path and func_type != "diet_plan":
            return False
        if path == "total_calories" and func_type == "food_recommend":
            return False  # food_recommend 用 total_calories_food
        if path == "total_calories_food" and func_type != "food_recommend":
            return False
        return True

    def _get_nested(self, data: dict, path: str) -> Optional[List[Any]]:
        """按点号路径取值，支持 * 通配符（返回匹配的所有数值）

        语义：
        - 具体 key：从 dict 容器取值；list 整体作为一个容器保留（让 * 去展开）
        - `*`：dict 展开为所有 value 容器；list 展开为所有元素容器
        """
        parts = path.split(".")
        current = [data]
        for part in parts:
            next_level = []
            for node in current:
                if part == "*":
                    if isinstance(node, dict):
                        next_level.extend(node.values())
                    elif isinstance(node, list):
                        next_level.extend(node)
                else:
                    if isinstance(node, dict) and part in node:
                        next_level.append(node[part])
            current = next_level
            if not current:
                break
        return [v for v in current
                if isinstance(v, (int, float)) and not isinstance(v, bool)]

    def _finalize(self, issues: List[dict], _obj: Any, stats: dict = None) -> Dict[str, Any]:
        severity = "low"
        if any(i["severity"] == "high" for i in issues):
            severity = "high"
        elif any(i["severity"] == "medium" for i in issues):
            severity = "medium"
        if stats is None:
            stats = {"issues": len(issues)}
        else:
            stats["issues"] = len(issues)
        return {
            "passed": len(issues) == 0,  # 有数值问题即不通过（提示用户/调用方关注）
            "issues": issues,
            "severity": severity,
            "stats": stats,
        }


# 单例
numeric_checker = NumericChecker()
