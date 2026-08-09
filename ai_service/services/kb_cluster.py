# -*- coding: utf-8 -*-
"""知识库双层智能聚类（kb_cluster.py）

目标架构"双层聚类"：
- 第一层：BGE 向量粗筛（余弦相似度，批量计算）；
- 第二层：灰色区间相似度调用本地/云端 LLM 语义终审（是否同主题/同结论）；
- 三层分级：高相似直接归簇 / 低相似直接无关 / 灰色区间 LLM 判定。

用于把同主题的文献卡片聚成簇，供"文献合并""争议识别""综述生成"复用。
"""
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from config.settings import settings
from vector.embedder import embedder

logger = logging.getLogger(__name__)

# 卡片四段骨架（与知识库卡片 purified_content 结构一致）
_SECTIONS = ("核心循证结论", "量化临床数据", "适用人群", "局限性/学术争议")


def card_text(card: Dict[str, Any], max_len: int = 400) -> str:
    """把卡片转成用于相似度比较/LLM 判定的紧凑文本"""
    parts = [str(card.get("title", "") or "")]
    content = card.get("purified_content") or card.get("content") or ""
    if content:
        parts.append(str(content)[:max_len])
    return "\n".join(parts)


def cosine_similarity_matrix(texts: List[str]) -> np.ndarray:
    """批量计算 BGE 向量余弦相似度矩阵（第一层粗筛）"""
    n = len(texts)
    if n == 0:
        return np.zeros((0, 0))
    try:
        vecs = embedder.encode([t[:500] for t in texts])
        norm = np.linalg.norm(vecs, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        unit = vecs / norm
        return np.dot(unit, unit.T)
    except Exception as e:
        logger.warning(f"BGE 相似度矩阵计算失败，降级为字符重叠: {e}")
        return _char_overlap_matrix(texts)


def _char_overlap_matrix(texts: List[str]) -> np.ndarray:
    n = len(texts)
    mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i >= j:
                mat[i][j] = mat[j][i]
                continue
            t1 = set(texts[i].replace(" ", "")[:200])
            t2 = set(texts[j].replace(" ", "")[:200])
            if not t1 or not t2:
                continue
            mat[i][j] = mat[j][i] = len(t1 & t2) / len(t1 | t2)
    np.fill_diagonal(mat, 1.0)
    return mat


class KnowledgeClusterer:
    """双层智能聚类器"""

    def __init__(self, llm: Optional[Any] = None,
                 high_threshold: float = None,
                 low_threshold: float = None,
                 enabled: bool = None):
        self.llm = llm
        self.high_threshold = high_threshold if high_threshold is not None else settings.KB_CLUSTER_HIGH_THRESHOLD
        self.low_threshold = low_threshold if low_threshold is not None else settings.KB_CLUSTER_LOW_THRESHOLD
        self.enabled = enabled if enabled is not None else settings.KB_CLUSTER_ENABLED

    # ---------- 第二层：LLM 语义终审 ----------
    def _llm_judge_pair(self, text_a: str, text_b: str) -> bool:
        """灰色区间用 LLM 判定两卡片是否同一主题/可归簇"""
        prompt = [
            {"role": "system", "content": "你是营养学知识库聚类助手。判断两篇文献摘要是否属于同一主题且结论方向一致。"
                                          "只输出 JSON：{\"same_topic\": true/false, \"reason\": \"简短理由\"}"},
            {"role": "user", "content": f"文献A:\n{text_a[:400]}\n\n文献B:\n{text_b[:400]}"},
        ]
        try:
            if self.llm is None:
                from llm.router import llm as _default_llm
                self.llm = _default_llm
            raw = self.llm.chat_json(prompt, temperature=0.0)
            return bool(raw.get("same_topic", False))
        except Exception as e:
            logger.warning(f"LLM 聚类终审失败，回退为按高阈值判定: {e}")
            return False

    # ---------- 主流程：双层聚类 ----------
    def cluster(self, cards: List[Dict[str, Any]],
                judge: Optional[Callable[[str, str], bool]] = None) -> Dict[str, Any]:
        """对卡片列表执行双层聚类。

        Returns:
            {
              "clusters": [{"cluster_id", "cards": [card, ...], "topic", "score"}],
              "singles": [card, ...],
              "meta": {"total", "clustered", "single", "pairs_high", "pairs_llm", "pairs_ambiguous", "llm_judged"},
            }
        """
        if not self.enabled or len(cards) < 2:
            return {"clusters": [], "singles": cards, "method": "skipped",
                    "meta": {"total": len(cards), "clustered": 0, "single": len(cards),
                             "pairs_high": 0, "pairs_llm": 0, "pairs_ambiguous": 0, "llm_judged": 0}}

        texts = [card_text(c) for c in cards]
        sim = cosine_similarity_matrix(texts)
        n = len(cards)
        judge_fn = judge or self._llm_judge_pair

        # 并查集：把"相关"的卡片合并
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        meta = {"pairs_high": 0, "pairs_llm": 0, "pairs_ambiguous": 0, "llm_judged": 0}
        for i in range(n):
            for j in range(i + 1, n):
                s = float(sim[i][j])
                if s >= self.high_threshold:
                    union(i, j)
                    meta["pairs_high"] += 1
                elif s < self.low_threshold:
                    continue
                else:
                    meta["pairs_ambiguous"] += 1
                    if judge_fn(texts[i], texts[j]):
                        union(i, j)
                        meta["llm_judged"] += 1
                    meta["pairs_llm"] += 1

        # 组装簇
        groups: Dict[int, List[Dict[str, Any]]] = {}
        for idx, card in enumerate(cards):
            groups.setdefault(find(idx), []).append(card)

        clusters, singles = [], []
        for root, members in groups.items():
            if len(members) >= 2:
                topic = members[0].get("topic") or members[0].get("group") or "未分类"
                clusters.append({
                    "cluster_id": f"cluster_{root}",
                    "cards": members,
                    "topic": topic,
                    "score": round(float(sim[root][root]) if n else 0.0, 3),
                    "card_count": len(members),
                })
            else:
                singles.append(members[0])

        meta.update({"total": n, "clustered": n - len(singles), "single": len(singles)})
        return {"clusters": clusters, "singles": singles, "meta": meta}


# 单例
kb_clusterer = KnowledgeClusterer()
