"""本地 bge-reranker 交叉编码重排序

在 BM25 + 向量混合检索（RRF 融合）之后，用交叉编码器对候选集做精排，
提升检索结果相关性排序质量。纯本地推理（sentence_transformers.CrossEncoder），
模型缺失 / 加载失败 / 推理失败时自动降级为原排序，不影响主检索流程。
"""

import os
from threading import Lock

from config.settings import settings
from utils.log_config import get_logger

_logger = get_logger("reranker")


class LocalReranker:

    def __init__(self):
        self._model = None
        self._lock = Lock()
        self._load_failed = False

    @property
    def available(self) -> bool:
        """模型文件是否就绪（本地加载前提）"""
        if not settings.RERANKER_ENABLED:
            return False
        model_dir = settings.RERANKER_MODEL_PATH
        return (
            os.path.isdir(model_dir)
            and os.path.exists(os.path.join(model_dir, "pytorch_model.bin"))
        )

    def _load(self):
        """懒加载模型（单例 + 线程安全，失败后不再重试）"""
        if self._model is not None or self._load_failed:
            return self._model
        with self._lock:
            if self._model is not None or self._load_failed:
                return self._model
            try:
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(settings.RERANKER_MODEL_PATH, max_length=512)
                _logger.info("bge-reranker 模型加载成功（交叉编码精排已启用）")
            except Exception as e:
                self._load_failed = True
                _logger.warning(f"bge-reranker 加载失败，重排序降级为原排序: {e}")
        return self._model

    def rerank(self, query: str, results: list, top_k: int = 5) -> list:
        """对候选结果做交叉编码精排，返回重排后 top_k 条。

        - 模型不可用 / 推理异常时原样返回（由调用方负责截断）
        - 每项补充 rerank_score 字段，便于上层观测
        """
        if not results or not self.available:
            return results
        model = self._load()
        if model is None:
            return results
        try:
            pairs = [(query, str(r.get("content", ""))[:500] or "") for r in results]
            scores = model.predict(pairs)
            for r, s in zip(results, scores):
                r["rerank_score"] = float(s)
            ranked = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
            _logger.debug(f"reranker 精排 {len(results)} 条候选 → 输出 top_k={top_k}")
            return ranked[:top_k]
        except Exception as e:
            _logger.warning(f"重排序推理失败，降级为原排序: {e}")
            return results


reranker = LocalReranker()
