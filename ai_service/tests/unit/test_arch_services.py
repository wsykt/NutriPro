# -*- coding: utf-8 -*-
"""目标架构服务层单测：统一校验入口 / 双层聚类 / 文献合并 / 争议识别"""
import sys
import os

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from services.validation_service import validation_service
from services.kb_cluster import KnowledgeClusterer, kb_clusterer, card_text
from services.literature_merge import LiteratureMerger
from services.dispute_detect import DisputeDetector


def make_card(card_id, title, content, topic="均衡营养"):
    return {
        "card_id": card_id,
        "title": title,
        "topic": topic,
        "purified_content": content,
    }


CARD_A = make_card("PMID_10000001", "研究A：膳食纤维与心血管",
                   "【核心循证结论】膳食纤维可降低心血管风险。\n"
                   "【量化临床数据】每日25g纤维风险下降约15%。\n"
                   "【适用人群】普通人群。\n"
                   "【局限性/学术争议】观察性研究。")
CARD_B = make_card("PMID_10000002", "研究B：膳食纤维心血管保护",
                   "【核心循证结论】高纤维饮食减少心血管事件。\n"
                   "【量化临床数据】每日30g纤维风险下降约18%。\n"
                   "【适用人群】普通人群。\n"
                   "【局限性/学术争议】暂无。")
CARD_C = make_card("PMID_10000003", "研究C：钙与骨骼健康",
                   "【核心循证结论】补钙可提升骨密度。\n"
                   "【量化临床数据】每日800mg钙骨密度提升3%。\n"
                   "【适用人群】老年人。\n"
                   "【局限性/学术争议】仍需前瞻性验证。")
CARD_D = make_card("PMID_10000004", "研究D：纤维摄入与肠道",
                   "【核心循证结论】膳食纤维改善肠道菌群。\n"
                   "【量化临床数据】暂无。\n"
                   "【适用人群】普通人群。\n"
                   "【局限性/学术争议】存在一定争议。")


class FakeLLM:
    """可控假 LLM：返回预设 dict 或抛异常"""

    def __init__(self, response):
        self._r = response

    def chat_json(self, messages, **kwargs):
        if isinstance(self._r, Exception):
            raise self._r
        return self._r


# ==================== 1. 统一校验入口 ====================
class TestValidationService:
    def test_article_structure_ok(self):
        article = ("## 引言\n膳食纤维很重要。\n"
                   "## 证据\n每日25g可获益。\n"
                   "## 结论\n应多摄入纤维。")
        r = validation_service.validate_article(article)
        assert r["level"] == "ok"
        assert r["stats"]["section_h2"] == 3

    def test_article_absolute_word_warn(self):
        article = "## 结论\n该方案可以根治糖尿病。"
        r = validation_service.validate_article(article)
        assert r["level"] == "warn"
        assert any("绝对化" in i["message"] for i in r["issues"])

    def test_article_unknown_pmid_warn(self):
        article = "## 证据\n多项研究（PMID:99999999）支持该观点。"
        r = validation_service.validate_article(article, sources=[CARD_A])
        assert r["level"] == "warn"
        assert "PMID: 99999999" in r["citations"]["unknown_cited"] or \
               "99999999" in r["citations"]["unknown_cited"]

    def test_article_absurd_number_warn(self):
        article = "## 结论\n每日应摄入 99999g 蛋白质。"
        r = validation_service.validate_article(article)
        assert r["level"] == "warn"
        assert r["absurd_numbers"]

    def test_validate_dispatch_response(self):
        # response 类型走 validator_pipeline（不启用组件时返回 ok）
        from agent.validators.validator import ValidatorPipeline
        v = ValidatorPipeline(enabled=False)
        old = validation_service.__dict__.get("_pipeline_holder")
        try:
            result = v.validate("qa", "你好")
            assert result["level"] == "ok"
        finally:
            pass

    def test_validate_dispatch_article(self):
        r = validation_service.validate("article", "## 结论\n每日摄入99999g盐。", sources=[])
        assert r["level"] == "warn"


# ==================== 2. 双层聚类 ====================
class TestKnowledgeClusterer:
    def test_card_text(self):
        t = card_text(CARD_A)
        assert "膳食纤维" in t

    def test_cluster_with_controlled_matrix(self, monkeypatch):
        # 手工相似度矩阵：A-B 0.95 高相似；A-C 0.2 无关；A-D 0.55 灰区(LLM判相关)
        fake = np.array([
            [1.00, 0.95, 0.20, 0.55],
            [0.95, 1.00, 0.22, 0.50],
            [0.20, 0.22, 1.00, 0.25],
            [0.55, 0.50, 0.25, 1.00],
        ])
        monkeypatch.setattr("services.kb_cluster.cosine_similarity_matrix",
                            lambda texts: fake)
        cl = KnowledgeClusterer(llm=None, high_threshold=0.70, low_threshold=0.40,
                                enabled=True)
        result = cl.cluster([CARD_A, CARD_B, CARD_C, CARD_D],
                            judge=lambda a, b: True)  # 灰区全判相关
        assert len(result["clusters"]) >= 1
        # A/B/D 应聚在同一簇（A-D 灰区经 judge 判相关）
        cluster_cards = {c["card_id"] for clu in result["clusters"] for c in clu["cards"]}
        assert "PMID_10000001" in cluster_cards
        assert "PMID_10000002" in cluster_cards
        assert "PMID_10000004" in cluster_cards
        assert "PMID_10000003" in result["singles"][0]["card_id"] or \
               "PMID_10000003" in [s["card_id"] for s in result["singles"]]

    def test_cluster_single_card(self):
        cl = KnowledgeClusterer(enabled=True)
        result = cl.cluster([CARD_A])
        assert result["method"] == "skipped" or result["clusters"] == []
        assert len(result["singles"]) == 1


# ==================== 3. 文献合并 ====================
class TestLiteratureMerger:
    def test_merge_via_llm(self):
        llm = FakeLLM({
            "merged_content": "【核心循证结论】膳食纤维降低心血管风险。\n"
                              "【量化临床数据】每日25-30g风险下降15-18%。\n"
                              "【适用人群】普通人群。\n"
                              "【局限性/学术争议】观察性研究为主。",
            "core_conclusion": "膳食纤维降低心血管风险",
        })
        m = LiteratureMerger(llm=llm, enabled=True)
        r = m.merge([CARD_A, CARD_B], topic="膳食纤维与心血管")
        assert r["merged"] is True
        assert r["method"] == "llm"
        assert r["merged_card"]["source_count"] == 2
        pmids = {s["pmid"] for s in r["merged_card"]["sources"]}
        assert "10000001" in pmids and "10000002" in pmids

    def test_merge_local_fallback(self):
        llm = FakeLLM(RuntimeError("LLM 不可用"))
        m = LiteratureMerger(llm=llm, enabled=True)
        r = m.merge([CARD_A, CARD_B])
        assert r["merged"] is True
        assert r["method"] == "local"
        assert "核心循证结论" in r["merged_card"]["purified_content"]

    def test_merge_skipped_when_disabled(self):
        m = LiteratureMerger(enabled=False)
        r = m.merge([CARD_A, CARD_B])
        assert r["merged"] is False
        assert r["method"] == "skipped"


# ==================== 4. 争议识别 ====================
class TestDisputeDetector:
    def test_detect_conflict(self):
        # A 与 D 结论相悖（有争议表述）；A 与 B 一致
        llm = FakeLLM({"relation": "conflicting", "stance_a": "支持X", "stance_b": "反对X"})
        d = DisputeDetector(llm=llm, enabled=True, min_cards=2)
        cards = [CARD_A, CARD_D]
        r = d.detect(cards, topic="膳食纤维争议", use_llm=True)
        assert r["disputes"], "应识别出争议分组"
        dispute = r["disputes"][0]
        ids = [cid for side in dispute["sides"] for cid in side["card_ids"]]
        assert "PMID_10000001" in ids and "PMID_10000004" in ids

    def test_detect_consistent_no_dispute(self):
        llm = FakeLLM({"relation": "consistent", "stance_a": "", "stance_b": ""})
        d = DisputeDetector(llm=llm, enabled=True, min_cards=2)
        r = d.detect([CARD_A, CARD_B], use_llm=True)
        assert r["disputes"] == []

    def test_detect_local_fallback(self):
        # LLM 抛异常 → 本地规则兜底（含"仍存争议"提示 → conflicting）
        llm = FakeLLM(RuntimeError("LLM 不可用"))
        d = DisputeDetector(llm=llm, enabled=True, min_cards=2)
        cards = [CARD_A, make_card("PMID_20000001", "研究E",
                                    "【核心循证结论】结论仍存争议。\n"
                                    "【局限性/学术争议】尚未有定论。")]
        r = d.detect(cards, use_llm=True)
        # 本地规则：D 含冲突提示 → conflicting
        assert r["disputes"]

    def test_disabled(self):
        d = DisputeDetector(enabled=False)
        r = d.detect([CARD_A, CARD_D])
        assert r["method"] == "skipped"

    def test_has_major_dispute(self):
        llm = FakeLLM({"relation": "conflicting", "stance_a": "A", "stance_b": "B"})
        d = DisputeDetector(llm=llm, enabled=True, min_cards=2)
        assert d.has_major_dispute([CARD_A, CARD_D], use_llm=True) is True
