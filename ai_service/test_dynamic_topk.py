"""RAG 动态 top_k 检索 + 模板召回阈值 测试

覆盖：
- dynamic_retrieve 按相似度分段取条数（高≥0.7取5 / 中[0.45,0.7)取3 / 低保底5 / 空结果 / 开关关闭）
- _retrieve_template 相似度过滤 + 极高匹配跳过 LLM 标记
"""
import unittest
from unittest.mock import MagicMock

from vector.retriever import ChromaRetriever
from config.settings import settings


def _mk_retriever(results):
    r = ChromaRetriever.__new__(ChromaRetriever)
    r.hybrid_retrieve = MagicMock(return_value=results)
    return r


class TestDynamicTopK(unittest.TestCase):

    def setUp(self):
        self._enabled = settings.RAG_DYNAMIC_TOPK_ENABLED

    def tearDown(self):
        settings.RAG_DYNAMIC_TOPK_ENABLED = self._enabled

    def test_high_similarity_takes_high_count(self):
        r = _mk_retriever([{'content': f'c{i}', 'similarity': 0.8 - i * 0.01} for i in range(10)])
        out = r.dynamic_retrieve('q')
        self.assertEqual(len(out), settings.RAG_TOPK_HIGH_COUNT)

    def test_medium_similarity_takes_low_count(self):
        r = _mk_retriever([{'content': f'c{i}', 'similarity': 0.6 - i * 0.02} for i in range(8)])
        out = r.dynamic_retrieve('q')
        self.assertEqual(len(out), settings.RAG_TOPK_LOW_COUNT)

    def test_low_similarity_fallback_default(self):
        r = _mk_retriever([{'content': f'c{i}', 'similarity': 0.3 - i * 0.01} for i in range(8)])
        out = r.dynamic_retrieve('q', default_top_k=5)
        self.assertEqual(len(out), 5)

    def test_mixed_similarity_only_high_segment(self):
        results = [{'content': 'a', 'similarity': 0.85},
                   {'content': 'b', 'similarity': 0.72},
                   {'content': 'c', 'similarity': 0.60}] * 3
        r = _mk_retriever(results)
        out = r.dynamic_retrieve('q')
        self.assertEqual(len(out), settings.RAG_TOPK_HIGH_COUNT)

    def test_empty_results(self):
        r = _mk_retriever([])
        self.assertEqual(r.dynamic_retrieve('q'), [])

    def test_disabled_uses_plain_hybrid(self):
        settings.RAG_DYNAMIC_TOPK_ENABLED = False
        r = _mk_retriever([{'content': 'x', 'similarity': 0.3}] * 3)
        out = r.dynamic_retrieve('q', default_top_k=3)
        self.assertEqual(len(out), 3)
        r.hybrid_retrieve.assert_called_once()


class TestTemplateRetrieveThreshold(unittest.TestCase):

    def _mk_router(self):
        from services.mode_router import ModeRouter
        mr = ModeRouter.__new__(ModeRouter)
        mr._retriever = MagicMock()
        mr._retriever.count.return_value = 100
        return mr

    def test_below_min_similarity_returns_empty(self):
        mr = self._mk_router()
        mr._retriever.search.return_value = [{'content': 't', 'similarity': 0.30}]
        text, skip = mr._retrieve_template('qa', question='高血压吃什么好')
        self.assertEqual(text, '')
        self.assertFalse(skip)

    def test_meets_min_similarity_returns_template(self):
        mr = self._mk_router()
        mr._retriever.search.return_value = [{'content': 't1', 'similarity': 0.55},
                                             {'content': 't2', 'similarity': 0.50}]
        text, skip = mr._retrieve_template('qa', question='高血压吃什么好')
        self.assertIn('t1', text)
        self.assertIn('t2', text)
        self.assertFalse(skip)

    def test_extreme_match_marks_skip_llm(self):
        mr = self._mk_router()
        mr._retriever.search.return_value = [{'content': 't1', 'similarity': 0.97}]
        text, skip = mr._retrieve_template('qa', question='高血压吃什么好')
        self.assertEqual(text, 't1')
        self.assertTrue(skip)

    def test_no_retriever_returns_empty(self):
        from services.mode_router import ModeRouter
        mr = ModeRouter.__new__(ModeRouter)
        mr._retriever = None
        text, skip = mr._retrieve_template('qa', question='x')
        self.assertEqual(text, '')
        self.assertFalse(skip)


if __name__ == '__main__':
    unittest.main()
