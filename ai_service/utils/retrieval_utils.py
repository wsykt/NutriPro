"""多路检索融合工具

提供 BM25 关键词检索 + RRF 结果融合重排，提升召回质量。
所有检索场景（对话、食材、知识库）统一调用此工具。
"""

import math
import re
import heapq
from collections import Counter
from typing import List, Dict, Optional


# ============================================================
# BM25 检索（轻量纯 Python 实现，无三方依赖）
# ============================================================

class BM25Retriever:
    """轻量 BM25 检索器

    用法：
        bm25 = BM25Retriever()
        bm25.index(documents)  # 建索引
        results = bm25.search(query, top_k=5)  # 检索
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._documents: List[str] = []
        self._doc_metadatas: List[dict] = []
        self._avgdl: float = 0
        self._doc_freq: Dict[str, int] = {}
        self._doc_len: List[int] = []
        self._total_docs: int = 0
        self._is_indexed = False

    def _tokenize(self, text: str) -> List[str]:
        """中文分词：按字符 bi-gram + 单字混合"""
        text = re.sub(r'[^\w\u4e00-\u9fff]', ' ', text.lower())
        tokens = []
        for word in text.split():
            if len(word) <= 1:
                tokens.append(word)
                continue
            # bi-gram
            for i in range(len(word) - 1):
                tokens.append(word[i:i+2])
            # 保留原词
            tokens.append(word)
        # 过滤单字停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没', '看', '好', '自', '己', '这', '他', '她', '它', '们', '那', '些'}
        return [t for t in tokens if t not in stop_words and len(t.strip()) > 0]

    def index(self, documents: List[str], metadatas: Optional[List[dict]] = None):
        """建立 BM25 索引"""
        self._documents = documents
        self._doc_metadatas = metadatas or [{}] * len(documents)
        self._total_docs = len(documents)
        self._doc_len = []
        self._doc_freq = Counter()
        self._avgdl = 0

        total_length = 0
        for doc in documents:
            tokens = self._tokenize(doc)
            self._doc_len.append(len(tokens))
            total_length += len(tokens)
            for token in set(tokens):
                self._doc_freq[token] += 1

        self._avgdl = total_length / max(self._total_docs, 1)
        self._is_indexed = True

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """执行 BM25 检索"""
        if not self._is_indexed or self._total_docs == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 计算每个文档的 BM25 分数
        scores = []
        for idx in range(self._total_docs):
            score = 0
            doc_len = self._doc_len[idx]
            for token in query_tokens:
                if token not in self._doc_freq:
                    continue
                df = self._doc_freq[token]
                idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1.0)
                # 计算词频
                tf = self._tokenize(self._documents[idx]).count(token)
                tf = tf / max(doc_len, 1) * self._avgdl
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * doc_len / max(self._avgdl, 1)))
            scores.append(score)

        # 取 Top-K
        top_indices = heapq.nlargest(top_k, range(len(scores)), key=lambda i: scores[i])
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "content": self._documents[idx],
                    "score": round(scores[idx], 4),
                    "metadata": self._doc_metadatas[idx],
                })
        return results


# ============================================================
# RRF 融合重排
# ============================================================

def rrf_fuse(*ranked_lists: List[Dict], weights: Optional[List[float]] = None, k: int = 60) -> List[Dict]:
    """RRF（Reciprocal Rank Fusion）算法融合多路检索结果

    参数:
        *ranked_lists: 每路检索结果列表，每项含 content + score
        weights: 每路权重，默认均等
        k: RRF 常数（默认 60，越大融合越平滑）

    返回:
        融合后排重后的结果列表（score 为融合分数）
    """
    if not ranked_lists:
        return []

    if weights is None:
        weights = [1.0] * len(ranked_lists)
    else:
        weights = [w / sum(weights) for w in weights]  # 归一化

    # 融合分数
    fusion_scores = {}  # content -> score
    fusion_metadata = {}

    for list_idx, results in enumerate(ranked_lists):
        weight = weights[list_idx]
        for rank, item in enumerate(results):
            content = item["content"]
            rrf_score = weight / (k + rank + 1)
            if content in fusion_scores:
                fusion_scores[content] += rrf_score
            else:
                fusion_scores[content] = rrf_score
                fusion_metadata[content] = item.get("metadata", {})

    # 按融合分数降序
    sorted_items = sorted(fusion_scores.items(), key=lambda x: -x[1])

    results = []
    for content, score in sorted_items:
        results.append({
            "content": content,
            "score": round(score, 4),
            "metadata": fusion_metadata.get(content, {}),
        })
    return results


# ============================================================
# 检索去重工具
# ============================================================

def deduplicate_results(results: List[Dict], overlap_threshold: float = 0.9) -> List[Dict]:
    """基于字符重叠率去重（保留首次出现的条目）"""
    if not results:
        return results

    def char_overlap(a: str, b: str) -> float:
        if not a or not b:
            return 0
        # 按字符集合计算 Jaccard 相似度
        set_a, set_b = set(a), set(b)
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / max(len(union), 1)

    deduped = []
    for item in results:
        is_dup = False
        for existing in deduped:
            if char_overlap(item["content"], existing["content"]) > overlap_threshold:
                is_dup = True
                break
        if not is_dup:
            deduped.append(item)
    return deduped


# ============================================================
# 上下文截断
# ============================================================

def truncate_context(results: List[Dict], max_chars: int = 500) -> List[Dict]:
    """截断检索结果内容，防止超长上下文"""
    for item in results:
        content = item.get("content", "")
        if len(content) > max_chars:
            item["content"] = content[:max_chars] + "..."
    return results


# ============================================================
# 权威加权（卫健委/国家标准结果权重上浮）
# ============================================================

AUTHORITY_KEYWORDS = [
    "中国居民膳食指南",
    "中国食物成分表",
    "WS/T",  # 卫生健康标准
    "GB ",   # 国家标准
    "国家标准",
    "卫健委",
    "中国营养学会",
    "中国糖尿病医学营养治疗指南",
    "中国肥胖预防和控制蓝皮书",
]

def boost_authority_results(results: List[Dict], boost_factor: float = 1.2) -> List[Dict]:
    """权威/国家标准来源的检索结果权重上浮"""
    for item in results:
        content = item.get("content", "")
        metadata = item.get("metadata", {})
        source = str(metadata.get("source", ""))

        is_authority = any(kw in content or kw in source for kw in AUTHORITY_KEYWORDS)
        if is_authority:
            item["score"] = round(item.get("score", 0) * boost_factor, 4)
            item["is_authority"] = True
        else:
            item["is_authority"] = False

    # 重新按分数排序
    results.sort(key=lambda x: -x.get("score", 0))
    return results


# ============================================================
# 高级多路检索入口（一站式调用）
# ============================================================

def hybrid_search(
    query: str,
    vector_search_fn,
    bm25_retriever: BM25Retriever,
    top_k: int = 5,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
    deduplicate: bool = True,
) -> List[Dict]:
    """混合检索入口：向量 + BM25 双路融合

    参数:
        query: 查询文本
        vector_search_fn: 向量检索回调，入参 (query, top_k)，返回 [{"content":..., "score":...}]
        bm25_retriever: BM25 检索器实例
        top_k: 各路的 top_k 参数（融合前）
        vector_weight: 向量路权重（默认 0.6）
        bm25_weight: BM25 路权重（默认 0.4）
        deduplicate: 是否去重

    返回:
        融合重排后的结果列表，已截断
    """
    # 1. 双路检索
    vector_results = vector_search_fn(query, top_k=top_k) if vector_search_fn else []
    bm25_results = bm25_retriever.search(query, top_k=top_k) if bm25_retriever._is_indexed else []

    # 2. RRF 融合
    weights = [vector_weight, bm25_weight]
    fused = rrf_fuse(vector_results, bm25_results, weights=weights)

    # 3. 去重
    if deduplicate:
        fused = deduplicate_results(fused)

    # 4. 权威加权
    fused = boost_authority_results(fused)

    # 5. 截断
    fused = truncate_context(fused)

    return fused
