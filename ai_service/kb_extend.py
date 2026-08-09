# -*- coding: utf-8 -*-
"""
知识库参数化扩展入口（kb_extend.py）
====================================
解决「更换关键词/数量后无法自动完善」的问题：
把主题、关键词、每主题数量全部参数化，支持两种输入方式：

  1) JSON 配置文件（推荐，适合批量主题）：
       python kb_extend.py --config topics_demo.json
       --config 省略时默认读取 knowledge_base/topics_config.json

  2) 命令行直接指定单主题（适合快速验证一个关键词）：
       python kb_extend.py --group 普通人 --topic "补钙与骨骼健康" \
           --keywords "calcium supplementation bone health;calcium intake osteoporosis" \
           --max-per-topic 3 --no-ingest

统一复用 literature_enrich_v2 的 PubMed / Semantic Scholar / Europe-PMC /
PMC / Trip Database 多源搜索 + 制卡 + 四层去重入库逻辑，
可选运行 kb_cluster 双层聚类并输出分类报告。

典型用法（只需改 JSON 里的关键词与数量即可自动完善知识库）：
    python kb_extend.py --config my_topics.json --max-per-topic 5 --cluster
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

AI_DIR = os.path.dirname(os.path.abspath(__file__))
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)

from crawler.literature_enrich_v2 import (
    search_pubmed_direct,
    search_semantic_scholar,
    search_europepmc,
    search_pmc_direct,
    search_trip_database,
    make_card_from_literature,
    ingest_to_chromadb,
)

DEFAULT_CONFIG = os.path.join(AI_DIR, "knowledge_base", "topics_config.json")
OUTPUT_DIR = os.path.join(AI_DIR, "knowledge_base")

# 数据源 → 搜索函数 + 限流间隔
SOURCES = {
    "pubmed": (search_pubmed_direct, 0.4),
    "ss": (search_semantic_scholar, 1.0),
    "pmc": (search_europepmc, 0.5),
    "pmc_direct": (search_pmc_direct, 0.5),
    "trip": (search_trip_database, 1.0),
}


def load_topics(args) -> list:
    """从 JSON 配置或命令行参数构造主题列表。
    每项: {"group": 人群, "topic": 主题名, "keywords": [k1, k2, ...], "sources": [...可选]}
    """
    topics = []
    if args.config:
        cfg_path = args.config
        if not os.path.isabs(cfg_path):
            cfg_path = os.path.join(AI_DIR, cfg_path)
        if not os.path.exists(cfg_path):
            print(f"[错误] 配置文件不存在: {cfg_path}")
            sys.exit(1)
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        # 支持 {"topics": [...]} 或直接 [...]
        topics = data.get("topics", data) if isinstance(data, dict) else data
        if not isinstance(topics, list) or not topics:
            print(f"[错误] 配置文件中没有主题列表: {cfg_path}")
            sys.exit(1)
    elif args.topic:
        keywords = [k.strip() for k in (args.keywords or "").split(";") if k.strip()]
        if not keywords:
            print("[错误] 命令行模式需提供 --keywords（分号分隔）")
            sys.exit(1)
        sources = args.sources.split(",") if args.sources else list(SOURCES.keys())
        topics = [{"group": args.group, "topic": args.topic,
                   "keywords": keywords, "sources": sources}]
    else:
        print("[错误] 请通过 --config 指定配置文件，或用 --topic + --keywords 指定单主题")
        sys.exit(1)
    return topics


def collect_cards(topics: list, max_per_topic: int, only_sources: list) -> list:
    """多源搜索并制卡。返回全部卡片（含人群/主题标注）。"""
    cards = []
    for idx, t in enumerate(topics, 1):
        group = t.get("group", "普通人")
        topic = t.get("topic", "")
        kws = t.get("keywords", [])
        # 主题级数据源（未配置则用命令行 only_sources；再默认全部）
        sources = t.get("sources") or only_sources or list(SOURCES.keys())
        print(f"\n[{idx}/{len(topics)}] 人群={group} | 主题={topic} | 关键词数={len(kws)}")
        for kw in kws:
            per_source = max(1, max_per_topic // max(1, len(sources)))
            for src in sources:
                func, delay = SOURCES[src]
                try:
                    results = func(kw, max_results=per_source)
                except Exception as e:
                    print(f"    ⚠️ {src} 搜索失败: {e}")
                    continue
                made = 0
                for mat in results:
                    card = make_card_from_literature(mat, group, topic)
                    if card:
                        cards.append(card)
                        made += 1
                print(f"    [{src}] {kw[:50]}… → {len(results)} 篇, 制卡 {made} 张")
                time.sleep(delay)
    return cards


def run_cluster(cards: list, use_llm: bool) -> dict:
    """可选：双层聚类，输出分类报告（不入库，仅分析结构）"""
    from services.kb_cluster import KnowledgeClusterer
    llm = None
    if use_llm:
        from llm.router import llm as _llm
        llm = _llm
    clusterer = KnowledgeClusterer(llm=llm)
    result = clusterer.cluster(cards)
    print(f"\n[聚类] 总数={result['meta']['total']}, 成簇={result['meta']['clustered']}, "
          f"独立={result['meta']['single']}, LLM判定={result['meta']['llm_judged']}")
    for cl in result["clusters"]:
        print(f"  - 簇[{cl['cluster_id']}] 主题={cl['topic']} 卡片数={cl['card_count']}")
    return result


def main():
    parser = argparse.ArgumentParser(description="知识库参数化扩展入口")
    parser.add_argument("--config", default=None,
                        help="JSON 配置文件路径（默认 knowledge_base/topics_config.json）")
    parser.add_argument("--group", default="普通人", help="人群（命令行模式）")
    parser.add_argument("--topic", default=None, help="主题名（命令行模式）")
    parser.add_argument("--keywords", default=None, help="关键词，分号分隔（命令行模式）")
    parser.add_argument("--sources", default=None,
                        help="数据源白名单，逗号分隔: pubmed,ss,pmc,pmc_direct,trip")
    parser.add_argument("--max-per-topic", type=int, default=5,
                        help="每个主题每个数据源的文献数量上限")
    parser.add_argument("--no-ingest", action="store_true", help="只搜索制卡，不写入向量库")
    parser.add_argument("--cluster", action="store_true", help="制卡后运行双层聚类分析")
    parser.add_argument("--cluster-llm", action="store_true", help="聚类灰色区间使用 LLM 判定")
    args = parser.parse_args()

    if not args.config and not os.path.exists(DEFAULT_CONFIG):
        args.config = None  # 无默认配置时强制要求命令行参数

    topics = load_topics(args)
    print("=" * 70)
    print("知识库参数化扩展")
    print(f"主题数: {len(topics)} | 每主题每源上限: {args.max_per_topic}")
    print("=" * 70)

    cards = collect_cards(topics, args.max_per_topic, args.sources)
    print(f"\n总计制卡: {len(cards)} 张")

    if not cards:
        print("无有效卡片，退出")
        return

    # 按人群/来源统计
    by_group, by_source = {}, {}
    for c in cards:
        by_group[c.get("group", "未知")] = by_group.get(c.get("group", "未知"), 0) + 1
        by_source[c.get("source_channel", "未知")] = by_source.get(c.get("source_channel", "未知"), 0) + 1
    print("\n按人群:", {k: v for k, v in sorted(by_group.items(), key=lambda x: -x[1])})
    print("按来源:", {k: v for k, v in sorted(by_source.items(), key=lambda x: -x[1])})

    # 保存原始卡片（便于复查）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "kb_extend_cards.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    print(f"\n卡片已保存: {out_path}")

    # 可选聚类分析
    if args.cluster:
        run_cluster(cards, args.cluster_llm)

    # 入库
    if not args.no_ingest:
        from vector.retriever import retriever
        before = retriever.count()
        imported = ingest_to_chromadb(cards, retriever)
        after = retriever.count()
        print(f"\n[入库] 前 {before} → 新增 {imported} → 后 {after} (净增 {after - before})")
    else:
        print("\n[入库] 已跳过（--no-ingest）")

    print("\n完成。如需换主题/关键词，仅需修改配置 JSON 后重跑本脚本。")


if __name__ == "__main__":
    main()
