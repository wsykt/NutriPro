import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction
from vector.embedder import embedder
from config.settings import settings
from utils.retry_utils import chromadb_retry
from utils.retrieval_utils import BM25Retriever, hybrid_search
from utils.log_config import get_logger
import numpy as np

_logger = get_logger("retriever")


class BGEEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input):
        embeddings = embedder.encode(input)
        return embeddings.tolist()


class ChromaRetriever:

    # 语义去重窗口：仅对排名靠前的少量结果做两两 BGE 判重（避免 O(n²) 本地推理）
    DEDUP_TOP_WINDOW = 5
    # 轻量文本签名粗筛阈值（字符集 Jaccard ≥ 该值才调用 BGE 精确判重）
    LIGHT_SIMILARITY_PRE_FILTER = 0.5

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            "health_knowledge",
            embedding_function=BGEEmbeddingFunction()
        )
        self.MAX_CONTENT_LENGTH = 800
        self.DUPLICATE_SIMILARITY_THRESHOLD = 0.95
        self.MIN_SIMILARITY_THRESHOLD = 0.15

        # BM25 增量维护：待索引队列 + 脏索引标记。
        # add() 只把新文档挂入队列并打脏标记，检索前才合并重建一次，
        # 避免批量摄入时每次 add 都全量 get+重建（O(N²) → O(N)）。
        self._bm25_dirty = False
        self._bm25_pending = {"documents": [], "metadatas": []}

        # BM25 检索器（初始化时从向量库加载数据建索引）
        self.bm25 = BM25Retriever()
        self._build_bm25_index()

    def _build_bm25_index(self):
        """从 ChromaDB 中加载全部文档构建 BM25 索引"""
        try:
            total = self.count()
            if total > 0:
                all_data = self.collection.get(include=["documents", "metadatas"])
                documents = all_data.get("documents", []) or []
                metadatas = all_data.get("metadatas", []) or []
                if documents:
                    self.bm25.index(documents, metadatas)
                    _logger.info(f"BM25 索引已建立，共 {len(documents)} 条记录")
        except Exception as e:
            _logger.warning(f"BM25 索引建立失败（非关键错误）: {e}")

    @chromadb_retry
    def search(self, query, top_k=3, target_crowd=None):
        query_vec = embedder.encode_query(query).tolist()
        
        where = None
        if target_crowd and target_crowd != "普通人":
            where = {"$or": [
                {"target_crowd": target_crowd},
                {"category": {"$in": ["dietary_guideline", "nutrition_standard", "health_standard", "food_knowledge", "meal_guidance"]}}
            ]}
        
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=top_k * 2,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        
        raw_results = [{
            "content": results["documents"][0][i],
            "similarity": 1 - results["distances"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
        } for i in range(len(results["documents"][0]))]
        
        raw_results = sorted(raw_results, key=lambda x: x["similarity"], reverse=True)
        # 过滤极低相似度结果（但仍保留 MIN_SIMILARITY_THRESHOLD 以上的结果）
        raw_results = [r for r in raw_results if r["similarity"] >= self.MIN_SIMILARITY_THRESHOLD]
        filtered_results = self._deduplicate_results(raw_results)
        
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

    def _content_similarity(self, text1, text2):
        """基于 BGE 向量的余弦相似度（替代脆弱的 Jaccard 字符集方法）"""
        if not text1 or not text2:
            return 0.0
        try:
            vecs = embedder.encode([text1[:500], text2[:500]])
            v1, v2 = vecs[0], vecs[1]
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

    def hybrid_retrieve(self, query, top_k=5, target_crowd=None):
        """BM25 + 向量双路融合检索（单路异常可降级）"""
        # 检索前合并重建 BM25 索引（批量摄入后仅在此处重建一次）
        self._rebuild_bm25_if_dirty()

        def vector_search_fn(q, top_k=top_k):
            return self.search(q, top_k=top_k, target_crowd=target_crowd)

        try:
            from utils.retrieval_utils import hybrid_search as _hybrid_search
            return _hybrid_search(
                query=query,
                vector_search_fn=vector_search_fn,
                bm25_retriever=self.bm25,
                top_k=top_k,
                vector_weight=0.6,
                bm25_weight=0.4,
            )
        except Exception as e:
            _logger.warning(f"混合检索降级为纯向量检索: {e}")
            return vector_search_fn(query, top_k)

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
        embeddings = embedder.encode(documents).tolist()
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )
        # 同时更新 BM25 索引（增量：挂入待索引队列并打脏标记，
        # 检索前合并重建一次，避免每次 add 都全量 get+重建）
        self._mark_bm25_dirty(documents, metadatas)
        # 双写一致性：ai_template 卡片同步写入 SQLite 模板库（权威副本）
        self._dual_write_templates(documents, metadatas, ids)

    def _mark_bm25_dirty(self, documents, metadatas=None):
        """把新文档挂入 BM25 待索引队列并打脏标记（不立即重建索引）。

        批量摄入时（连续多次 add）只在首次检索前合并重建一次，
        将每次 add 的 O(N) 全量 get+重建 降为 O(1) 收集 + 单次 O(N) 重建。
        """
        self._bm25_dirty = True
        self._bm25_pending["documents"].extend(documents or [])
        self._bm25_pending["metadatas"].extend(metadatas or [])

    def _rebuild_bm25_if_dirty(self):
        """检索前合并重建 BM25 索引（脏标记置位时执行）：
        把累积的待索引文档并入旧索引后一次性重建；失败则保持脏标记下次再试。
        """
        if not self._bm25_dirty:
            return
        self._bm25_dirty = False
        try:
            pending_docs = self._bm25_pending.get("documents") or []
            pending_metas = self._bm25_pending.get("metadatas") or []
            self._bm25_pending = {"documents": [], "metadatas": []}
            if not pending_docs:
                return
            # BM25Retriever 为全量 index 实现，采用「旧索引 + 待索引」合并重建
            old_docs = self.bm25._documents if self.bm25._is_indexed else []
            old_metas = self.bm25._doc_metadatas if self.bm25._is_indexed else []
            self.bm25.index(old_docs + pending_docs, (old_metas or []) + pending_metas)
            _logger.info(
                f"BM25 索引合并重建完成（本次新增 {len(pending_docs)} 条，"
                f"共 {len(old_docs) + len(pending_docs)} 条）")
        except Exception as e:
            _logger.warning(f"BM25 索引合并重建失败（非关键错误）: {e}")
            self._bm25_dirty = True  # 失败恢复脏标记，下次检索再试

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
        """获取双层存储的完整备份内容（无备份时返回 document 本身）"""
        try:
            result = self.collection.get(ids=[doc_id], include=["documents", "metadatas"])
            if not result["ids"]:
                return ""
            meta = result["metadatas"][0] or {}
            if meta.get("has_backup") and meta.get("full_content"):
                return meta["full_content"]
            return result["documents"][0]
        except Exception as e:
            _logger.warning(f"获取完整内容失败: {e}")
            return ""

    def count(self):
        return self.collection.count()

    def clear(self):
        self.client.delete_collection("health_knowledge")
        self.collection = self.client.get_or_create_collection(
            "health_knowledge",
            embedding_function=BGEEmbeddingFunction()
        )
        # 同步清空 BM25 索引与待索引队列（避免合并重建时混入已删除文档）
        self.bm25.index([], [])
        self._bm25_pending = {"documents": [], "metadatas": []}
        self._bm25_dirty = False

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
            all_data = self.collection.get(include=["documents", "metadatas"])
            metadatas = all_data.get("metadatas", []) or []
            docs = all_data.get("documents", []) or []

            # 分类分布
            from collections import Counter
            cats = Counter(m.get("category", "unknown") for m in metadatas)
            stats["categories"] = dict(cats.most_common())

            # 来源分布
            srcs = Counter(m.get("source", "未知") for m in metadatas)
            stats["sources"] = dict(srcs.most_common())

            # 人群分布
            crowds = Counter(m.get("target_crowd", "") for m in metadatas if m.get("target_crowd"))
            stats["crowd_distribution"] = dict(crowds.most_common())

            # 内容长度统计
            lengths = sorted(len(d) for d in docs)
            if lengths:
                stats["content_stats"] = {
                    "min_len": min(lengths),
                    "max_len": max(lengths),
                    "avg_len": round(sum(lengths) / len(lengths), 1),
                    "median_len": lengths[len(lengths) // 2],
                }

            # 样本条目
            for i in range(min(5, len(docs))):
                stats["sample_entries"].append({
                    "content_preview": docs[i][:100] + ("..." if len(docs[i]) > 100 else ""),
                    "category": metadatas[i].get("category", ""),
                    "source": metadatas[i].get("source", ""),
                })
        except Exception:
            pass

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