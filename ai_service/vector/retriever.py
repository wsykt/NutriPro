import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction
from vector.embedder import embedder
from vector.reranker import reranker
from config.settings import settings
from utils.retry_utils import chromadb_retry
from utils.retrieval_utils import BM25Retriever, hybrid_search
from utils.log_config import get_logger
import numpy as np
import uuid

_logger = get_logger("retriever")


class BGEEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        embeddings = embedder.encode(input)
        return embeddings.tolist()


class ChromaRetriever:

    # ============================================================
    # 五库物理隔离配置
    # 原规划：食物 / 膳食指南(含人群建议) / 运动 / 补剂 / 文献 → 物理独立集合
    # + AI 模板独立集合（与权威知识分开，模板可快速重建）
    # ============================================================
    COLLECTION_DEFS = [
        {"name": "kb_food",       "desc": "食物营养（成分/GI/营养知识）"},
        {"name": "kb_guide",      "desc": "膳食指南（指南/标准/餐次建议）"},
        {"name": "kb_crowd",      "desc": "人群建议（按人群定制方案）"},
        {"name": "kb_literature", "desc": "文献（PubMed/权威报告/网络资料）"},
        {"name": "kb_templates",  "desc": "AI 模板卡片（可重建）"},
    ]
    # 保留的旧集合名（只读备份，迁移完成后不再写入）
    LEGACY_COLLECTION = "health_knowledge"

    # metadata → 物理集合 路由规则（按优先级顺序匹配）
    COLLECTION_ROUTING = [
        # template_type=ai_template 优先 → 模板库
        ({"template_type": "ai_template"}, "kb_templates"),
        # source_type=literature → 文献库
        ({"source_type": "literature"}, "kb_literature"),
        # category 显式映射
        ({"category": "food_data"}, "kb_food"),
        ({"category": "food_knowledge"}, "kb_food"),
        ({"category": "dietary_guideline"}, "kb_guide"),
        ({"category": "nutrition_standard"}, "kb_guide"),
        ({"category": "health_standard"}, "kb_guide"),
        ({"category": "meal_guidance"}, "kb_guide"),
        ({"category": "crowd_specific"}, "kb_crowd"),
    ]
    # 默认落库（未匹配到任何规则的文档 → 膳食指南库，与旧逻辑一致）
    DEFAULT_COLLECTION = "kb_guide"

    # 语义去重窗口：仅对排名靠前的少量结果做两两 BGE 判重（避免 O(n²) 本地推理）
    DEDUP_TOP_WINDOW = 5
    # 轻量文本签名粗筛阈值（字符集 Jaccard ≥ 该值才调用 BGE 精确判重）
    # 注意：模板卡片同人群结构相似，字符集 Jaccard 普遍 0.6~0.9，阈值过低（如0.5）
    # 会触发大量无效 BGE 判重（CPU 单次约 0.7s），导致检索慢 5~10s。阈值提高后
    # 仅对真正近乎逐字重复的文本触发 BGE（去重阈值为 BGE 余弦 ≥ 0.95）。
    LIGHT_SIMILARITY_PRE_FILTER = 0.9
    # 长度比例上限：两条文本长度相差超过该比例时不可能近乎逐字重复，直接跳过 BGE 判重
    LENGTH_RATIO_SKIP = 1.3

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # 多集合：按配置创建 5 个物理集合（同实例，共用 BGE embedder 保证语义可比）
        self.collections = {}
        for col_def in self.COLLECTION_DEFS:
            self.collections[col_def["name"]] = self.client.get_or_create_collection(
                col_def["name"],
                embedding_function=BGEEmbeddingFunction()
            )
        # 兼容旧单集合引用（仅用于 count 汇总 / 只读，不写入）
        self.collection = self.collections["kb_guide"]
        self.MAX_CONTENT_LENGTH = 800
        self.DUPLICATE_SIMILARITY_THRESHOLD = 0.95
        self.MIN_SIMILARITY_THRESHOLD = 0.15

        # BM25 增量维护：按集合独立维护（每库独立索引，避免跨库污染）
        # {collection_name: {"dirty": bool, "pending": {"documents": [], "metadatas": []}, "bm25": BM25Retriever}}
        self._bm25_states = {}
        for col_def in self.COLLECTION_DEFS:
            self._bm25_states[col_def["name"]] = {
                "dirty": False,
                "pending": {"documents": [], "metadatas": []},
                "bm25": BM25Retriever(),
            }

        self._build_bm25_index()

    def _build_bm25_index(self):
        """从各物理集合加载全部文档构建独立 BM25 索引"""
        for col_name, state in self._bm25_states.items():
            try:
                collection = self.collections[col_name]
                total = collection.count()
                if total > 0:
                    all_data = collection.get(include=["documents", "metadatas"])
                    documents = all_data.get("documents", []) or []
                    metadatas = all_data.get("metadatas", []) or []
                    if documents:
                        state["bm25"].index(documents, metadatas)
                        _logger.info(f"BM25 索引已建立 [{col_name}]，共 {len(documents)} 条记录")
            except Exception as e:
                _logger.warning(f"BM25 索引建立失败 [{col_name}]（非关键错误）: {e}")

    def _route_collection(self, metadata: dict) -> str:
        """根据 metadata 路由到物理集合（未匹配 → 默认库）"""
        meta = metadata or {}
        for rule, col_name in self.COLLECTION_ROUTING:
            if all(meta.get(k) == v for k, v in rule.items()):
                return col_name
        # 兜底：模板类（有 template_type 但非 ai_template）也入模板库
        if meta.get("template_type"):
            return "kb_templates"
        return self.DEFAULT_COLLECTION

    def _all_collection_names(self):
        return [c["name"] for c in self.COLLECTION_DEFS]

    @chromadb_retry
    def search(self, query, top_k=3, target_crowd=None, collections=None, doc_level=None):
        """多集合并行向量检索（collections=None → 全库并行，跨库按相似度合并）

        五库物理隔离后的统一入口：
        - 可指定 collections（如 ["kb_food", "kb_crowd"]）实现"多库并行检索"
        - 不指定则全部 5 个库并行检索后合并去重（行为与旧单集合一致，但检索隔离）
        - doc_level 限定检索粒度：document（整篇）/ paragraph（段落）/ fact（事实卡片）
        """
        query_vec = embedder.encode_query(query).tolist()

        col_names = collections if collections else self._all_collection_names()
        all_raw = []

        for col_name in col_names:
            collection = self.collections[col_name]
            if collection.count() == 0:
                continue
            where = None
            conditions = []
            if target_crowd and target_crowd != "普通人":
                # 人群过滤：命中 target_crowd 或通用权威知识（旧逻辑保留）
                conditions.append({"$or": [
                    {"target_crowd": target_crowd},
                    {"category": {"$in": ["dietary_guideline", "nutrition_standard", "health_standard", "food_knowledge", "meal_guidance"]}}
                ]})
            if doc_level in ("document", "paragraph", "fact"):
                # 三级检索粒度过滤
                conditions.append({"doc_level": doc_level})
            if conditions:
                where = conditions[0] if len(conditions) == 1 else {"$and": conditions}
            try:
                results = collection.query(
                    query_embeddings=[query_vec],
                    n_results=top_k * 2,
                    where=where,
                    include=["documents", "metadatas", "distances"],
                )
                for i in range(len(results["documents"][0])):
                    all_raw.append({
                        "content": results["documents"][0][i],
                        "similarity": 1 - results["distances"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "_collection": col_name,
                    })
            except Exception as e:
                _logger.warning(f"集合检索失败 [{col_name}]: {e}")

        all_raw = sorted(all_raw, key=lambda x: x["similarity"], reverse=True)
        # 过滤极低相似度结果
        all_raw = [r for r in all_raw if r["similarity"] >= self.MIN_SIMILARITY_THRESHOLD]
        filtered_results = self._deduplicate_results(all_raw)

        for r in filtered_results:
            r["content"] = self._truncate_content(r["content"])

        return filtered_results[:top_k]

    def _deduplicate_results(self, results):
        """对候选结果去重（避免 O(n²) BGE 本地编码）：
        1) 先按相似度降序，保证高分结果优先保留；
        2) 用轻量字符集签名做粗筛（纯字符运算，零本地推理）；
        3) 仅对排名靠前（top 窗口）且粗筛疑似重复的结果调用 BGE 精确判重。
        """
        if not results:
            return results

        # 1) 按相似度降序（高分优先保留，与 search 外层排序一致）
        results = sorted(results, key=lambda x: x.get("similarity", 0), reverse=True)

        unique_results = []
        seen = []  # [(签名, content)]，仅保留最近 top 窗口用于比对

        for result in results:
            content = result["content"]
            sig = self._light_text_signature(content)

            is_duplicate = False
            # 2) 轻量粗筛：只与窗口内最近保留的结果做字符集比对
            for seen_sig, seen_content in seen[-self.DEDUP_TOP_WINDOW:]:
                if self._light_signature_similarity(sig, seen_sig) >= self.LIGHT_SIMILARITY_PRE_FILTER:
                    # 长度比例悬殊 → 不可能近乎逐字重复，跳过 BGE 判重
                    l1, l2 = len(content), len(seen_content)
                    if l1 > 0 and l2 > 0 and max(l1, l2) / min(l1, l2) > self.LENGTH_RATIO_SKIP:
                        continue
                    # 3) 疑似重复 → BGE 向量精确判重（窗口内最多 DEDUP_TOP_WINDOW 次编码）
                    if self._content_similarity(content, seen_content) >= self.DUPLICATE_SIMILARITY_THRESHOLD:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique_results.append(result)
                seen.append((sig, content))

        return unique_results

    @staticmethod
    def _light_text_signature(text):
        """轻量文本签名：去空白后的字符集合（前 200 字符），用于去重粗筛"""
        if not text:
            return set()
        return set(text.replace(" ", "").replace("\n", "")[:200])

    @staticmethod
    def _light_signature_similarity(sig1, sig2):
        """字符集 Jaccard 相似度（粗筛用，O(1) 成本）"""
        if not sig1 or not sig2:
            return 0.0
        union = sig1 | sig2
        return len(sig1 & sig2) / len(union) if union else 0.0

    # BGE 编码结果缓存：去重判重时同一文本会与多条候选比较，避免同一文本重复 CPU 推理
    _EMBED_CACHE = {}
    _EMBED_CACHE_MAX = 64

    def _cached_encode(self, text_key):
        """按文本（截断后）缓存 BGE 向量（有界缓存，超出后简单清空重建）"""
        vec = self._EMBED_CACHE.get(text_key)
        if vec is None:
            vec = embedder.encode([text_key])[0]
            if len(self._EMBED_CACHE) >= self._EMBED_CACHE_MAX:
                self._EMBED_CACHE.clear()
            self._EMBED_CACHE[text_key] = vec
        return vec

    def _content_similarity(self, text1, text2):
        """基于 BGE 向量的余弦相似度（替代脆弱的 Jaccard 字符集方法）"""
        if not text1 or not text2:
            return 0.0
        try:
            v1 = self._cached_encode(text1[:500])
            v2 = self._cached_encode(text2[:500])
            dot = float(np.dot(v1, v2))
            norm1 = float(np.linalg.norm(v1))
            norm2 = float(np.linalg.norm(v2))
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot / (norm1 * norm2)
        except Exception:
            # 降级为简单的字符集重叠（兜底）
            t1 = text1.replace(" ", "").replace("\n", "")[:200]
            t2 = text2.replace(" ", "").replace("\n", "")[:200]
            if not t1 or not t2:
                return 0.0
            common = set(t1) & set(t2)
            all_chars = set(t1) | set(t2)
            return len(common) / len(all_chars) if all_chars else 0.0

    def hybrid_retrieve(self, query, top_k=5, target_crowd=None, collections=None, doc_level=None,
                        use_rerank=True):
        """BM25 + 向量双路融合检索（五库隔离：可指定 collections 并行多库检索）

        doc_level: document/paragraph/fact 三级检索粒度过滤（None → 不限）
        融合后用本地 bge-reranker 做交叉编码精排（候选集放大 RERANKER_CANDIDATE_MULTIPLIER 倍，
        模型缺失 / 推理失败自动降级为融合原排序）。
        use_rerank=False 时跳过本次交叉编码精排（用于多库并行场景：各库先不重排，
        由调用方合并后统一精排一次，避免 CPU 交叉编码器被反复调用）。
        """
        # 检索前合并重建各集合 BM25 索引（批量摄入后仅在此处重建一次）
        self._rebuild_bm25_if_dirty()

        candidate_k = top_k * settings.RERANKER_CANDIDATE_MULTIPLIER

        def vector_search_fn(q, top_k=top_k):
            return self.search(q, top_k=top_k, target_crowd=target_crowd,
                               collections=collections, doc_level=doc_level)

        try:
            from utils.retrieval_utils import hybrid_search_multi as _hybrid_search_multi
            results = _hybrid_search_multi(
                query=query,
                vector_search_fn=vector_search_fn,
                bm25_states=self._bm25_states,
                collections=collections if collections else self._all_collection_names(),
                top_k=candidate_k,
                vector_weight=0.6,
                bm25_weight=0.4,
                doc_level=doc_level,
            )
        except Exception as e:
            _logger.warning(f"混合检索降级为纯向量检索: {e}")
            results = vector_search_fn(query, candidate_k)

        # 本地 reranker 精排（不可用时原样返回，此处统一截断到 top_k）
        if use_rerank:
            results = reranker.rerank(query, results, top_k=top_k)
        return results[:top_k]

    def dynamic_retrieve(self, query, target_crowd=None, default_top_k=5):
        """动态 top_k 融合检索：按相似度分布分段决定返回条数

        分段策略（阈值可从环境变量配置，按实际相似度分布校准）：
        - 命中条数 ≥ RAG_TOPK_HIGH_THRESHOLD(0.70) → 取最高 RAG_TOPK_HIGH_COUNT(5) 条
        - 命中条数 ≥ RAG_TOPK_LOW_THRESHOLD(0.45)  → 取 RAG_TOPK_LOW_COUNT(3) 条
        - 无达标命中 → 按 default_top_k 取最高分若干条（保底）
        """
        if not settings.RAG_DYNAMIC_TOPK_ENABLED:
            return self.hybrid_retrieve(query, top_k=default_top_k, target_crowd=target_crowd)

        high_t = settings.RAG_TOPK_HIGH_THRESHOLD
        low_t = settings.RAG_TOPK_LOW_THRESHOLD
        high_k = settings.RAG_TOPK_HIGH_COUNT
        low_k = settings.RAG_TOPK_LOW_COUNT

        # 拉取更大候选集，供分段判断后截断
        candidate_k = max(high_k, low_k, default_top_k) * settings.RAG_TOPK_CANDIDATE_MULTIPLIER
        try:
            results = self.hybrid_retrieve(query, top_k=candidate_k, target_crowd=target_crowd)
        except Exception:
            results = []
        if not results:
            return []

        # 按相似度分段
        high_hits = [r for r in results if r.get("similarity", 0) >= high_t]
        if high_hits:
            return high_hits[:high_k]
        low_hits = [r for r in results if r.get("similarity", 0) >= low_t]
        if low_hits:
            return low_hits[:low_k]
        # 无达标命中：保底返回 default_top_k 条最高分（避免完全无参考）
        return results[:default_top_k]

    def _truncate_content(self, content):
        if len(content) <= self.MAX_CONTENT_LENGTH:
            return content
        return content[:self.MAX_CONTENT_LENGTH] + "..."

    @chromadb_retry
    def add(self, documents, metadatas=None, ids=None):
        """按 metadata 路由写入对应物理集合（五库隔离）"""
        embeddings = embedder.encode(documents).tolist()

        # 按条路由：每条文档依据 metadata 落到对应集合
        metadatas = metadatas or [{}] * len(documents)
        ids = ids or [f"auto_{uuid.uuid4().hex}" for _ in documents]

        # 分组落库：同一集合的文档批量写入（减少 ChromaDB 调用次数）
        buckets = {}
        for i, doc in enumerate(documents):
            col_name = self._route_collection(metadatas[i] if i < len(metadatas) else {})
            buckets.setdefault(col_name, {"docs": [], "metas": [], "emb": [], "ids": []})
            buckets[col_name]["docs"].append(doc)
            buckets[col_name]["metas"].append(metadatas[i])
            buckets[col_name]["emb"].append(embeddings[i])
            buckets[col_name]["ids"].append(ids[i])

        for col_name, bucket in buckets.items():
            self.collections[col_name].add(
                documents=bucket["docs"],
                metadatas=bucket["metas"],
                ids=bucket["ids"],
                embeddings=bucket["emb"],
            )
            # 该集合 BM25 增量挂入待索引队列并打脏标记
            self._mark_bm25_dirty(col_name, bucket["docs"], bucket["metas"])

        # 双写一致性：ai_template 卡片同步写入 SQLite 模板库（权威副本）
        self._dual_write_templates(documents, metadatas, ids)

    def _mark_bm25_dirty(self, collection_name, documents, metadatas=None):
        """把新文档挂入指定集合的 BM25 待索引队列并打脏标记"""
        state = self._bm25_states[collection_name]
        state["dirty"] = True
        state["pending"]["documents"].extend(documents or [])
        state["pending"]["metadatas"].extend(metadatas or [])

    def _rebuild_bm25_if_dirty(self):
        """检索前合并重建各集合的 BM25 索引（脏标记置位时执行）：
        把累积的待索引文档并入旧索引后一次性重建；失败则保持脏标记下次再试。
        """
        for col_name, state in self._bm25_states.items():
            if not state["dirty"]:
                continue
            state["dirty"] = False
            try:
                pending_docs = state["pending"].get("documents") or []
                pending_metas = state["pending"].get("metadatas") or []
                state["pending"] = {"documents": [], "metadatas": []}
                if not pending_docs:
                    continue
                # BM25Retriever 为全量 index 实现，采用「旧索引 + 待索引」合并重建
                bm25 = state["bm25"]
                old_docs = bm25._documents if bm25._is_indexed else []
                old_metas = bm25._doc_metadatas if bm25._is_indexed else []
                bm25.index(old_docs + pending_docs, (old_metas or []) + pending_metas)
                _logger.info(
                    f"BM25 索引合并重建完成 [{col_name}]（本次新增 {len(pending_docs)} 条，"
                    f"共 {len(old_docs) + len(pending_docs)} 条）")
            except Exception as e:
                _logger.warning(f"BM25 索引合并重建失败 [{col_name}]（非关键错误）: {e}")
                state["dirty"] = True  # 失败恢复脏标记，下次检索再试

    def _dual_write_templates(self, documents, metadatas, ids):
        """把本次写入中的 ai_template 卡片双写到 SQLite（失败不影响主流程）"""
        try:
            from services.template_store import template_store
        except Exception:
            return
        try:
            if not documents:
                return
            for i, meta in enumerate(metadatas or []):
                meta = meta or {}
                if meta.get("template_type") != "ai_template":
                    continue
                doc = documents[i] if i < len(documents) else ""
                cid = ids[i] if ids and i < len(ids) else ""
                if not doc or not cid:
                    continue
                template_store.upsert(cid, doc, meta, meta.get("full_content", ""))
        except Exception:
            pass

    def add_with_backup(self, display_doc: str, full_doc: str, metadata: dict, doc_id: str):
        """双层存储入库：display_doc 存入 ChromaDB 用于检索，full_doc 存入 metadata.full_content 用于改写/分析。
        - display_doc: 精简展示版（约200字），用于向量检索匹配
        - full_doc: 完整备份版（保留核心结论原文），用于大模型改写和分析
        """
        meta = dict(metadata) if metadata else {}
        if settings.KB_DUAL_LAYER_STORAGE and full_doc and len(full_doc) > len(display_doc):
            meta["full_content"] = full_doc
            meta["has_backup"] = True
        else:
            meta["has_backup"] = False
        self.add(documents=[display_doc], metadatas=[meta], ids=[doc_id])

    def get_full_content(self, doc_id: str) -> str:
        """获取双层存储的完整备份内容（无备份时返回 document 本身），跨集合查找"""
        try:
            # 兼容单集合场景（测试 mock）：优先 collections，缺失时回退 collection
            col_iter = self.collections.values() if hasattr(self, "collections") else [self.collection]
            for col in col_iter:
                result = col.get(ids=[doc_id], include=["documents", "metadatas"])
                if result["ids"]:
                    meta = result["metadatas"][0] or {}
                    if meta.get("has_backup") and meta.get("full_content"):
                        return meta["full_content"]
                    return result["documents"][0]
            return ""
        except Exception as e:
            _logger.warning(f"获取完整内容失败: {e}")
            return ""

    def count(self):
        return sum(col.count() for col in self.collections.values())

    def clear(self):
        """清空所有物理集合（旧集合 health_knowledge 只读保留）"""
        for col_def in self.COLLECTION_DEFS:
            col_name = col_def["name"]
            self.client.delete_collection(col_name)
            self.collections[col_name] = self.client.get_or_create_collection(
                col_name,
                embedding_function=BGEEmbeddingFunction()
            )
            # 同步清空该集合 BM25 索引与待索引队列
            state = self._bm25_states[col_name]
            state["bm25"].index([], [])
            state["pending"] = {"documents": [], "metadatas": []}
            state["dirty"] = False
        # 兼容旧引用指向 kb_guide
        self.collection = self.collections["kb_guide"]

    def get_rich_stats(self):
        """返回知识库的丰富统计数据（真实数据驱动）"""
        total_docs = self.count()
        stats = {
            "total_docs": total_docs,
            "categories": {},
            "sources": {},
            "crowd_distribution": {},
            "content_stats": {"min_len": 0, "max_len": 0, "avg_len": 0, "median_len": 0},
            "sample_entries": [],
        }

        if total_docs == 0:
            return stats

        try:
            from collections import Counter
            cats = Counter()
            srcs = Counter()
            crowds = Counter()
            lengths = []
            sample_pool = []

            for col_name, col in self.collections.items():
                col_count = col.count()
                if col_count == 0:
                    continue
                all_data = col.get(include=["documents", "metadatas"])
                metadatas = all_data.get("metadatas", []) or []
                docs = all_data.get("documents", []) or []

                cats.update(m.get("category", "unknown") for m in metadatas)
                srcs.update(m.get("source", "未知") for m in metadatas)
                crowds.update(m.get("target_crowd", "") for m in metadatas if m.get("target_crowd"))
                lengths.extend(len(d) for d in docs)
                for i in range(len(docs)):
                    sample_pool.append({
                        "content_preview": docs[i][:100] + ("..." if len(docs[i]) > 100 else ""),
                        "category": metadatas[i].get("category", ""),
                        "source": metadatas[i].get("source", ""),
                        "collection": col_name,
                    })

            stats["categories"] = dict(cats.most_common())
            stats["sources"] = dict(srcs.most_common())
            stats["crowd_distribution"] = dict(crowds.most_common())

            lengths.sort()
            if lengths:
                stats["content_stats"] = {
                    "min_len": min(lengths),
                    "max_len": max(lengths),
                    "avg_len": round(sum(lengths) / len(lengths), 1),
                    "median_len": lengths[len(lengths) // 2],
                }
            stats["sample_entries"] = sample_pool[:5]
            # 各集合分布（五库隔离可见性）
            stats["collections"] = {
                col_name: col.count()
                for col_name, col in self.collections.items()
            }
        except Exception as e:
            _logger.warning(f"get_rich_stats 聚合失败: {e}")

        return stats

    def ensure_initial_data(self):
        if self.count() > 0:
            return

        health_knowledge = [
            {
                "content": "中国居民膳食指南2022核心推荐一：食物多样，合理搭配。每天摄入12种以上食物，每周25种以上。主食粗细搭配，每天摄入谷薯类食物250-400g，其中全谷物和杂豆类50-150g，薯类50-100g。",
                "metadata": {"category": "dietary_guideline", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "中国居民膳食指南2022核心推荐二：少盐少油，控糖限酒。成人每天食盐不超过5g，烹调油25-30g，添加糖不超过50g，最好控制在25g以下。不饮酒或少量饮酒，男性酒精摄入量不超过25g，女性不超过15g。",
                "metadata": {"category": "dietary_guideline", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "中国居民膳食指南2022核心推荐三：吃动平衡，健康体重。各年龄段人群都应天天运动，每周至少进行150分钟中等强度有氧运动，或75分钟高强度有氧运动，或等量的中等强度和高强度有氧活动组合。",
                "metadata": {"category": "dietary_guideline", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "中国居民膳食指南2022核心推荐四：杜绝浪费，兴新食尚。珍惜食物，按需备餐，提倡分餐不浪费。选择新鲜卫生的食物和适宜的烹调方式，保障饮食卫生。",
                "metadata": {"category": "dietary_guideline", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "成人蛋白质推荐摄入量：男性每天65g，女性每天55g。优质蛋白质占一半以上，包括鱼、禽、蛋、瘦肉、豆制品、奶制品。健身人群蛋白质需求为1.6-2.2g/kg体重/天。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "老年人膳食建议：蛋白质推荐摄入量为1.2-1.4g/kg体重/天，高于成年人。食物要细软易消化，少量多餐，每天5-6餐。保证充足钙和维生素D摄入，预防骨质疏松。",
                "metadata": {"category": "crowd_specific", "target_crowd": "老年人", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "孕妇膳食建议：孕早期叶酸摄入量增加至每天400μg，铁摄入量增加至每天27mg。孕中晚期蛋白质增加15-20g/天，能量增加300-450kcal/天。避免生冷食物和酒精摄入。",
                "metadata": {"category": "crowd_specific", "target_crowd": "孕妇", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "青少年膳食建议：能量和营养素需求高于成年人，蛋白质1.2-1.5g/kg体重/天。三餐规律，保证早餐摄入，每天摄入足量钙和维生素D促进骨骼发育。减少含糖饮料和零食摄入。",
                "metadata": {"category": "crowd_specific", "target_crowd": "青少年", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "糖尿病患者膳食建议：选择低GI食物，控制碳水化合物总量。主食粗细搭配，每餐主食量不超过一个拳头大小。多吃蔬菜，每餐蔬菜量占一餐饭量的一半。定时定量，少食多餐。",
                "metadata": {"category": "crowd_specific", "target_crowd": "糖尿病患者", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "健身人群膳食建议：训练日蛋白质摄入量1.6-2.2g/kg体重，碳水化合物5-7g/kg体重，脂肪0.8-1g/kg体重。训练后30分钟内补充蛋白质20-30g。保证充足水分，训练中每15-20分钟补水100-150ml。",
                "metadata": {"category": "crowd_specific", "target_crowd": "健身人群", "source": "运动营养学"}
            },
            {
                "content": "BMI健康标准（中国标准）：偏瘦<18.5，正常18.5-23.9，超重24-27.9，肥胖>=28。BMI计算公式：体重(kg)/身高(m)的平方。",
                "metadata": {"category": "health_standard", "source": "中国成人超重和肥胖症预防控制指南"}
            },
            {
                "content": "每日饮水建议：成人每天饮用1500-1700ml水，相当于7-8杯水。运动量大或高温环境下适当增加。建议少量多次饮用，不要等到口渴才喝水。",
                "metadata": {"category": "health_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "膳食纤维推荐摄入量：成人每天25-30g。膳食纤维有助于维持肠道健康，降低胆固醇，控制血糖。富含膳食纤维的食物：全谷物、杂豆、蔬菜、水果、坚果。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "钙推荐摄入量：成年人每天800mg，50岁以上老年人每天1000mg，孕妇和哺乳期女性每天1000-1200mg。富含钙的食物：奶制品、豆制品、绿叶蔬菜、小鱼干、芝麻酱。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "铁推荐摄入量：成年男性每天12mg，成年女性每天20mg，孕妇每天27mg。缺铁会导致贫血，表现为疲劳、乏力、头晕。富含铁的食物：红肉、动物肝脏、动物血制品、豆类、深绿色蔬菜。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "维生素D推荐摄入量：成年人每天10μg（400IU），65岁以上老年人每天15μg（600IU）。维生素D有助于钙吸收，缺乏会导致佝偻病和骨质疏松。晒太阳是获取维生素D的有效方式，每天10-20分钟。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "三大营养素供能比：碳水化合物50%-65%，蛋白质10%-15%，脂肪20%-30%。合理的供能比有助于维持身体健康和正常代谢。",
                "metadata": {"category": "nutrition_standard", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "常见主食GI值：白米饭73、白馒头88、白面包70、全麦面包50、燕麦42、糙米56、荞麦54、玉米55、小米71、红薯77、紫薯77、土豆64、莲藕38。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见水果GI值：苹果36、梨36、柚子25、草莓41、蓝莓53、葡萄43、桃子42、橙子43、香蕉52、菠萝66、芒果55、西瓜72、荔枝72、龙眼73。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见蔬菜GI值：菠菜15、西兰花15、黄瓜15、西红柿15、生菜15、芹菜15、胡萝卜39、南瓜75、豌豆48、扁豆35、魔芋17、藕38。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见豆类GI值：黄豆18、绿豆27、红豆26、鹰嘴豆30、扁豆35、黑豆18、豆腐30、豆浆16、扁豆35、四季豆27。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见奶制品GI值：牛奶27、酸奶36、脱脂牛奶32、全脂牛奶27、奶酪27、冰淇淋61。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见肉类蛋类GI值：鸡蛋14、鸭蛋14、鹌鹑蛋14、鸡肉0、牛肉0、猪肉0、鱼肉0、虾仁0。肉类蛋类不含碳水化合物，GI值为0。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见零食GI值：巧克力49、饼干70、蛋糕73、薯片75、爆米花72、蜜饯78、木糖醇12、麦芽糊精105、果糖19、乳糖46。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "常见饮料GI值：白开水0、无糖茶0、咖啡0、可乐43、雪碧42、橙汁46、苹果汁41、葡萄汁48、蜂蜜73。",
                "metadata": {"category": "food_knowledge", "source": "食物GI值表"}
            },
            {
                "content": "优质脂肪来源：橄榄油、茶籽油、核桃、杏仁、深海鱼（三文鱼、沙丁鱼）、牛油果。这些食物富含不饱和脂肪酸，有助于心血管健康。",
                "metadata": {"category": "food_knowledge", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "不良脂肪来源：油炸食品、肥肉、动物内脏、奶油蛋糕、薯片、方便面。这些食物富含饱和脂肪和反式脂肪，过量摄入增加心血管疾病风险。",
                "metadata": {"category": "food_knowledge", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "晚餐建议：晚餐应吃得清淡、适量，不宜过饱。晚餐时间建议在睡前3-4小时，避免影响睡眠。晚餐蛋白质和蔬菜占比可以适当提高，碳水化合物适当减少。",
                "metadata": {"category": "meal_guidance", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "早餐建议：早餐是一天中最重要的一餐，应包含主食、蛋白质、蔬菜或水果。营养均衡的早餐能提供上午所需能量，提高注意力和工作效率。",
                "metadata": {"category": "meal_guidance", "source": "中国居民膳食指南2022"}
            },
            {
                "content": "午餐建议：午餐应吃饱吃好，提供全天能量的40%左右。包含主食、优质蛋白质、多种蔬菜，保证营养均衡。",
                "metadata": {"category": "meal_guidance", "source": "中国居民膳食指南2022"}
            },
        ]

        documents = [item["content"] for item in health_knowledge]
        metadatas = [item["metadata"] for item in health_knowledge]
        ids = [f"health_{i}" for i in range(len(health_knowledge))]

        self.add(documents, metadatas, ids)
        _logger.info(f"已初始化健康知识库，共 {len(documents)} 条记录")


retriever = ChromaRetriever()