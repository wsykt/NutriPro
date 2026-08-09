# -*- coding: utf-8 -*-
"""
多渠道医学文献采集脚本（插件化渠道架构）
========================================
为知识库补充多渠道卡片，重点：
  1. Europe-PMC 渠道（优先接入，与PubMed同源，覆盖预印本/临床试验）
  2. 青少年细分人群标签分类：普通青少年/体育特长生/素食人群/乳糖不耐受/肥胖青少年/睡眠运动指南
  3. 插件化渠道注册表：预留 PMC / Trip-Database / Google Scholar 扩展接口

用法：
    python knowledge_builder_channels.py                      # 采集青少年细分人群卡片
    python knowledge_builder_channels.py --channels europe_pmc pubmed   # 指定渠道
"""
import os
import json
import re
import sys
import time
import argparse
from datetime import datetime

AI_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_DIR)

from build_knowledge_base_full import (purify_material, deduplicate_and_merge,
                                       TokenTracker, get_guidelines_for_group,
                                       KB_FILE)

KB_DIR = os.path.join(AI_DIR, "knowledge_base")
NEW_KB_FILE = os.path.join(KB_DIR, "knowledge_base_channels.json")

# ======================== 渠道插件架构 ========================
class BaseChannel:
    """渠道基类：所有医学文献渠道必须实现 search 方法"""
    name = "base"
    def search(self, query, max_results=4):
        raise NotImplementedError


class PubmedChannel(BaseChannel):
    """PubMed渠道（NCB E-utilities）"""
    name = "pubmed"
    def search(self, query, max_results=4):
        from build_knowledge_base_full import search_pubmed
        return search_pubmed(query, max_results=max_results)


class EuropePmcChannel(BaseChannel):
    """
    Europe-PMC渠道（REST API，覆盖：
      SRC:MED PubMed文献 / SRC:PPR 预印本medRxiv / SRC:CT 临床试验）
    与PubMed同源但聚合更广，作为第一优先渠道。
    """
    name = "europe_pmc"
    BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def search(self, query, max_results=4):
        try:
            resp = requests_get_json(self.BASE, {
                "query": query, "format": "json", "pageSize": max_results,
                "resultType": "core",
            })
            hits = resp.get("resultList", {}).get("result", []) if resp else []
            results = []
            for r in hits:
                pmid = r.get("pmid") or r.get("id", "")
                if not pmid:
                    continue
                authors = r.get("authorString", "")[:150]
                journal = ""
                jinfo = r.get("journalInfo", {}) or {}
                j = jinfo.get("journal", {}) or {}
                journal = j.get("title", "")
                abstract = r.get("abstractText", "")[:800]
                results.append({
                    "id": f"PMID_{pmid}",
                    "source_channel": "Europe-PMC",
                    "title": r.get("title", ""),
                    "authors": authors,
                    "journal": journal,
                    "pubdate": str(r.get("pubYear", "")),
                    "content": abstract if abstract else f"研究关于{r.get('title','')}的相关内容",
                    "url": f"https://europepmc.org/article/MED/{pmid}",
                })
                time.sleep(0.4)
            return results
        except Exception as e:
            print(f"    ✗ Europe-PMC搜索失败：{e}")
            return []


# ---------- 预留渠道（后续接入，接口已就位） ----------
class PmcChannel(BaseChannel):
    """PMC全文渠道（预留：PMC Open Access Subset API）"""
    name = "pmc"
    def search(self, query, max_results=4):
        print("    ⚠ PMC渠道未启用（预留接口）")
        return []


class TripDatabaseChannel(BaseChannel):
    """Trip Database临床证据渠道（预留）"""
    name = "trip_database"
    def search(self, query, max_results=4):
        print("    ⚠ Trip-Database渠道未启用（预留接口）")
        return []


class GoogleScholarChannel(BaseChannel):
    """Google Scholar渠道（预留）"""
    name = "google_scholar"
    def search(self, query, max_results=4):
        print("    ⚠ Google Scholar渠道未启用（预留接口）")
        return []


# 渠道注册表：新增渠道只需在此注册（插件化扩展点）
CHANNEL_REGISTRY = {
    "europe_pmc": EuropePmcChannel(),
    "pubmed": PubmedChannel(),
    "pmc": PmcChannel(),
    "trip_database": TripDatabaseChannel(),
    "google_scholar": GoogleScholarChannel(),
}


def requests_get_json(url, params, timeout=20):
    import requests
    resp = requests.get(url, params=params, timeout=timeout)
    if resp.status_code == 200:
        return resp.json()
    return None


# ======================== 青少年细分人群配置 ========================
TEEN_SUBGROUPS = [
    # 1. 普通青少年（骨骼/钙/维生素D主线）
    {"sub_group": "普通青少年", "topic": "青少年钙与维生素D骨骼发育",
     "keywords": ["adolescent calcium vitamin D bone mineral density",
                  "school age children peak bone mass calcium"]},
    {"sub_group": "普通青少年", "topic": "青少年生长发育营养需求",
     "keywords": ["adolescent growth spurt nutrition requirements",
                  "pubertal growth nutritional status teenagers"]},
    # 2. 体育特长生
    {"sub_group": "体育特长生", "topic": "青少年运动员营养与运动表现",
     "keywords": ["adolescent athletes sports nutrition performance",
                  "young athlete energy availability training"]},
    {"sub_group": "体育特长生", "topic": "青少年运动员钙与骨骼应力",
     "keywords": ["young athletes bone stress calcium vitamin D",
                  "adolescent athlete female athlete triad bone"]},
    # 3. 素食人群
    {"sub_group": "素食人群", "topic": "青少年素食者营养与钙铁锌",
     "keywords": ["vegetarian vegan adolescents nutrient adequacy",
                  "plant based diet teenagers calcium iron zinc"]},
    # 4. 乳糖不耐受
    {"sub_group": "乳糖不耐受", "topic": "乳糖不耐受青少年钙摄入",
     "keywords": ["lactose intolerance adolescents calcium intake",
                  "dairy free diet bone health teenagers"]},
    # 5. 肥胖青少年
    {"sub_group": "肥胖青少年", "topic": "青少年肥胖营养干预",
     "keywords": ["adolescent obesity dietary intervention lifestyle",
                  "overweight teenagers weight management nutrition"]},
    # 6. 睡眠运动指南
    {"sub_group": "睡眠运动指南", "topic": "青少年睡眠时长与生长激素",
     "keywords": ["adolescent sleep duration growth hormone height",
                  "sleep physical activity teenagers health outcomes"]},
]


# ======================== 主流程 ========================
def main(channels=None, topics_file=None, max_results=3, max_topics=None, output=None):
    channels = channels or ["europe_pmc"]
    print("=" * 70)
    print("多渠道知识库采集")
    print("启用渠道:", channels)
    print("=" * 70)

    # 主题清单：默认内置 TEEN_SUBGROUPS；可传外部 JSON 文件（结构 [{sub_group, topic, keywords:[...]}]）
    if topics_file:
        with open(topics_file, "r", encoding="utf-8") as f:
            topics = json.load(f)
        print(f"自定义主题文件: {topics_file}（{len(topics)} 个主题）")
    else:
        topics = TEEN_SUBGROUPS
    if max_topics:
        topics = topics[:max_topics]
        print(f"仅处理前 {max_topics} 个主题")
    print(f"子主题数: {len(topics)}")

    tracker = TokenTracker()
    all_cards = []
    for sub in topics:
        key = f"{sub['sub_group']}_{sub['topic']}"
        print(f"\n[{key}] 处理中...")
        materials = []
        for ch_name in channels:
            channel = CHANNEL_REGISTRY[ch_name]
            for kw in sub["keywords"]:
                print(f"  [{channel.name}] {kw}")
                found = channel.search(kw, max_results=max_results)
                materials.extend(found)
                time.sleep(0.3)
        # 官方指南（按子主题人群名匹配；若配置了 guideline_group 则优先使用）
        guide_group = sub.get("guideline_group", "青少年")
        guides = get_guidelines_for_group(guide_group)
        materials.extend(guides)
        print(f"  素材: {len(materials)}篇（含指南{len(guides)}篇）")

        # 提纯 → 去重合并
        new_count = 0
        for mat in materials:
            card = purify_material(mat, guide_group, sub["topic"], tracker)
            if not card:
                continue
            # 附加细分人群标签
            card["sub_group"] = sub["sub_group"]
            action, result = deduplicate_and_merge(card, all_cards)
            if action == "drop":
                print(f"    ✗ 去重: {card['card_id']}")
            elif action == "add":
                all_cards.append(card)
                new_count += 1
            elif action == "merge":
                i, merged = result
                all_cards[i] = merged
        print(f"  新增: {new_count}张")

    # 保存
    save_path = output or NEW_KB_FILE
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(all_cards, f, ensure_ascii=False, indent=2)

    # 统计
    print(f"\n{'='*70}")
    print(f"采集完成：新增卡片 {len(all_cards)} 张（保存至 {save_path}）")
    sub_stats = {}
    for c in all_cards:
        sg = c.get("sub_group", "未知")
        sub_stats[sg] = sub_stats.get(sg, 0) + 1
    for sg, n in sorted(sub_stats.items()):
        print(f"  {sg}: {n}张")
    print(f"Token累计: {tracker.total}（调用{tracker.calls}次）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="多渠道知识库采集（可自定义主题/数量）")
    parser.add_argument("--channels", nargs="+", default=["europe_pmc"],
                        help="渠道列表（europe_pmc/pubmed/pmc/trip_database/google_scholar）")
    parser.add_argument("--topics-file", default=None,
                        help="自定义主题 JSON 文件（[{sub_group, topic, keywords:[...]}]），默认内置青少年细分主题")
    parser.add_argument("--max-results", type=int, default=3,
                        help="每关键词检索条数（默认3）")
    parser.add_argument("--max-topics", type=int, default=None,
                        help="最多处理主题数（用于小批量试跑）")
    parser.add_argument("--output", default=None,
                        help="输出 JSON 路径（默认 knowledge_base/knowledge_base_channels.json）")
    args = parser.parse_args()
    main(channels=args.channels, topics_file=args.topics_file,
         max_results=args.max_results, max_topics=args.max_topics, output=args.output)
