# -*- coding: utf-8 -*-
"""学术争议识别（dispute_detect.py）

目标架构"学术争议识别"：
- 输入：同主题多篇文献卡片；
- 两两判定结论关系：一致(consistent) / 互补(complementary) / 相悖(conflicting) / 无关(unknown)；
- 输出争议分组（结论相悖的文献归类打标），供综述文章"学术争议"章节注入。
"""
import logging
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger(__name__)

_RELATION_LABELS = ("consistent", "complementary", "conflicting", "unknown")

_DISPUTE_SYSTEM = (
    "你是营养学证据评估助手。判断两篇文献摘要的结论关系。\n"
    "只输出 JSON：{\"relation\": \"consistent|complementary|conflicting|unknown\","
    " \"stance_a\": \"文献A立场\", \"stance_b\": \"文献B立场\"}\n"
    "关系定义：结论方向相同=consistent；结论不冲突但侧重点不同=complementary；"
    "结论方向相反或互相否定=conflicting；信息不足=unknown。"
)

# 本地规则：明显含"争议""尚无定论""不一致"的表述标记为潜在冲突
_CONFLICT_HINTS = ("仍存争议", "尚无定论", "结论不一致", "有争议", "观点分歧", "相互矛盾")
_CONSISTENT_HINTS = ("无争议", "一致认为", "多项研究一致", "共识")


class DisputeDetector:
    """学术争议识别器"""

    def __init__(self, llm: Optional[Any] = None, enabled: bool = None,
                 min_cards: int = None):
        self.llm = llm
        self.enabled = enabled if enabled is not None else settings.KB_DISPUTE_ENABLED
        self.min_cards = min_cards if min_cards is not None else settings.KB_DISPUTE_MIN_CARDS

    # ---------- LLM 两两判定 ----------
    def _llm_relation(self, text_a: str, text_b: str) -> Dict[str, str]:
        if self.llm is None:
            try:
                from llm.router import llm as _default_llm
                self.llm = _default_llm
            except Exception as e:
                logger.warning(f"LLM 不可用，使用本地规则判定: {e}")
                return {}
        try:
            raw = self.llm.chat_json(
                [{"role": "system", "content": _DISPUTE_SYSTEM},
                 {"role": "user",
                  "content": f"文献A:\n{text_a[:400]}\n\n文献B:\n{text_b[:400]}"}],
                temperature=0.0,
            )
            rel = raw.get("relation", "unknown")
            if rel not in _RELATION_LABELS:
                rel = "unknown"
            return {"relation": rel, "stance_a": raw.get("stance_a", ""),
                    "stance_b": raw.get("stance_b", "")}
        except Exception as e:
            logger.warning(f"LLM 争议判定失败: {e}")
            return {}

    # ---------- 本地规则兜底 ----------
    @staticmethod
    def _local_relation(text_a: str, text_b: str) -> str:
        a_conf, b_conf = any(h in text_a for h in _CONFLICT_HINTS), any(h in text_b for h in _CONFLICT_HINTS)
        if a_conf and not any(h in text_b for h in _CONSISTENT_HINTS):
            return "conflicting"
        if b_conf and not any(h in text_a for h in _CONSISTENT_HINTS):
            return "conflicting"
        return "unknown"

    # ---------- 主流程 ----------
    def detect(self, cards: List[Dict[str, Any]], topic: str = "",
               use_llm: bool = True) -> Dict[str, Any]:
        """识别同主题文献中的学术争议。

        Returns:
            {
              "disputes": [{
                 "topic", "confidence": "high|low",
                 "sides": [{"card_ids": [...], "stance": "..."}, ...],
                 "evidence": "争议双方立场摘要",
              }],
              "pairs_evaluated": n, "method": "llm"|"local"|"skipped",
            }
        """
        if not self.enabled or len(cards) < self.min_cards:
            return {"disputes": [], "pairs_evaluated": 0, "method": "skipped"}

        n = len(cards)
        texts = [
            f"{c.get('title', '')}\n{c.get('purified_content') or c.get('content') or ''}"
            for c in cards
        ]
        # 记录每对冲突：{(i, j): (relation_info, method)}
        conflicts: Dict[tuple, Dict[str, str]] = {}
        for i in range(n):
            for j in range(i + 1, n):
                rel_info = {}
                if use_llm:
                    rel_info = self._llm_relation(texts[i], texts[j])
                if not rel_info:
                    rel_info = {"relation": self._local_relation(texts[i], texts[j])}
                if rel_info.get("relation") == "conflicting":
                    conflicts[(i, j)] = rel_info

        # 组装争议分组（按并查集把相互冲突的文献聚成一组）
        if not conflicts:
            return {"disputes": [], "pairs_evaluated": n * (n - 1) // 2,
                    "method": "llm" if use_llm else "local"}

        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for (i, j) in conflicts:
            union(i, j)

        groups: Dict[int, List[int]] = {}
        for idx in range(n):
            groups.setdefault(find(idx), []).append(idx)

        disputes = []
        for root, members in groups.items():
            if len(members) < 2:
                continue
            # 是否组内确实存在 conflict 边
            has_conflict = any(
                (i, j) in conflicts or (j, i) in conflicts
                for i in members for j in members if i != j)
            if not has_conflict:
                continue
            # 参与争议的卡片及其立场（来自冲突记录）
            side_by_card: Dict[int, str] = {}
            for (i, j), info in conflicts.items():
                if i in members and j in members:
                    side_by_card.setdefault(i, info.get("stance_a", ""))
                    side_by_card.setdefault(j, info.get("stance_b", ""))
            involved = [k for k in members if k in side_by_card]
            neutral = [k for k in members if k not in side_by_card]
            sides = []
            if involved:
                stance_text = "；".join(side_by_card[k] for k in involved if side_by_card[k])
                sides.append({"card_ids": [cards[k].get("card_id", f"card_{k}") for k in involved],
                              "stance": stance_text or "观点对立"})
            if neutral:
                sides.append({"card_ids": [cards[k].get("card_id", f"card_{k}") for k in neutral],
                              "stance": "中性/未参与争议"})
            evidence = "；".join(
                f"{cards[i].get('card_id', 'card_' + str(i))}与"
                f"{cards[j].get('card_id', 'card_' + str(j))}结论相悖"
                for (i, j) in conflicts if i in members and j in members)[:300]
            disputes.append({
                "topic": topic or cards[0].get("topic", ""),
                "confidence": "high" if len(involved) >= 2 else "low",
                "sides": sides,
                "evidence": evidence,
            })

        return {"disputes": disputes,
                "pairs_evaluated": n * (n - 1) // 2,
                "method": "llm" if use_llm else "local"}

    # ---------- 综述辅助 ----------
    def has_major_dispute(self, cards: List[Dict[str, Any]], use_llm: bool = True) -> bool:
        """综述生成判断：是否需注入"学术争议"章节"""
        return bool(self.detect(cards, use_llm=use_llm).get("disputes"))


# 单例
dispute_detector = DisputeDetector()
