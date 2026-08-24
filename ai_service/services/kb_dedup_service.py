# -*- coding: utf-8 -*-
"""知识库四层去重服务（漏斗模型）

层1: 元数据硬过滤 —— func_type + 人群 + BMI 档位全部一致才视为候选
层2: 语义相似度判定 —— BGE 向量余弦相似度替代脆弱的 Jaccard 字符集方法
层3: 分级合并策略 —— 高相似(≥0.75)→云端合并；中相似(≥0.50)→标记变体；低相似→新增
层4: 双层存储入库 —— 精简展示版+完整备份版（保留核心结论原文，防大模型歧义）

设计原则：
- 比赛阶段不删除冷数据（KB_AUTO_COLD_CLEANUP=false），仅保留接口
- 核心结论保留原文，不做精简改写，降低大模型幻觉/歧义风险
"""
import json
import time
import uuid
import enum
from typing import List, Optional, Tuple, Any
from utils.log_config import get_logger

logger = get_logger("kb_dedup")


class MergeStrategy(enum.Enum):
    """去重分级策略"""
    REJECT = "reject"           # 完全相同 → 丢弃，仅更新元数据
    CLOUD_MERGE = "cloud_merge" # 高相似 → 云端整合合并
    MARK_VARIANT = "variant"    # 中相似 → 标记为同主题变体
    INGEST_NEW = "new"          # 低相似/无候选 → 新增入库


class DedupResult:
    """去重判定结果"""
    def __init__(self, strategy: MergeStrategy, best_match: dict = None,
                 similarity: float = 0.0, candidates: list = None):
        self.strategy = strategy
        self.best_match = best_match or {}
        self.similarity = similarity
        self.candidates = candidates or []

    @property
    def has_match(self) -> bool:
        return bool(self.best_match)

    def __repr__(self):
        return f"DedupResult(strategy={self.strategy.value}, sim={self.similarity:.3f}, candidates={len(self.candidates)})"


class KBDedupService:
    """知识库四层去重服务"""

    def __init__(self, retriever, embedder=None, llm=None):
        self.retriever = retriever
        self.embedder = embedder
        self.llm = llm
        # 从 settings 读取阈值
        from config.settings import settings
        self.high_threshold = settings.KB_DEDUP_HIGH_THRESHOLD       # 0.75
        self.medium_threshold = settings.KB_DEDUP_MEDIUM_THRESHOLD   # 0.50
        self.dedup_threshold = settings.KB_DUP_SIMILARITY_THRESHOLD # 0.45
        self.top_k = settings.KB_DEDUP_TOP_K_CANDIDATES             # 5
        self.dual_layer = settings.KB_DUAL_LAYER_STORAGE
        self.content_max = settings.KB_CONTENT_MAX_LENGTH           # 500
        self.display_max = settings.KB_CONTENT_DISPLAY_LENGTH       # 200

    def check_and_ingest(self, func_type: str, result: Any,
                         trigger_route: str, build_ingest_doc_fn,
                         merge_with_cloud_fn, **kwargs) -> dict:
        """完整的去重+入库流程：
        1. 查询候选集（元数据预过滤 + 向量检索）
        2. 判定去重策略
        3. 按策略执行：合并/标记变体/新增
        4. 双层存储入库

        Returns: {"action": "merged"|"variant"|"new"|"rejected", "id": str, "similarity": float}
        """
        if not self.retriever:
            return {"action": "skipped", "id": "", "similarity": 0}

        # 1) 空结果不入库
        if result is None:
            return {"action": "skipped", "id": "", "similarity": 0}
        if isinstance(result, str) and len(result.strip()) < 20:
            return {"action": "skipped", "id": "", "similarity": 0}
        if isinstance(result, dict) and not result:
            return {"action": "skipped", "id": "", "similarity": 0}

        # 2) 查询候选集
        dedup = self._find_candidates(func_type, **kwargs)

        # 3) 按策略执行
        if dedup.strategy == MergeStrategy.REJECT:
            # 完全相同 → 仅更新命中次数
            logger.info(f"[去重] 完全重复，跳过入库 sim={dedup.similarity:.3f}")
            return {"action": "rejected", "id": "", "similarity": dedup.similarity}

        elif dedup.strategy == MergeStrategy.CLOUD_MERGE:
            # 高相似 → 云端合并
            old_content = dedup.best_match.get("content", "")
            old_meta = dict(dedup.best_match.get("metadata", {}) or {})
            old_id = dedup.best_match.get("id", "")  # 可能没有 id 字段

            merged_doc = merge_with_cloud_fn(func_type, old_content, result, **kwargs)

            # 更新元数据
            old_meta.update({
                "template_type": "ai_template",
                "func_type": old_meta.get("func_type") or func_type,
                "merged_from": json.dumps([{
                    "reason": "duplicate_topic_merge",
                    "trigger_route": trigger_route,
                    "merge_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "old_similarity": round(dedup.similarity, 3),
                }], ensure_ascii=False),
                "ingest_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": str(float(old_meta.get("version", "1.0") or "1.0") + 0.1),
                "source": old_meta.get("source", "") + f"+merged_with_{trigger_route}",
            })
            old_meta = {k: v for k, v in old_meta.items() if v is not None and str(v) != ""}

            new_id = f"live_merge_{func_type}_{int(time.time())}_{uuid.uuid4().hex[:6]}"

            # 双层存储：合并文档可能较长，拆分为展示版+完整版
            display_doc, full_doc = self._split_dual_layer(merged_doc)
            if self.dual_layer and full_doc:
                self.retriever.add_with_backup(display_doc, full_doc, old_meta, new_id)
            else:
                self.retriever.add(documents=[merged_doc], metadatas=[old_meta], ids=[new_id])

            logger.info(f"[去重-合并] id={new_id} sim={dedup.similarity:.3f} dual_layer={bool(full_doc)}")
            return {"action": "merged", "id": new_id, "similarity": dedup.similarity}

        elif dedup.strategy == MergeStrategy.MARK_VARIANT:
            # 中相似 → 新增但标记为变体
            doc, meta, cid = build_ingest_doc_fn(func_type, result, **kwargs)
            meta["variant_of"] = dedup.best_match.get("metadata", {}).get("topic", "")
            meta["variant_similarity"] = round(dedup.similarity, 3)

            display_doc, full_doc = self._split_dual_layer(doc)
            if self.dual_layer and full_doc:
                self.retriever.add_with_backup(display_doc, full_doc, meta, cid)
            else:
                self.retriever.add(documents=[doc], metadatas=[meta], ids=[cid])

            logger.info(f"[去重-变体] id={cid} sim={dedup.similarity:.3f} variant_of={meta.get('variant_of','')}")
            return {"action": "variant", "id": cid, "similarity": dedup.similarity}

        else:
            # 新增入库
            doc, meta, cid = build_ingest_doc_fn(func_type, result, **kwargs)

            display_doc, full_doc = self._split_dual_layer(doc)
            if self.dual_layer and full_doc:
                self.retriever.add_with_backup(display_doc, full_doc, meta, cid)
            else:
                self.retriever.add(documents=[doc], metadatas=[meta], ids=[cid])

            logger.info(f"[去重-新增] id={cid} sim={dedup.similarity:.3f}")
            return {"action": "new", "id": cid, "similarity": dedup.similarity}

    def _find_candidates(self, func_type: str, **kwargs) -> DedupResult:
        """层1+层2: 元数据预过滤 + 向量检索候选集 + 语义相似度判定"""
        from local_fallback_engine import crowd_kb_name

        # 构造查询
        match_query = self._build_match_query(func_type, **kwargs)
        if not match_query or len(match_query.strip()) < 3:
            return DedupResult(MergeStrategy.INGEST_NEW)

        # 提取结构化元数据
        crowd, goal, up, bmi_id, bmi_cn = self._extract_crowd_and_goal(func_type, **kwargs)
        kb_crowd = crowd_kb_name(crowd)

        # 层1: 元数据预过滤检索
        try:
            hits = self.retriever.search(match_query, top_k=self.top_k, target_crowd=kb_crowd)
        except Exception as e:
            logger.debug(f"[去重查询失败] {e}")
            hits = []

        if not hits:
            return DedupResult(MergeStrategy.INGEST_NEW)

        # 层2: 结构化一致性检查 + 语义相似度排序
        valid_candidates = []
        for h in hits:
            meta = h.get("metadata", {}) or {}
            # 结构化硬过滤
            if not self._is_same_topic(meta, func_type, kb_crowd, bmi_id):
                continue
            valid_candidates.append(h)

        if not valid_candidates:
            return DedupResult(MergeStrategy.INGEST_NEW)

        # 取最高相似度候选
        best = max(valid_candidates, key=lambda x: x.get("similarity", 0))
        best_sim = best.get("similarity", 0)

        # 层3: 分级策略判定
        if best_sim >= 0.95:
            strategy = MergeStrategy.REJECT
        elif best_sim >= self.high_threshold:
            strategy = MergeStrategy.CLOUD_MERGE
        elif best_sim >= self.medium_threshold:
            strategy = MergeStrategy.MARK_VARIANT
        else:
            strategy = MergeStrategy.INGEST_NEW

        return DedupResult(strategy, best, best_sim, valid_candidates)

    def _is_same_topic(self, meta: dict, func_type: str, crowd_kb: str, bmi_id: str) -> bool:
        """结构化判定：func_type + 人群 + BMI 档位全部一致"""
        if not isinstance(meta, dict):
            return False
        if meta.get("func_type") and meta.get("func_type") != func_type:
            return False
        if crowd_kb and meta.get("target_crowd") and meta.get("target_crowd") != crowd_kb:
            return False
        if bmi_id and meta.get("bmi_id") and meta.get("bmi_id") != bmi_id:
            return False
        return True

    def _split_dual_layer(self, doc: str) -> Tuple[str, str]:
        """双层存储拆分：
        - display_doc: 精简展示版（≤ display_max 字），用于向量检索
        - full_doc: 完整备份版，保留核心结论原文，用于大模型改写/分析
        核心结论原文不截断（保留【标题】【目标】【核心结论】等关键段落完整）
        """
        if not self.dual_layer or len(doc) <= self.display_max:
            return doc, ""

        # 保留前 display_max 字作为展示版
        display = doc[:self.display_max]
        # 确保不截断在关键标记中间
        for marker in ["\n【", "\n\n", "。"]:
            cut_pos = display.rfind(marker)
            if cut_pos > self.display_max * 0.7:
                display = display[:cut_pos + len(marker)]
                break

        return display, doc

    def _build_match_query(self, func_type: str, **kwargs) -> str:
        """构造去重查询"""
        from local_fallback_engine import crowd_display_name
        if func_type == "qa":
            return kwargs.get("question", "")
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {}) or {}
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')} {kwargs.get('goal','')} 一日膳食方案 BMI={up.get('bmi','')}"
        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", []) or []
            return f"{crowd_display_name(kwargs.get('crowd_type',''))} {kwargs.get('goal','')} 食材菜谱推荐 {' '.join(list(ings)[:3])}"
        else:
            up = kwargs.get("user_profile", {}) or {}
            chronic = " ".join(kwargs.get("chronic_diseases") or [])
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')} {kwargs.get('goal','')} {chronic} 一周运动方案"

    def _extract_crowd_and_goal(self, func_type: str, **kwargs) -> tuple:
        """从 kwargs 解析人群/BMI（复用 mode_router 逻辑的简化版）"""
        from local_fallback_engine import canonical_crowd
        up = {}
        crowd = "通用"
        goal = "保持健康"

        if func_type == "qa":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = (kwargs.get("question", "") or "")[:20] or "健康问答"
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = kwargs.get("goal", "") or "均衡饮食"
        elif func_type == "food_recommend":
            crowd = canonical_crowd(kwargs.get("crowd_type", "通用"))
            goal = (kwargs.get("goal", "") or "健康饮食")[:20]
        elif func_type == "exercise":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = kwargs.get("goal", "") or "保持健康"

        bmi_val = up.get("bmi") if isinstance(up, dict) else None
        if bmi_val and isinstance(bmi_val, (int, float)):
            if bmi_val < 18.5:
                bmi_id, bmi_cn = "very_low", "过低"
            elif bmi_val < 20:
                bmi_id, bmi_cn = "low", "偏低"
            elif bmi_val < 24:
                bmi_id, bmi_cn = "normal", "正常"
            elif bmi_val < 28:
                bmi_id, bmi_cn = "high", "偏高"
            else:
                bmi_id, bmi_cn = "very_high", "超高"
        else:
            bmi_id, bmi_cn = "normal", "正常"

        return crowd, goal, up if isinstance(up, dict) else {}, bmi_id, bmi_cn

    def check_relevance_with_local_llm(self, user_question: str, generated_answer: str,
                                        kb_context: str = "") -> dict:
        """本地大模型相关性校验：
        不看知识库，单纯判断用户问题与最终回答是否相关。
        可选传入 kb_context 做一致性检查。

        Returns: {"relevant": bool, "confidence": float, "reason": str}
        """
        if not self.llm:
            return {"relevant": True, "confidence": 0.0, "reason": "无本地LLM，跳过校验"}

        prompt = (
            "请判断以下用户问题与AI回答是否相关。只回答JSON格式：\n"
            '{"relevant": true/false, "confidence": 0.0-1.0, "reason": "简短原因"}\n\n'
            f"【用户问题】{user_question[:300]}\n\n"
            f"【AI回答】{generated_answer[:500]}\n"
        )
        if kb_context:
            prompt += f"\n【知识库参考内容】{kb_context[:300]}\n"

        try:
            # mode 参数局部生效，避免改写共享 _mode 造成并发串台
            result = self.llm.chat_json(prompt, temperature=0.1, mode="local")

            if isinstance(result, dict) and "relevant" in result:
                return result
            return {"relevant": True, "confidence": 0.5, "reason": "校验结果解析失败，默认通过"}
        except Exception as e:
            logger.debug(f"[相关性校验失败] {e}")
            return {"relevant": True, "confidence": 0.0, "reason": f"校验异常: {e}"}

    # ============================================================
    # 文献卡片专用四层去重入库（供 crawler/literature_enrich_v2 使用）
    # 维度与模板卡片不同：group + topic 做元数据硬过滤，而非 func_type+BMI
    # ============================================================

    def check_literature_ingest(self, card: dict, display_doc: str, full_doc: str,
                                meta: dict, doc_id: str) -> dict:
        """文献卡片四层去重入库：
        层1: group + topic 元数据硬过滤（只与同人群同主题的文献卡比较）
        层2: BGE 向量余弦相似度（复用 retriever.search 返回的 similarity）
        层3: 分级策略 —— 文献卡保持单一来源可追溯，高相似直接丢弃；中相似标记变体
        层4: 双层存储入库（add_with_backup）

        Returns: {"action": "new"|"variant"|"rejected", "id": str, "similarity": float}
        """
        if not self.retriever:
            return {"action": "skipped", "id": doc_id, "similarity": 0}

        group = card.get("group", "普通人") or "普通人"
        topic = card.get("topic", "") or ""
        query = f"{group} {topic} {card.get('title', '')}"

        try:
            hits = self.retriever.search(query, top_k=self.top_k)
        except Exception as e:
            logger.debug(f"[文献去重查询失败] {e}")
            hits = []

        # 层1: 元数据硬过滤
        best_sim = 0.0
        for h in hits:
            m = h.get("metadata", {}) or {}
            if m.get("source_type") != "literature":
                continue
            if group and m.get("group") and m.get("group") != group:
                continue
            if topic and m.get("topic") and m.get("topic") != topic:
                continue
            sim = h.get("similarity", 0) or 0
            if sim > best_sim:
                best_sim = sim

        # 层3: 分级策略
        if best_sim >= self.high_threshold:
            # 高相似重复文献：直接丢弃，不合并（文献卡保持单一来源可追溯）
            logger.info(f"[文献去重-重复] drop id={doc_id} sim={best_sim:.3f} topic={topic}")
            return {"action": "rejected", "id": doc_id, "similarity": best_sim}

        action = "new"
        if best_sim >= self.medium_threshold:
            # 中相似 → 标记为同主题变体后入库
            meta["variant_of"] = topic
            meta["variant_similarity"] = round(best_sim, 3)
            action = "variant"

        # 层4: 双层存储入库
        if self.dual_layer and full_doc:
            self.retriever.add_with_backup(display_doc, full_doc, meta, doc_id)
        else:
            self.retriever.add(documents=[display_doc], metadatas=[meta], ids=[doc_id])

        logger.info(f"[文献去重-{action}] id={doc_id} sim={best_sim:.3f} dual_layer={bool(full_doc)}")
        return {"action": action, "id": doc_id, "similarity": best_sim}
