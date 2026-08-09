# -*- coding: utf-8 -*-
"""校验组件统一入口（ValidatorPipeline）

将事实校验、数值检查、安全风险拦截三个独立组件串成一条校验流水线，
供 orchestrator.process 在返回结果前统一调用。

流程：safety(拦截) → numeric(数值) → fact(事实) → 汇总
"""
import logging
from typing import Any, Dict, List, Optional

from agent.validators.fact_checker import fact_checker
from agent.validators.numeric_checker import numeric_checker
from agent.validators.safety_interceptor import safety_interceptor

logger = logging.getLogger(__name__)


class ValidatorPipeline:
    """三组件校验流水线"""

    def __init__(self, fact=None, numeric=None, safety=None, enabled: bool = True):
        self.fact = fact or fact_checker
        self.numeric = numeric or numeric_checker
        self.safety = safety or safety_interceptor
        self.enabled = enabled

    def validate(self, func_type: str, result: Any,
                 target_crowd: str = "", chronic_diseases: List[str] = None,
                 kb_context: str = "") -> Dict[str, Any]:
        """执行完整校验链。

        Args:
            func_type: qa / diet_plan / food_recommend / exercise
            result: AI 生成结果（str 或 dict）
            target_crowd: 目标人群（如 孕妇/糖尿病患者/老年人）
            chronic_diseases: 慢性病列表
            kb_context: 知识库召回内容（事实校验用）

        Returns:
            {
              "passed": bool,              # 全部通过才 True
              "level": "ok"|"warn"|"block"|"error",
              "safety": {...},             # 安全拦截结果
              "numeric": {...},            # 数值检查结果
              "fact": {...},               # 事实校验结果
              "issues": [...],             # 汇总（严重问题在前）
              "blocked": bool,             # 是否需阻断
            }
        """
        if not self.enabled:
            return {"passed": True, "level": "ok", "blocked": False,
                    "safety": {"level": "ok"}, "numeric": {"passed": True},
                    "fact": {"passed": True}, "issues": []}

        # 1) 安全风险拦截（最高优先级）
        safety_result = self.safety.check_json(result, target_crowd, chronic_diseases)

        # 2) 数值检查（结构化功能）
        numeric_result = {"passed": True, "issues": [], "severity": "low"}
        if func_type in ("diet_plan", "food_recommend", "exercise") and isinstance(result, dict):
            numeric_result = self.numeric.check_json(result, func_type)
            # 补充宏量营养素配比（饮食方案）
            nb = result.get("nutrition_breakdown") if isinstance(result, dict) else None
            if isinstance(nb, dict) and func_type == "diet_plan":
                balance = self.numeric.check_macro_balance(
                    nb.get("protein", 0) or 0,
                    nb.get("carbohydrate", 0) or 0,
                    nb.get("fat", 0) or 0,
                )
                numeric_result["macro_balance"] = balance
        elif func_type == "qa" and isinstance(result, str):
            numeric_result = self.numeric.check_text(result, func_type)

        # 3) 事实校验
        fact_result = self.fact.check_json(result, kb_context, target_crowd) \
            if isinstance(result, dict) else self.fact.check(result or "", kb_context, target_crowd)

        # 4) 汇总
        issues = []
        for section in (safety_result, numeric_result, fact_result):
            for i in (section.get("issues") or []):
                i["section"] = {"safety": "safety", "numeric": "numeric", "fact": "fact"}[
                    "safety" if section is safety_result else
                    ("numeric" if section is numeric_result else "fact")]
                issues.append(i)

        blocked = safety_result.get("level") == "block"
        # 数值 high 或事实 high 仅告警，不阻断（安全为最高优先级）
        # 仅 info 级问题（如免责声明缺失）不升级告警级别，仅记录
        non_info = [i for i in issues if i.get("severity") != "info"]
        if blocked:
            level = "block"
        elif safety_result.get("level") == "warn" or \
                numeric_result.get("severity") == "high" or fact_result.get("severity") == "high":
            level = "warn"
        elif non_info:
            level = "warn"
        else:
            level = "ok"

        return {
            "passed": not blocked,
            "level": level,
            "safety": safety_result,
            "numeric": numeric_result,
            "fact": fact_result,
            "issues": sorted(issues, key=lambda x: {"block": 0, "warn": 1, "medium": 1, "high": 1, "info": 2}.get(x.get("severity"), 2)),
            "blocked": blocked,
        }


# 单例
validator_pipeline = ValidatorPipeline()
