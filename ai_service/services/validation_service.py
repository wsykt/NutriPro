# -*- coding: utf-8 -*-
"""统一校验入口（ValidationService）

目标架构"校验组件统一入口"：
- 对话/结构化输出（qa / diet_plan / food_recommend / exercise）
  委托 ValidatorPipeline（safety → numeric → fact 三组件链）；
- 文稿/科普文章（长文本）独立文稿校验：结构完整性、引用一致性、
  绝对化用语、异常数值。

对话与文稿统一经 validation_service 单例调用，避免散落各处。
"""
import logging
import re
from typing import Any, Dict, List, Optional

from agent.validators.validator import validator_pipeline

logger = logging.getLogger(__name__)

# 绝对化/夸大用语（科普文稿需告警）
_ABSOLUTE_WORDS = [
    "根治", "治愈率100%", "100%治愈", "绝对有效", "包治",
    "永不复发", "毫无副作用", "一定", "最有效", "最好",
    "神药", "特效", "立竿见影",
]

# 异常数值启发式：营养素摄入量超出常识上限（克/毫克场景不同，仅兜底告警）
_ABSURD_NUM_RE = re.compile(r"(\d{4,})\s*(g|kg|mg|ug|千卡|kcal|卡)", re.IGNORECASE)

_PMID_RE = re.compile(r"PMID[:：]?\s*(\d{5,9})")


class ValidationService:
    """统一校验入口（对话 + 文稿）"""

    # ---------- 对话 / 结构化输出校验 ----------
    def validate_response(self, func_type: str, result: Any,
                          target_crowd: str = "",
                          chronic_diseases: Optional[List[str]] = None,
                          kb_context: str = "") -> Dict[str, Any]:
        """委托 ValidatorPipeline 执行三组件校验链（对话/结构化输出）"""
        return validator_pipeline.validate(
            func_type=func_type,
            result=result,
            target_crowd=target_crowd,
            chronic_diseases=chronic_diseases or [],
            kb_context=kb_context,
        )

    # ---------- 文稿 / 科普文章校验 ----------
    def validate_article(self, article: str,
                         sources: Optional[List[Dict[str, Any]]] = None,
                         expected_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """科普文稿校验。

        Args:
            article: 文章正文（Markdown）
            sources: 引用来源卡片列表（含 card_id/PMID），用于引用一致性核对
            expected_sections: 期望章节关键词（默认空，不强制章节骨架）

        Returns:
            {
              "passed": bool, "level": "ok"|"warn",
              "stats": {"char_len": n, "words_zh": n, "section_h2": n, "section_h3": n},
              "structure": {...}, "citations": {...}, "absolute_words": [...],
              "absurd_numbers": [...], "issues": [...],
            }
        """
        issues: List[Dict[str, Any]] = []
        text = article or ""

        # 1) 结构完整性
        h2 = re.findall(r"^##\s+(.+)$", text, re.M)
        h3 = re.findall(r"^###\s+(.+)$", text, re.M)
        char_len = len(text.replace("\n", "").replace(" ", ""))
        words_zh = len(re.findall(r"[\u4e00-\u9fff]", text))
        structure = {
            "has_h2": bool(h2),
            "h2_count": len(h2),
            "h3_count": len(h3),
            "sections_h2": h2[:20],
        }
        if not h2 and expected_sections:
            issues.append({"severity": "warn", "section": "structure",
                           "message": "文稿缺少二级章节（##）结构"})
        elif not h2:
            issues.append({"severity": "info", "section": "structure",
                           "message": "文稿未使用 ## 章节结构（可能是单段回答）"})
        if expected_sections:
            missing = [s for s in expected_sections if s not in text]
            if missing:
                issues.append({"severity": "warn", "section": "structure",
                               "message": f"缺失期望章节内容: {', '.join(missing[:5])}"})

        # 2) 引用一致性（正文 PMID 必须能在 sources 中找到）
        cited_pmids = sorted(set(_PMID_RE.findall(text)))
        known_pmids = set()
        for s in sources or []:
            cid = str(s.get("card_id", ""))
            m = re.search(r"(\d{5,9})", cid)
            if m:
                known_pmids.add(m.group(1))
            if s.get("pmid"):
                known_pmids.add(str(s["pmid"]))
        unknown_cited = [p for p in cited_pmids if p not in known_pmids]
        citations = {
            "cited_pmids": cited_pmids,
            "known_sources": sorted(known_pmids),
            "unknown_cited": unknown_cited,
        }
        if unknown_cited:
            issues.append({"severity": "warn", "section": "citations",
                           "message": f"正文引用了未在来源中的 PMID: {', '.join(unknown_cited[:5])}"})

        # 3) 绝对化用语
        absolute_hits = [w for w in _ABSOLUTE_WORDS if w in text]
        if absolute_hits:
            issues.append({"severity": "warn", "section": "language",
                           "message": f"检测到绝对化/夸大用语: {', '.join(absolute_hits)}"})

        # 4) 异常数值
        absurd_numbers = [m.group(0) for m in _ABSURD_NUM_RE.finditer(text)]
        if absurd_numbers:
            issues.append({"severity": "warn", "section": "numeric",
                           "message": f"检测到疑似异常数值: {', '.join(absurd_numbers[:5])}"})

        level = "warn" if any(i["severity"] == "warn" for i in issues) else "ok"
        return {
            "passed": level == "ok",
            "level": level,
            "stats": {"char_len": char_len, "words_zh": words_zh,
                      "section_h2": len(h2), "section_h3": len(h3)},
            "structure": structure,
            "citations": citations,
            "absolute_words": absolute_hits,
            "absurd_numbers": absurd_numbers,
            "issues": issues,
        }

    # ---------- 汇总便捷方法 ----------
    def validate(self, kind: str, result: Any, **kwargs) -> Dict[str, Any]:
        """按类型统一入口：kind = response | article"""
        if kind == "article":
            return self.validate_article(result, kwargs.get("sources"))
        return self.validate_response(kwargs.get("func_type", "qa"), result,
                                      target_crowd=kwargs.get("target_crowd", ""),
                                      chronic_diseases=kwargs.get("chronic_diseases"),
                                      kb_context=kwargs.get("kb_context", ""))


# 单例
validation_service = ValidationService()
