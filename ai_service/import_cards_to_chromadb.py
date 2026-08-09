# -*- coding: utf-8 -*-
"""
知识卡片批量导入ChromaDB脚本
=============================
将533张结构化知识卡片导入本地ChromaDB向量数据库
保留现有数据，增量添加
"""
import sys
import os
import json

# 设置ai_service为工作路径（确保能导入项目模块）
AI_SERVICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AI_SERVICE_DIR)
os.chdir(AI_SERVICE_DIR)

from vector.retriever import retriever
from utils.log_config import get_logger

_logger = get_logger("kb_importer")

# 533张知识卡片JSON路径
KB_JSON = os.path.join(AI_SERVICE_DIR, "knowledge_base", "full_knowledge_base.json")


def load_cards():
    """加载知识卡片"""
    with open(KB_JSON, "r", encoding="utf-8") as f:
        cards = json.load(f)
    print(f"加载知识卡片：{len(cards)}张")
    return cards


def card_to_document(card):
    """
    将知识卡片转换为ChromaDB文档格式
    document = 卡片标题 + 提纯内容
    metadata = 人群、主题、来源渠道等
    """
    title = card.get("title", "")
    content = card.get("purified_content", "")
    
    # 拼接文档内容
    document = f"【标题】{title}\n{content}"
    
    # 构建metadata（兼容现有结构 + 新增字段）
    group = card.get("group", "通用")
    
    # 人群映射（适配现有target_crowd字段）
    crowd_mapping = {
        "普通人": "普通人",
        "健身用户": "健身人群",
        "孕妇": "孕妇",
        "青少年": "青少年",
        "老年人": "老年人",
        "糖尿病患者": "糖尿病患者",
        "通用": None  # 通用主题不设特定人群
    }
    
    # 分类映射（适配现有category字段）
    category_mapping = {
        "糖尿病患者": "crowd_specific",
        "老年人": "crowd_specific",
        "孕妇": "crowd_specific",
        "青少年": "crowd_specific",
        "健身用户": "crowd_specific",
        "普通人": "dietary_guideline",
        "通用": "nutrition_standard"
    }
    
    metadata = {
        # 兼容现有字段
        "category": category_mapping.get(group, "nutrition_standard"),
        "source": card.get("journal", "") or card.get("source_channel", "未知"),
        "target_crowd": crowd_mapping.get(group, None),

        # 新增字段（v3.2）
        "card_id": card.get("card_id", ""),
        "group": group,
        "topic": card.get("topic", ""),
        "source_channel": card.get("source_channel", ""),
        "source_url": card.get("source_url", ""),
        "authors": card.get("authors", ""),
        "pubdate": card.get("pubdate", ""),
        "is_official_guide": str(card.get("is_official_guide", False)),
        "ingest_time": card.get("ingest_time", ""),
        "version": str(card.get("version", 1)),
        "source_type": "vector_kb",  # 标记为向量知识库来源

        # 细分人群标签（v3.2 青少年专项，如：普通青少年/体育特长生/素食人群/乳糖不耐受/肥胖青少年/睡眠运动指南）
        "sub_group": card.get("sub_group", ""),

        # 合并信息（如有）
        "merged_from": json.dumps(card.get("merged_from", []), ensure_ascii=False) if card.get("merged_from") else "",
        "debate_relation": json.dumps(card.get("debate_relation", {}), ensure_ascii=False) if card.get("debate_relation") else "",
    }
    
    # 移除None值（ChromaDB不支持None）
    metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}
    
    return document, metadata


def get_existing_card_ids():
    """获取ChromaDB中已存在的card_id（用于去重）"""
    try:
        all_data = retriever.collection.get(include=["metadatas"])
        existing_ids = set()
        for meta in all_data.get("metadatas", []) or []:
            cid = meta.get("card_id", "")
            if cid:
                existing_ids.add(cid)
        return existing_ids
    except Exception as e:
        _logger.warning(f"获取已有card_id失败: {e}")
        return set()


def import_cards(cards, batch_size=50):
    """批量导入知识卡片"""
    # 获取已存在的card_id用于去重
    existing_ids = get_existing_card_ids()
    print(f"ChromaDB现有card_id：{len(existing_ids)}个")
    
    # 过滤掉已存在的卡片
    new_cards = []
    for card in cards:
        cid = card.get("card_id", "")
        if cid and cid in existing_ids:
            continue
        new_cards.append(card)
    
    print(f"去重后需导入：{len(new_cards)}张（跳过{len(cards)-len(new_cards)}张已存在）")
    
    if not new_cards:
        print("无需导入，所有卡片已存在")
        return 0
    
    # 批量导入
    total_imported = 0
    for i in range(0, len(new_cards), batch_size):
        batch = new_cards[i:i+batch_size]
        
        documents = []
        metadatas = []
        ids = []
        
        for card in batch:
            doc, meta = card_to_document(card)
            documents.append(doc)
            metadatas.append(meta)
            # 使用card_id作为文档ID（确保唯一）
            ids.append(card.get("card_id", f"kb_card_{i}_{total_imported}"))
        
        try:
            retriever.add(documents, metadatas, ids)
            total_imported += len(batch)
            print(f"  批次 {i//batch_size + 1}：导入{len(batch)}张，累计{total_imported}张")
        except Exception as e:
            _logger.error(f"批次 {i//batch_size + 1} 导入失败: {e}")
            # 尝试逐条导入
            for j, card in enumerate(batch):
                try:
                    doc, meta = card_to_document(card)
                    retriever.add([doc], [meta], [ids[j]])
                    total_imported += 1
                except Exception as e2:
                    _logger.error(f"  卡片 {ids[j]} 导入失败: {e2}")
    
    return total_imported


def verify_import():
    """验证导入结果"""
    total = retriever.count()
    print(f"\n{'='*50}")
    print(f"ChromaDB总文档数：{total}")
    
    # 获取统计
    stats = retriever.get_rich_stats()
    print(f"\n分类分布：")
    for cat, count in stats.get("categories", {}).items():
        print(f"  {cat}: {count}")
    
    print(f"\n人群分布：")
    for crowd, count in stats.get("crowd_distribution", {}).items():
        print(f"  {crowd}: {count}")
    
    print(f"\n内容长度统计：")
    cs = stats.get("content_stats", {})
    print(f"  最短: {cs.get('min_len', 0)}字")
    print(f"  最长: {cs.get('max_len', 0)}字")
    print(f"  平均: {cs.get('avg_len', 0)}字")
    print(f"  中位: {cs.get('median_len', 0)}字")


def test_search():
    """测试检索功能"""
    print(f"\n{'='*50}")
    print("测试检索...")
    
    test_queries = [
        ("青少年补钙", "青少年"),
        ("糖尿病饮食管理", "糖尿病患者"),
        ("孕妇营养需求", "孕妇"),
        ("健身蛋白质补充", "健身人群"),
    ]
    
    for query, crowd in test_queries:
        print(f"\n  查询: '{query}' (人群: {crowd})")
        try:
            results = retriever.hybrid_retrieve(query, top_k=3, target_crowd=crowd)
            for i, r in enumerate(results):
                content_preview = r.get("content", "")[:80]
                sim = r.get("similarity", 0)
                meta = r.get("metadata", {})
                group = meta.get("group", "")
                topic = meta.get("topic", "")
                print(f"    [{i+1}] 相似度:{sim:.3f} | 人群:{group} | 主题:{topic}")
                print(f"        内容: {content_preview}...")
        except Exception as e:
            print(f"    ✗ 检索失败: {e}")


def main():
    print("=" * 50)
    print("知识卡片批量导入ChromaDB")
    print("=" * 50)
    
    # 当前ChromaDB状态
    print(f"导入前ChromaDB文档数：{retriever.count()}")
    
    # 加载卡片
    cards = load_cards()
    
    # 导入
    imported = import_cards(cards)
    print(f"\n导入完成：新增{imported}张卡片")
    
    # 验证
    verify_import()
    
    # 测试检索
    test_search()
    
    print(f"\n{'='*50}")
    print("导入流程全部完成")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
