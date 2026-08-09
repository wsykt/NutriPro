"""pytest 全局 fixtures"""
import sys
import os
import pytest

# 将 ai_service 目录加入 sys.path，使测试可直接 import 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def scorer():
    """质量打分器实例"""
    from utils.quality_scorer import QualityScorer
    return QualityScorer()


@pytest.fixture
def fallback_engine():
    """本地兜底引擎实例"""
    from local_fallback_engine import fallback_engine
    return fallback_engine
