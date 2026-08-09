# -*- coding: utf-8 -*-
"""文献智能合并（literature_merge.py）

目标架构"文献合并"：
- 输入：同主题、结论一致的多篇文献卡片（通常由 kb_cluster 聚类后获得）；
- 输出：约 500 字的复合权威卡片（多篇互证 + 量化数据 + 全部来源可溯源）；
- 生成策略：LLM 融合（云端/本地）为主，LLM 不可用时本地拼接降级。

复用约束：合并仅针对"结论一致"的文献；结论相悖的应走 dispute_detect.py。
"""
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger(__name__)

_MERGE_SYSTEM = (
    "你是营养学科普知识库编辑。将多篇结论一致的文献摘要融合成一张复合知识卡片。\n"
    "要求：\n"
    "1. 输出 JSON：{{\"merged_content\": 四段式正文, \"core_conclusion\": \"一句话核心结论\"}}\n"
    "2. 四段式正文必须包含【核心循证结论】【量化临床数据】【适用人群】【局限性/学术争议】四个小节；\n"
    "3. 全文中文，约 {target_words} 字以内；结论互证、去除重复表述；\n"
    "4. 量化数据保留具体数值；局限性合并各篇共性；不添加原文献没有的信息。"
)


def _extract_pmid(card: Dict[str, Any]) -> str:
    cid = str(card.get("card_id", ""))
    m = re.search(r"(\d{5,9})", cid)
    return m.group(1) if m else cid


class LiteratureMerger:
    """文献智能合并器"""

    def __init__(self, llm: Optional[Any] = None, target_words: int = None,
                 enabled: bool = None):
        self.llm = llm
        self.target_words = target_words if target_words is not None else settings.KB_MERGE_TARGET_WORDS
        self.enabled = enabled if enabled is not None else settings.KB_MERGE_ENABLED

    # ---------- LLM 融合（主路径） ----------
    def _merge_via_llm(self, cards: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        if self.llm is None:
            try:
                from llm.router import llm as _default_llm
                self.llm = _default_llm
            except Exception as e:
                logger.warning(f"LLM 不可用，使用本地合并: {e}")
                return None
        try:
            docs = "\n\n".join(
                f"[文献{i + 1}] {card.get('title', '')}\n{card.get('purified_content') or card.get('content') or ''}"
                for i, card in enumerate(cards))
            raw = self.llm.chat_json(
                [{"role": "system",
                  "content": _MERGE_SYSTEM.format(target_words=self.target_words)},
                 {"role": "user", "content": docs}],
                temperature=0.3,
            )
            content = raw.get("merged_content", "")
            if not content or len(content.strip()) < 30:
                logger.warning("LLM 融合结果为空/过短，回退本地合并")
                return None
            return {"merged_content": content,
                    "core_conclusion": raw.get("core_conclusion", "")}
        except Exception as e:
            logger.warning(f"LLM 融合失败，回退本地合并: {e}")
            return None

    # ---------- 本地拼接降级 ----------
    @staticmethod
    def _merge_locally(cards: List[Dict[str, Any]], target_words: int) -> Dict[str, str]:
        conclusions, data, crowd, limits = [], [], [], []
        for card in cards:
            content = card.get("purified_content") or card.get("content") or ""
            for line in content.split("\n"):
                if "【核心循证结论】" in line:
                    conclusions.append(line.split("】", 1)[-1].strip())
                elif "【量化临床数据】" in line:
                    data.append(line.split("】", 1)[-1].strip())
                elif "【适用人群】" in line:
                    crowd.append(line.split("】", 1)[-1].strip())
                elif "【局限性/学术争议】" in line:
                    limits.append(line.split("】", 1)[-1].strip())
        dedup = lambda arr: list(dict.fromkeys(x for x in arr if x and x != "暂无"))
        conclusions, data = dedup(conclusions), dedup(data)
        crowd, limits = dedup(crowd), dedup(limits)

        def clip(sec: str) -> str:
            return sec[:target_words] if len(sec) > target_words else sec

        merged = (
            f"【核心循证结论】{clip('；'.join(conclusions) or '多篇文献结论一致。')}\n"
            f"【量化临床数据】{clip('；'.join(data) or '暂无')}\n"
            f"【适用人群】{clip('；'.join(crowd) or '普通人群')}\n"
            f"【局限性/学术争议】{clip('；'.join(limits) or '暂无')}"
        )
        return {"merged_content": merged, "core_conclusion": conclusions[0] if conclusions else ""}

    # ---------- 主流程 ----------
    def merge(self, cards: List[Dict[str, Any]], topic: str = "") -> Dict[str, Any]:
        """合并结论一致的文献卡片为复合权威卡片。

        Returns:
            {
              "merged": bool, "source_count": n,
              "merged_card": {"card_id", "title", "topic", "purified_content",
                              "core_conclusion", "sources": [{card_id, pmid, title}]},
              "method": "llm" | "local" | "skipped",
            }
        """
        if not self.enabled or len(cards) < 2:
            return {"merged": False, "source_count": len(cards),
                    "method": "skipped", "merged_card": None}

        merged = self._merge_via_llm(cards) if settings.LLM_MODE in ("cloud", "local") else None
        method = "llm"
        if merged is None:
            merged = self._merge_locally(cards, self.target_words)
            method = "local"

        sources = [{"card_id": c.get("card_id", ""), "pmid": _extract_pmid(c),
                    "title": c.get("title", "")} for c in cards]
        merged_card = {
            "card_id": f"COMPOSITE_{topic or 'merged'}_{int(time.time())}",
            "title": f"[复合] {topic or cards[0].get('topic', '')}",
            "topic": topic or cards[0].get("topic", ""),
            "purified_content": merged["merged_content"],
            "core_conclusion": merged["core_conclusion"],
            "sources": sources,
            "source_count": len(cards),
            "merge_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return {"merged": True, "source_count": len(cards),
                "method": method, "merged_card": merged_card}


# 单例
literature_merger = LiteratureMerger()
