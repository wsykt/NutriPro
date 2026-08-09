# -*- coding: utf-8 -*-
"""事实校验组件（FactChecker）

职责：对 AI 生成的回答/方案做事实性检查，识别：
  1. 无知识库依据的结论性断言（AI 幻觉高风险点）
  2. 与权威指南/知识库不一致的表述
  3. 绝对化、夸大性用语（如"保证""必定""100%"）

设计原则：
- 独立组件，不依赖具体 Agent，可被 orchestrator / mode_router 复用
- 只报告问题，不修改内容（下游决定是否拦截或降级）
- 支持规则引擎（本地，零成本）优先，LLM 校验为可选项
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# 绝对化/夸大用语（AI 幻觉高发点）
ABSOLUTE_PHRASES = [
    "100%", "百分之百", "保证", "必定", "一定有效", "完全治愈",
    "根治", "包治", "神奇疗效", "立刻见效", "立竿见影", "绝对安全",
    "无一例外", "所有患者", "任何情况",
]

# 需知识库/权威依据支撑的结论性关键词
CLAIM_KEYWORDS = [
    "研究表明", "研究显示", "据统计", "专家指出", "临床上",
    "推荐摄入", "可降低", "可预防", "有效治疗", "显著提高",
    "摄入量", "指南建议", "WHO建议",
]


class FactChecker:
    """事实校验器：规则引擎 + 可选 LLM 校验"""

    def __init__(self, retriever=None, llm=None):
        self.retriever = retriever
        self.llm = llm
        self.absolute_phrases = ABSOLUTE_PHRASES
        self.claim_keywords = CLAIM_KEYWORDS

    def check(self, text: str, kb_context: str = "",
              target_crowd: str = "") -> Dict[str, Any]:
        """执行事实校验。

        Args:
            text: 待校验的 AI 生成文本（str）
            kb_context: 知识库召回内容（用于交叉核对）
            target_crowd: 目标人群（用于人群相关性提示）

        Returns:
            {"passed": bool, "issues": [...], "severity": "low"|"medium"|"high", "stats": {...}}
        """
        if not text or not isinstance(text, str):
            return {"passed": True, "issues": [], "severity": "low",
                    "stats": {"chars": 0}}

        issues = []
        text_lower = text.lower()

        # 1) 绝对化用语检测
        for phrase in self.absolute_phrases:
            if phrase in text:
                issues.append({
                    "type": "absolute_claim",
                    "severity": "medium",
                    "message": f"检测到绝对化/夸大表述：「{phrase}」，可能缺乏科学依据，建议弱化措辞",
                    "matched": phrase,
                })

        # 2) 结论性断言但缺少知识库依据（仅当有 kb_context 时才能交叉核对）
        if kb_context:
            for kw in self.claim_keywords:
                if kw in text:
                    # 结论性关键词出现，检查知识库是否有对应支撑
                    # 简化核对：知识库包含"结论关键字"或高相关文本即视为有依据
                    kb_compact = kb_context.replace(" ", "").replace("\n", "")
                    if kw not in kb_compact and not self._kb_supports(text, kb_context, kw):
                        issues.append({
                            "type": "unsupported_claim",
                            "severity": "low",
                            "message": f"出现结论性表述「{kw}」，但当前知识库未直接支撑，建议标注来源或核实",
                            "matched": kw,
                        })

        # 3) 生成统计数据
        stats = {
            "chars": len(text),
            "absolute_claims": sum(1 for i in issues if i["type"] == "absolute_claim"),
            "unsupported_claims": sum(1 for i in issues if i["type"] == "unsupported_claim"),
        }

        # 4) 严重度判定
        severity = "low"
        if any(i["severity"] == "high" for i in issues):
            severity = "high"
        elif any(i["severity"] == "medium" for i in issues):
            severity = "medium"

        return {
            "passed": severity != "high",  # 仅 high 级拦截
            "issues": issues,
            "severity": severity,
            "stats": stats,
        }

    def _kb_supports(self, text: str, kb_context: str, keyword: str) -> bool:
        """检查知识库文本是否间接支撑该结论（基于关键词共现的启发式）"""
        # 取结论性语句（关键词所在句）
        sentences = re.split(r"[。；\n]", text)
        claim_sent = next((s for s in sentences if keyword in s), "")
        if not claim_sent:
            return True  # 无明确结论句，不误报
        # 提取关键词附近的数字/量词
        nums = re.findall(r"\d+(?:\.\d+)?", claim_sent)
        kb_nums = set(re.findall(r"\d+(?:\.\d+)?", kb_context))
        # 若结论句含数字且知识库不含该数字，可能为幻觉
        if nums and not (set(nums) & kb_nums):
            return False
        return True

    def check_json(self, result: Dict[str, Any], kb_context: str = "",
                   target_crowd: str = "") -> Dict[str, Any]:
        """校验 JSON 结构化结果（先序列化文本再走规则引擎）"""
        if not isinstance(result, dict):
            return self.check(str(result), kb_context, target_crowd)
        text = json.dumps(result, ensure_ascii=False)
        base = self.check(text, kb_context, target_crowd)

        # JSON 特有检查：字段完整性由各校验器负责，这里只做文本级
        return base

    def check_with_llm(self, text: str, kb_context: str = "") -> Dict[str, Any]:
        """可选的 LLM 深度事实校验（成本高，默认不使用；供离线精检场景）"""
        if not self.llm:
            return {"passed": True, "issues": [], "severity": "low",
                    "note": "无LLM，跳过深度校验"}
        prompt = (
            "你是医学事实核查员。请检查以下健康回答是否存在事实错误、夸大或误导。\n"
            "只回答JSON：{\"issues\": [{\"type\":\"...\", \"severity\":\"low|medium|high\", "
            "\"message\":\"...\"}], \"passed\": true/false}\n\n"
            f"【知识库参考】{kb_context[:600]}\n\n【待核查回答】{text[:1000]}\n"
        )
        try:
            original_mode = getattr(self.llm, "_mode", "cloud")
            self.llm._mode = "local"
            result = self.llm.chat_json(prompt, temperature=0.1)
            self.llm._mode = original_mode
            if isinstance(result, dict):
                issues = result.get("issues", []) or []
                passed = result.get("passed", True)
                severity = "high" if any(i.get("severity") == "high" for i in issues) else \
                           ("medium" if any(i.get("severity") == "medium" for i in issues) else "low")
                return {"passed": passed, "issues": issues, "severity": severity,
                        "stats": {"chars": len(text), "llm_checked": True}}
        except Exception as e:
            logger.debug(f"[FactChecker LLM校验失败] {e}")
        return {"passed": True, "issues": [], "severity": "low",
                "note": "LLM校验失败，默认通过"}


# 单例
fact_checker = FactChecker()
