# -*- coding: utf-8 -*-
"""知识库四层去重 / 双层存储 / 本地相关性校验 单元测试

验证范围：
1. KBDedupService 初始化与配置加载
2. 层1 元数据硬过滤（func_type + 人群 + BMI 档位不一致 → 直接新增）
3. 层2 语义相似度判定（BGE 向量余弦）
4. 层3 分级合并策略：
   - 完全重复(≥0.95) → REJECT
   - 高相似(≥0.75)   → CLOUD_MERGE（调用云端合并）
   - 中相似(≥0.50)   → MARK_VARIANT（标记变体后入库）
   - 低相似           → INGEST_NEW（新增入库）
5. 层4 双层存储：add_with_backup / get_full_content
6. 本地大模型相关性校验 check_relevance_with_local_llm
7. mode_router 集成：_apply_relevance_check 注入 validation.relevance

使用 Mock 避免真实 LLM / ChromaDB 调用，仅测逻辑分发。
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# 确保 health/ai_service 在路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _make_hit(content="测试内容", similarity=0.6, metadata=None):
    """构造一条检索命中结果"""
    return {
        "content": content,
        "similarity": similarity,
        "metadata": metadata or {
            "func_type": "qa",
            "target_crowd": "糖尿病患者",
            "bmi_id": "normal",
            "topic": "糖尿病-BMI正常-健康问答",
        },
    }


class TestKBDedupInit(unittest.TestCase):
    """去重服务初始化与配置加载"""

    def test_init_loads_settings(self):
        from services.kb_dedup_service import KBDedupService, MergeStrategy
        from config.settings import settings
        mock_ret = MagicMock()
        svc = KBDedupService(retriever=mock_ret, llm=MagicMock())
        self.assertEqual(svc.high_threshold, settings.KB_DEDUP_HIGH_THRESHOLD)
        self.assertEqual(svc.medium_threshold, settings.KB_DEDUP_MEDIUM_THRESHOLD)
        self.assertEqual(svc.dedup_threshold, settings.KB_DUP_SIMILARITY_THRESHOLD)
        self.assertEqual(svc.top_k, settings.KB_DEDUP_TOP_K_CANDIDATES)
        self.assertTrue(svc.dual_layer)
        self.assertGreater(svc.content_max, 0)
        self.assertGreater(svc.display_max, 0)

    def test_merge_strategy_enum_values(self):
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(MergeStrategy.REJECT.value, "reject")
        self.assertEqual(MergeStrategy.CLOUD_MERGE.value, "cloud_merge")
        self.assertEqual(MergeStrategy.MARK_VARIANT.value, "variant")
        self.assertEqual(MergeStrategy.INGEST_NEW.value, "new")


class TestFindCandidates(unittest.TestCase):
    """层1+层2 候选集筛选与分级策略判定"""

    def setUp(self):
        from services.kb_dedup_service import KBDedupService
        self.svc = KBDedupService(retriever=MagicMock(), llm=MagicMock())
        self.svc.top_k = 5

    def test_no_query_returns_new(self):
        """空查询 → INGEST_NEW"""
        dedup = self.svc._find_candidates("qa", question="")
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_no_hits_returns_new(self):
        """检索无命中 → INGEST_NEW"""
        self.svc.retriever.search.return_value = []
        dedup = self.svc._find_candidates("qa", question="高血压吃什么好？",
                                          user_profile={"crowd_type": "高血压"})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_metadata_filter_diff_func(self):
        """func_type 不一致 → 过滤掉，无候选 → INGEST_NEW"""
        hit = _make_hit(metadata={"func_type": "diet_plan", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食",
                                          user_profile={"crowd_type": "糖尿病"})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_metadata_filter_diff_crowd(self):
        """人群不一致 → 过滤掉"""
        hit = _make_hit(metadata={"func_type": "qa", "target_crowd": "健身人群", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食",
                                          user_profile={"crowd_type": "糖尿病"})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_metadata_filter_diff_bmi(self):
        """BMI 档位不一致 → 过滤掉"""
        hit = _make_hit(metadata={"func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "high"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_high_similarity_triggers_cloud_merge(self):
        """高相似(0.80≥0.75) → CLOUD_MERGE"""
        hit = _make_hit(similarity=0.80, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食建议",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.CLOUD_MERGE)
        self.assertAlmostEqual(dedup.similarity, 0.80, places=2)

    def test_medium_similarity_triggers_variant(self):
        """中相似(0.60≥0.50<0.75) → MARK_VARIANT"""
        hit = _make_hit(similarity=0.60, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食建议",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.MARK_VARIANT)

    def test_low_similarity_triggers_new(self):
        """低相似(0.47<0.50) → INGEST_NEW"""
        hit = _make_hit(similarity=0.47, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食建议",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.INGEST_NEW)

    def test_near_identical_triggers_reject(self):
        """完全重复(≥0.95) → REJECT"""
        hit = _make_hit(similarity=0.96, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [hit]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食建议",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        from services.kb_dedup_service import MergeStrategy
        self.assertEqual(dedup.strategy, MergeStrategy.REJECT)

    def test_picks_highest_similarity_candidate(self):
        """多个候选时取最高相似度"""
        h1 = _make_hit(similarity=0.55, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        h2 = _make_hit(similarity=0.78, metadata={
            "func_type": "qa", "target_crowd": "糖尿病患者", "bmi_id": "normal"})
        self.svc.retriever.search.return_value = [h1, h2]
        dedup = self.svc._find_candidates("qa", question="糖尿病饮食建议",
                                          user_profile={"crowd_type": "糖尿病", "bmi": 22.0})
        self.assertAlmostEqual(dedup.similarity, 0.78, places=2)


class TestCheckAndIngest(unittest.TestCase):
    """check_and_ingest 全流程：按策略执行入库"""

    def setUp(self):
        from services.kb_dedup_service import KBDedupService
        self.svc = KBDedupService(retriever=MagicMock(), llm=MagicMock())
        # 构造超过 display_max(200字) 的长文档，确保触发双层存储拆分
        long_doc = "【标题】测试卡片\n" + "核心结论：糖尿病饮食应控制碳水总量，选择低GI食物，多吃蔬菜，定时定量少食多餐。" * 5
        # build_ingest_doc 回调：返回 (document, metadata, card_id)
        self.build_fn = MagicMock(return_value=(
            long_doc,
            {"func_type": "qa", "target_crowd": "糖尿病患者", "topic": "test"},
            "card_001",
        ))
        # merge_with_cloud 回调：返回合并后长文本（触发双层存储，>display_max=200字）
        long_merge = "【标题】[整合版] 合并后的卡片内容，" + "整合了新旧两份模板的差异化信息，保留核心结论原文，按合理顺序重排，冲突数据取新值并加注释。" * 6
        self.merge_fn = MagicMock(return_value=long_merge)

    def test_reject_strategy_skips_ingest(self):
        """REJECT 策略：不入库，仅返回 rejected"""
        with patch.object(self.svc, "_find_candidates") as mock_find:
            from services.kb_dedup_service import DedupResult, MergeStrategy
            mock_find.return_value = DedupResult(
                MergeStrategy.REJECT, _make_hit(similarity=0.96), 0.96)
            res = self.svc.check_and_ingest(
                "qa", "这是一段足够长的回答内容用于测试去重逻辑。",
                "C_direct", self.build_fn, self.merge_fn,
                question="糖尿病吃什么", user_profile={"crowd_type": "糖尿病"})
        self.assertEqual(res["action"], "rejected")
        self.svc.retriever.add_with_backup.assert_not_called()
        self.svc.retriever.add.assert_not_called()

    def test_cloud_merge_strategy_calls_merge_and_dual_layer(self):
        """CLOUD_MERGE：调用云端合并 + 双层存储入库"""
        with patch.object(self.svc, "_find_candidates") as mock_find:
            from services.kb_dedup_service import DedupResult, MergeStrategy
            mock_find.return_value = DedupResult(
                MergeStrategy.CLOUD_MERGE, _make_hit(similarity=0.80), 0.80)
            res = self.svc.check_and_ingest(
                "qa", "这是一段足够长的回答内容用于测试合并去重逻辑流程。",
                "C_direct", self.build_fn, self.merge_fn,
                question="糖尿病吃什么", user_profile={"crowd_type": "糖尿病"})
        self.assertEqual(res["action"], "merged")
        self.merge_fn.assert_called_once()
        # 双层存储开启时应调用 add_with_backup
        self.svc.retriever.add_with_backup.assert_called_once()

    def test_variant_strategy_marks_variant(self):
        """MARK_VARIANT：新增但标记 variant_of"""
        with patch.object(self.svc, "_find_candidates") as mock_find:
            from services.kb_dedup_service import DedupResult, MergeStrategy
            mock_find.return_value = DedupResult(
                MergeStrategy.MARK_VARIANT, _make_hit(similarity=0.60), 0.60)
            res = self.svc.check_and_ingest(
                "qa", "这是一段足够长的回答内容用于测试变体标记逻辑流程。",
                "C_direct", self.build_fn, self.merge_fn,
                question="糖尿病吃什么", user_profile={"crowd_type": "糖尿病"})
        self.assertEqual(res["action"], "variant")
        self.build_fn.assert_called_once()
        # 校验 metadata 里写了 variant_of
        call_kwargs = self.svc.retriever.add_with_backup.call_args
        meta = call_kwargs.args[2]
        self.assertIn("variant_of", meta)

    def test_new_strategy_ingests(self):
        """INGEST_NEW：直接新增入库"""
        with patch.object(self.svc, "_find_candidates") as mock_find:
            from services.kb_dedup_service import DedupResult, MergeStrategy
            mock_find.return_value = DedupResult(MergeStrategy.INGEST_NEW)
            res = self.svc.check_and_ingest(
                "qa", "这是一段足够长的回答内容用于测试新增入库逻辑流程。",
                "C_direct", self.build_fn, self.merge_fn,
                question="糖尿病吃什么", user_profile={"crowd_type": "糖尿病"})
        self.assertEqual(res["action"], "new")
        self.build_fn.assert_called_once()
        self.svc.retriever.add_with_backup.assert_called_once()

    def test_empty_result_skipped(self):
        """空结果 → skipped"""
        res = self.svc.check_and_ingest(
            "qa", "", "C_direct", self.build_fn, self.merge_fn, question="x")
        self.assertEqual(res["action"], "skipped")
        res = self.svc.check_and_ingest(
            "qa", {}, "C_direct", self.build_fn, self.merge_fn, question="x")
        self.assertEqual(res["action"], "skipped")

    def test_no_retriever_skipped(self):
        """无 retriever → skipped"""
        from services.kb_dedup_service import KBDedupService
        svc = KBDedupService(retriever=None, llm=MagicMock())
        res = svc.check_and_ingest(
            "qa", "有内容", "C_direct", self.build_fn, self.merge_fn, question="x")
        self.assertEqual(res["action"], "skipped")


class TestSplitDualLayer(unittest.TestCase):
    """双层存储拆分逻辑"""

    def setUp(self):
        from services.kb_dedup_service import KBDedupService
        self.svc = KBDedupService(retriever=MagicMock(), llm=MagicMock())
        self.svc.display_max = 200

    def test_short_doc_no_split(self):
        """短文档（≤display_max）不拆分，full_doc 为空"""
        short = "【标题】短卡片\n这是一段简短内容。"
        display, full = self.svc._split_dual_layer(short)
        self.assertEqual(display, short)
        self.assertEqual(full, "")

    def test_long_doc_split(self):
        """长文档拆分为展示版+完整版，完整版保留原文"""
        long_doc = "【标题】长卡片\n" + ("核心结论：每日蛋白质摄入应达到1.2g/kg。" * 30)
        display, full = self.svc._split_dual_layer(long_doc)
        self.assertLessEqual(len(display), self.svc.display_max + 20)
        self.assertEqual(full, long_doc)  # 完整版保留原文

    def test_dual_layer_disabled(self):
        """双层存储关闭时返回原文，无 full_doc"""
        self.svc.dual_layer = False
        long_doc = "【标题】卡片\n" + "内容" * 200
        display, full = self.svc._split_dual_layer(long_doc)
        self.assertEqual(display, long_doc)
        self.assertEqual(full, "")


class TestRelevanceCheck(unittest.TestCase):
    """本地大模型相关性校验"""

    def setUp(self):
        from services.kb_dedup_service import KBDedupService
        self.svc = KBDedupService(retriever=MagicMock(), llm=MagicMock())

    def test_no_llm_returns_pass(self):
        """无 LLM → 默认通过"""
        self.svc.llm = None
        rel = self.svc.check_relevance_with_local_llm("高血压吃什么", "建议限盐多运动")
        self.assertTrue(rel["relevant"])

    def test_relevant_answer(self):
        """相关问题相关回答 → relevant=True"""
        self.svc.llm.chat_json.return_value = {
            "relevant": True, "confidence": 0.9, "reason": "回答直接针对问题"}
        rel = self.svc.check_relevance_with_local_llm("高血压吃什么好", "建议低盐饮食，多吃蔬菜")
        self.assertTrue(rel["relevant"])
        self.assertGreater(rel["confidence"], 0.5)

    def test_irrelevant_answer(self):
        """答非所问 → relevant=False"""
        self.svc.llm.chat_json.return_value = {
            "relevant": False, "confidence": 0.85, "reason": "回答与问题无关"}
        rel = self.svc.check_relevance_with_local_llm("高血压吃什么好", "今天天气晴朗适合跑步")
        self.assertFalse(rel["relevant"])

    def test_llm_exception_returns_pass(self):
        """LLM 异常 → 默认通过，不阻断主流程"""
        self.svc.llm.chat_json.side_effect = Exception("Ollama 离线")
        rel = self.svc.check_relevance_with_local_llm("高血压吃什么", "建议限盐")
        self.assertTrue(rel["relevant"])

    def test_malformed_result_returns_pass(self):
        """LLM 返回非标准格式 → 默认通过"""
        self.svc.llm.chat_json.return_value = "这不是一个字典"
        rel = self.svc.check_relevance_with_local_llm("问题", "回答")
        self.assertTrue(rel["relevant"])

    def test_uses_local_mode(self):
        """相关性校验应强制使用本地模式"""
        self.svc.llm._mode = "cloud"
        self.svc.llm.chat_json.return_value = {"relevant": True, "confidence": 0.9, "reason": "ok"}
        self.svc.check_relevance_with_local_llm("问题", "回答")
        # 调用前应切到 local，调用后恢复 cloud
        self.assertEqual(self.svc.llm._mode, "cloud")


class TestModeRouterRelevanceIntegration(unittest.TestCase):
    """mode_router 集成相关性校验：_apply_relevance_check"""

    def setUp(self):
        from services.mode_router import ModeRouter
        self.mr = ModeRouter()
        self.mr.init(llm=MagicMock(), retriever=MagicMock(), local_engine=MagicMock())
        # init 创建了真实的 KBDedupService，替换为 MagicMock 以控制相关性校验返回值
        self.mr._dedup_service = MagicMock()
        # 确保开关开启
        self.mr._relevance_check = True

    def test_relevance_injected_into_validation(self):
        """相关性结果注入 validation.relevance"""
        self.mr._dedup_service.check_relevance_with_local_llm.return_value = {
            "relevant": True, "confidence": 0.9, "reason": "相关"}
        resp = {"result": "回答内容", "validation": {"passed": True, "stage": "A"}}
        out = self.mr._apply_relevance_check(resp, "qa", "回答内容",
                                             question="高血压吃什么")
        self.assertIn("relevance", out["validation"])
        self.assertTrue(out["validation"]["relevance"]["relevant"])

    def test_relevance_check_skipped_when_disabled(self):
        """开关关闭 → 不校验，validation 无 relevance 字段"""
        self.mr._relevance_check = False
        resp = {"result": "回答", "validation": {"passed": True}}
        out = self.mr._apply_relevance_check(resp, "qa", "回答", question="x")
        self.assertNotIn("relevance", out["validation"])

    def test_relevance_check_skipped_when_no_dedup_service(self):
        """去重服务不可用 → 不校验"""
        self.mr._dedup_service = None
        resp = {"result": "回答", "validation": {"passed": True}}
        out = self.mr._apply_relevance_check(resp, "qa", "回答", question="x")
        self.assertNotIn("relevance", out["validation"])

    def test_short_question_skipped(self):
        """问题过短 → 跳过"""
        resp = {"result": "回答", "validation": {"passed": True}}
        out = self.mr._apply_relevance_check(resp, "qa", "回答", question="x")
        self.assertNotIn("relevance", out["validation"])

    def test_exception_does_not_block(self):
        """校验异常不阻断主流程"""
        self.mr._dedup_service.check_relevance_with_local_llm.side_effect = Exception("boom")
        resp = {"result": "回答", "validation": {"passed": True}}
        out = self.mr._apply_relevance_check(resp, "qa", "回答", question="高血压吃什么好")
        # 异常被吞掉，resp 原样返回
        self.assertEqual(out["result"], "回答")

    def test_diet_question_built_from_kwargs(self):
        """diet_plan 相关性校验：问题由 kwargs 推导"""
        self.mr._dedup_service.check_relevance_with_local_llm.return_value = {
            "relevant": True, "confidence": 0.8, "reason": "ok"}
        resp = {"result": {"goal": "减脂"}, "validation": {"passed": True}}
        up = {"crowd_type": "健身", "bmi": 23.0}
        out = self.mr._apply_relevance_check(resp, "diet_plan", {"goal": "减脂"},
                                             user_profile=up, goal="减脂")
        self.assertIn("relevance", out["validation"])
        call_args = self.mr._dedup_service.check_relevance_with_local_llm.call_args
        user_q = call_args.args[0]
        self.assertIn("减脂", user_q)


class TestRetrieverDualLayer(unittest.TestCase):
    """retriever 双层存储方法（add_with_backup / get_full_content）"""

    def test_add_with_backup_stores_full_content(self):
        """add_with_backup 把 full_doc 存入 metadata.full_content"""
        from vector.retriever import ChromaRetriever
        with patch.object(ChromaRetriever, "__init__", lambda self: None):
            ret = ChromaRetriever()
            ret.add = MagicMock()
        with patch("vector.retriever.settings") as mock_settings:
            mock_settings.KB_DUAL_LAYER_STORAGE = True
            ret.add_with_backup(
                display_doc="精简展示版",
                full_doc="完整备份版，保留核心结论原文",
                metadata={"func_type": "qa"},
                doc_id="test_001",
            )
        ret.add.assert_called_once()
        call_kwargs = ret.add.call_args
        meta = call_kwargs.kwargs["metadatas"][0]
        self.assertTrue(meta["has_backup"])
        self.assertEqual(meta["full_content"], "完整备份版，保留核心结论原文")

    def test_add_with_backup_short_doc_no_backup(self):
        """full_doc 不长于 display_doc → 不存备份"""
        from vector.retriever import ChromaRetriever
        with patch.object(ChromaRetriever, "__init__", lambda self: None):
            ret = ChromaRetriever()
            ret.add = MagicMock()
        with patch("vector.retriever.settings") as mock_settings:
            mock_settings.KB_DUAL_LAYER_STORAGE = True
            ret.add_with_backup(
                display_doc="展示版",
                full_doc="短",
                metadata={},
                doc_id="test_002",
            )
        meta = ret.add.call_args.kwargs["metadatas"][0]
        self.assertFalse(meta["has_backup"])

    def test_get_full_content_returns_backup(self):
        """get_full_content 优先返回 metadata.full_content"""
        from vector.retriever import ChromaRetriever
        with patch.object(ChromaRetriever, "__init__", lambda self: None):
            ret = ChromaRetriever()
            ret.collection = MagicMock()
        ret.collection.get.return_value = {
            "ids": ["x"],
            "documents": ["精简展示版"],
            "metadatas": [{"has_backup": True, "full_content": "完整备份版内容"}],
        }
        result = ret.get_full_content("x")
        self.assertEqual(result, "完整备份版内容")

    def test_get_full_content_fallback_to_document(self):
        """无备份时返回 document 本身"""
        from vector.retriever import ChromaRetriever
        with patch.object(ChromaRetriever, "__init__", lambda self: None):
            ret = ChromaRetriever()
            ret.collection = MagicMock()
        ret.collection.get.return_value = {
            "ids": ["x"],
            "documents": ["原文内容"],
            "metadatas": [{"has_backup": False}],
        }
        result = ret.get_full_content("x")
        self.assertEqual(result, "原文内容")


class TestEndToEndRoutingWithRelevance(unittest.TestCase):
    """端到端：mode_router.route 高性能模式注入相关性校验"""

    def setUp(self):
        from services.mode_router import ModeRouter
        self.mr = ModeRouter()
        self.mock_llm = MagicMock()
        self.mock_ret = MagicMock()
        self.mock_le = MagicMock()
        self.mock_ret.count.return_value = 0
        self.mr.init(llm=self.mock_llm, retriever=self.mock_ret, local_engine=self.mock_le)
        # 替换为 MagicMock 以控制相关性校验返回值
        self.mr._dedup_service = MagicMock()
        self.mr._relevance_check = True
        # 相关性校验 mock
        self.mr._dedup_service.check_relevance_with_local_llm.return_value = {
            "relevant": True, "confidence": 0.9, "reason": "回答切题"}

    def test_qa_high_performance_includes_relevance(self):
        """qa 高性能模式：relevance 由后台线程异步注入 validation"""
        self.mock_llm.chat.return_value = "关于高血压：1.限盐；2.运动；3.控体重；4.限酒。"
        result = self.mr.route(
            "qa", high_performance=True,
            question="高血压吃什么好？",
            user_profile={"age": 50, "crowd_type": "高血压"},
        )
        self.assertEqual(result["route"], "C_direct")
        # 高性能模式同步返回 skipped 标记，relevance 在后台线程异步注入
        self.assertEqual(result["validation"].get("skipped"), True)
        # 等待后台线程完成相关性校验
        deadline = time.time() + 5
        while "relevance" not in result.get("validation", {}) and time.time() < deadline:
            time.sleep(0.05)
        self.assertIn("relevance", result["validation"])
        self.assertTrue(result["validation"]["relevance"]["relevant"])

    def test_qa_normal_a_pass_includes_relevance(self):
        """qa 正常模式 A 通过 → validation 含 relevance"""
        self.mock_le.answer_health_query.return_value = (
            "高血压建议：1.限制盐摄入；2.适量运动；3.控制体重；4.少喝酒。"
            "温馨提示：本内容仅供膳食科普参考，不构成医疗建议。"
        )
        result = self.mr.route(
            "qa", high_performance=False,
            question="高血压吃什么好？",
            user_profile={"age": 50, "crowd_type": "高血压"},
            health_snapshot={}, chronic_diseases=["高血压"],
        )
        self.assertEqual(result["route"], "A_template_local")
        self.assertIn("relevance", result["validation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
