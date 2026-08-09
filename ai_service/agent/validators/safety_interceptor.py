# -*- coding: utf-8 -*-
"""安全风险拦截组件（SafetyInterceptor）

职责：对 AI 生成的健康方案做安全风险识别与拦截：
  1. 特殊人群禁忌（孕妇/糖尿病/高血压/老年人/青少年）的危险建议
  2. 高风险动作/饮食（极端节食、断食过度、危险补剂、超高强度运动）
  3. 医疗行为越界（诊断、开药、停药建议等应由执业医师处理的内容）
  4. 免责声明缺失提醒

设计原则：
- 独立组件，不依赖具体 Agent
- 拦截策略分级：BLOCK（阻断返回）/ WARN（附加警示）/ INFO（仅记录）
- 高风险场景优先阻断，安全为先
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SafetyLevel:
    """安全级别"""
    BLOCK = "block"     # 需阻断/大幅改写（返回安全提示）
    WARN = "warn"       # 附加安全警示，不阻断
    INFO = "info"       # 仅记录提示


# 高危动作/表述（命中即 BLOCK）
HIGH_RISK_PATTERNS = [
    # 极端饮食
    r"断食\s*\d+\s*(天|日)",            # 长时间断食
    r"(禁食|绝食)\s*(\d+)?\s*(天|日)",  # 禁食
    r"只(喝水|喝果汁|喝水)",            # 单一液体饮食
    r"极端(节食|低碳|低脂)",            # 极端饮食法
    r"一周(减|瘦)\s*\d+\s*公斤",        # 不健康减重速度（>1kg/周）
    # 危险补剂/药物
    r"(滥用|过量服用)\s*(药物|补剂|维生素)",
    r"(减肥药|泻药|利尿剂)",            # 药理性减肥
    r"(类固醇|生长激素)",               # 激素滥用
    # 危险运动
    r"(空腹|饿着)?\s*(高强度|剧烈)?\s*运动.*?(诱发|导致|引发)",
    # 医疗越界
    r"(停用|停药|减药|换药)\s*(降压药|降糖药|胰岛素|抗凝药|他汀|激素)",
    r"用\s*[^。；]{0,10}\s*治疗\s*[^。；]{0,10}\s*(癌症|肿瘤|糖尿病|高血压)",
]

# 特殊人群禁忌（人群 → 风险表述正则）
CROWD_BANS = {
    "孕妇": [
        r"(剧烈运动|高强度训练|冲刺跑|马拉松)",
        r"(节食|断食|减肥|严格控制热量)",
        r"(酒精|饮酒|醉酒)",
        r"(未经医生评估)?\s*(补充|服用)\s*(维生素A|视黄醇|高剂量.*维生素)",
    ],
    "糖尿病患者": [
        r"(空腹.{0,8}(剧烈运动|高强度|间歇训练))",
        r"(完全不吃主食|极低碳水|长期生酮)",
        r"(自行调整胰岛素|自行增减药量|擅自停药)",
    ],
    "高血压患者": [
        r"(突然停止服药|停药|减药)",
        r"(极限举重|憋气发力|大重量训练)",
        r"(高盐饮食|大量腌制品|每日食盐超过6克)" if False else r"(高盐饮食|大量腌制品)",
    ],
    "老年人": [
        r"(极限负重|大重量深蹲|剧烈跑跳)",
        r"(长时间单脚站立|高难度平衡训练)",
        r"(快速起身|突然剧烈运动)",
    ],
    "青少年": [
        r"(高蛋白补剂|蛋白粉替代正餐|增肌粉)",
        r"(过度节食减肥|极端控制体重)",
        r"(高强度力量训练+超量训练)",
    ],
    "心血管患者": [
        r"(极限高强度间歇训练|HIIT)",
        r"(憋气发力|瓦氏动作|大重量举重)",
    ],
}

# 需附带免责声明的关键词（缺失时 INFO）
DISCLAIMER_TRIGGERS = ["建议", "推荐", "应该", "需要", "一定要"]
STANDARD_DISCLAIMER = "温馨提示：本内容仅供膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。"

# 医疗诊断/处方边界词（命中即 WARN）
MEDICAL_BOUNDARY = [
    "诊断", "确诊", "处方", "开药", "替代药物", "替代治疗",
]


class SafetyInterceptor:
    """安全风险拦截器"""

    def __init__(self):
        self.high_risk = HIGH_RISK_PATTERNS
        self.crowd_bans = CROWD_BANS
        self.medical_boundary = MEDICAL_BOUNDARY

    def check(self, text: str, target_crowd: str = "",
              chronic_diseases: List[str] = None,
              require_disclaimer: bool = True) -> Dict[str, Any]:
        """对文本做安全风险评估。

        Returns:
            {
              "level": "block"|"warn"|"info"|"ok",
              "passed": bool,          # block 时 False
              "issues": [{"type","severity","message","matched"}],
              "needs_disclaimer": bool
            }
        """
        if not text or not isinstance(text, str):
            return {"level": "ok", "passed": True, "issues": [], "needs_disclaimer": False}

        issues = []
        level = SafetyLevel.INFO

        # 1) 高危模式（BLOCK）
        for pattern in self.high_risk:
            m = re.search(pattern, text)
            if m:
                issues.append({
                    "type": "high_risk",
                    "severity": "block",
                    "message": f"检测到高风险内容：「{m.group(0)}」，已拦截，建议改写为安全表述",
                    "matched": m.group(0),
                })
                level = SafetyLevel.BLOCK

        # 2) 人群禁忌（BLOCK/WARN）
        crowd_key = target_crowd or ""
        # 合并慢病映射：慢性病列表可能包含"高血压""糖尿病"等
        if chronic_diseases:
            for cd in chronic_diseases:
                if "高血压" in cd:
                    crowd_key = crowd_key or "高血压患者"
                elif "糖尿" in cd:
                    crowd_key = crowd_key or "糖尿病患者"
                elif "心血管" in cd or "心脏" in cd:
                    crowd_key = crowd_key or "心血管患者"

        bans = self.crowd_bans.get(crowd_key, [])
        # 高危人群：孕妇 / 糖尿病患者 命中任何禁忌规则直接 BLOCK（安全优先）
        sensitive_crowd = crowd_key in ("孕妇", "糖尿病患者")
        for pattern in bans:
            m = re.search(pattern, text)
            if m:
                sev = "block" if (sensitive_crowd or
                                  "停" in pattern or "断食" in pattern or "生酮" in pattern) else "warn"
                issues.append({
                    "type": "crowd_ban",
                    "severity": sev,
                    "message": f"{crowd_key}人群风险建议：「{m.group(0)}」不适合该人群，需调整",
                    "matched": m.group(0),
                })
                if sev == "block":
                    level = SafetyLevel.BLOCK
                elif level != SafetyLevel.BLOCK:
                    level = SafetyLevel.WARN

        # 3) 医疗边界（WARN）
        for kw in self.medical_boundary:
            if kw in text:
                issues.append({
                    "type": "medical_boundary",
                    "severity": "warn",
                    "message": f"涉及医疗行为表述「{kw}」，应提示用户遵医嘱，AI不可替代执业医师",
                    "matched": kw,
                })
                if level != SafetyLevel.BLOCK:
                    level = SafetyLevel.WARN

        # 4) 免责声明缺失（INFO）
        needs_disclaimer = False
        if require_disclaimer and STANDARD_DISCLAIMER[:10] not in text:
            if any(t in text for t in DISCLAIMER_TRIGGERS):
                needs_disclaimer = True
                issues.append({
                    "type": "missing_disclaimer",
                    "severity": "info",
                    "message": "回答含建议性内容但缺少免责声明，建议补充",
                    "matched": "",
                })
                if level not in (SafetyLevel.BLOCK, SafetyLevel.WARN):
                    level = SafetyLevel.INFO

        passed = level != SafetyLevel.BLOCK
        return {
            "level": level,
            "passed": passed,
            "issues": issues,
            "needs_disclaimer": needs_disclaimer,
        }

    def check_json(self, result: Dict[str, Any], target_crowd: str = "",
                   chronic_diseases: List[str] = None) -> Dict[str, Any]:
        """校验 JSON 结构化结果（序列化后走文本规则）"""
        if isinstance(result, str):
            return self.check(result, target_crowd, chronic_diseases)
        if not isinstance(result, dict):
            return {"level": "ok", "passed": True, "issues": [], "needs_disclaimer": False}
        # 抽取 tips / precautions / description 等用户可见文本做安全扫描
        text_parts = []
        for key in ("tips", "precautions", "progression_plan", "warm_up", "cool_down"):
            v = result.get(key)
            if isinstance(v, list):
                text_parts.extend(str(x) for x in v)
            elif isinstance(v, str):
                text_parts.append(v)
        if "daily_plan" in result:
            text_parts.append(json.dumps(result["daily_plan"], ensure_ascii=False))
        full_text = "\n".join(text_parts)
        return self.check(full_text, target_crowd, chronic_diseases)

    def build_safe_response(self, func_type: str, original: Any, issues: List[dict]) -> Any:
        """构造被拦截后的安全响应（BLOCK 时使用）"""
        if func_type == "qa":
            return (
                "非常抱歉，检测到本次回答中存在可能对您不安全的建议内容，已为您拦截。"
                "如您有具体健康问题，建议咨询执业医师或营养师获取个性化指导。"
                f"\n\n{STANDARD_DISCLAIMER}"
            )
        # 结构化功能：返回空结果 + 提示
        base = {} if isinstance(original, dict) else []
        return {
            "blocked": True,
            "reason": "检测到高风险或不适合当前人群的内容",
            "detail": [i["message"] for i in issues if i["severity"] in ("block", "warn")][:3],
            "data": base,
        }


# 单例
safety_interceptor = SafetyInterceptor()
