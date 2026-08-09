"""
食物数据 → 向量知识库整合脚本
==============================
将 merged_foods.json 中的食物数据转换为知识卡片格式，导入 ChromaDB

食物知识卡片格式：
- card_id: food_cn_{md5前12位}
- title: 食物名称（如"小麦粉(均值)"）
- purified_content: 营养素描述文本
- group: 通用
- topic: 食物营养数据
- source_channel: 中国食物成分查询平台
- is_official_guide: True（官方权威数据）

用法:
    python -m crawler.ingest_to_vector_kb              # 导入 merged_foods.json
    python -m crawler.ingest_to_vector_kb --clean      # 先清理旧食物卡片再导入
    python -m crawler.ingest_to_vector_kb --report      # 打印详细报告
"""
from __future__ import annotations
import os
import sys
import json
import hashlib
import logging
from typing import Dict, List, Optional

AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

logger = logging.getLogger(__name__)

MERGED_PATH = os.path.join(AI_SERVICE_DIR, "crawler", "merged_foods.json")

# 营养素中文名映射（用于生成可读文本）
NUTRIENT_CN = {
    "calorie": ("热量", "kcal"),
    "protein": ("蛋白质", "g"),
    "fat": ("脂肪", "g"),
    "carb": ("碳水化合物", "g"),
    "diet_fiber": ("膳食纤维", "g"),
    "calcium": ("钙", "mg"),
    "folic_acid": ("叶酸", "μg"),
    "dha": ("DHA", "mg"),
    "gi_value": ("GI值", ""),
}


def make_card_id(name: str, category: str) -> str:
    """生成唯一 card_id"""
    raw = f"food_cn_{name}_{category}"
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"food_cn_{h}"


def food_to_card(food: dict) -> dict:
    """将食物数据转换为知识卡片格式"""
    name = food.get("name", "")
    category = food.get("category", "")
    nutrients = food.get("nutrients", {}) or {}
    merged_count = food.get("merged_count", 1)
    source_url = food.get("source_url", "")

    # 生成营养素描述文本
    parts = [f"{name}，{category}类。"]
    parts.append("每100g可食部含：")

    nutrient_lines = []
    for key, (cn, unit) in NUTRIENT_CN.items():
        val = nutrients.get(key)
        if val is not None:
            if unit:
                nutrient_lines.append(f"{cn}{val}{unit}")
            else:
                nutrient_lines.append(f"{cn}{val}")
    parts.append("、".join(nutrient_lines) + "。")

    # 合并信息
    if merged_count > 1:
        merged_from = food.get("merged_from", [])
        parts.append(f"（本数据为{merged_count}个品种取均值：{'、'.join(merged_from[:5])}）")

    content = "".join(parts)

    return {
        "card_id": make_card_id(name, category),
        "title": f"{name}（{category}）",
        "purified_content": content,
        "group": "通用",
        "topic": "食物营养数据",
        "source_channel": "中国食物成分查询平台",
        "source_url": source_url,
        "is_official_guide": True,
        "source_type": "food_data",
        "food_name": name,
        "food_category": category,
        "merged_count": merged_count,
    }


def get_existing_food_card_ids(retriever) -> set:
    """获取向量库中已存在的食物卡片ID（source_type=food_data）"""
    try:
        all_data = retriever.collection.get(include=["metadatas"])
        existing = set()
        for meta in all_data.get("metadatas", []) or []:
            if meta.get("source_type") == "food_data":
                cid = meta.get("card_id", "")
                if cid:
                    existing.add(cid)
        return existing
    except Exception as e:
        logger.warning(f"获取已有食物卡片失败: {e}")
        return set()


def delete_existing_food_cards(retriever) -> int:
    """删除向量库中所有食物卡片（source_type=food_data）"""
    try:
        all_data = retriever.collection.get(include=["metadatas"])
        ids_to_delete = []
        for i, meta in enumerate(all_data.get("metadatas", []) or []):
            if meta.get("source_type") == "food_data":
                ids = all_data.get("ids", [])
                if i < len(ids):
                    ids_to_delete.append(ids[i])
        if ids_to_delete:
            retriever.collection.delete(ids=ids_to_delete)
            print(f"  已删除 {len(ids_to_delete)} 条旧食物卡片")
            return len(ids_to_delete)
        print(f"  无旧食物卡片需删除")
        return 0
    except Exception as e:
        logger.error(f"删除旧食物卡片失败: {e}")
        return 0


def main():
    import argparse
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="食物数据 → 向量知识库")
    parser.add_argument("--clean", action="store_true",
                        help="先清理旧食物卡片再导入")
    parser.add_argument("--report", action="store_true",
                        help="打印详细报告")
    parser.add_argument("--input", default=MERGED_PATH,
                        help=f"输入 JSON 路径（默认: {MERGED_PATH}）")
    args = parser.parse_args()

    print("=" * 70)
    print("食物数据 → 向量知识库整合")
    print("=" * 70)

    # 1. 加载整合后的食物数据
    if not os.path.exists(args.input):
        print(f"⚠️ 文件不存在: {args.input}")
        print("  请先运行: python -m crawler.merge_foods")
        return

    with open(args.input, "r", encoding="utf-8") as f:
        foods = json.load(f)
    print(f"\n【1】加载食物数据: {len(foods)} 条")

    # 2. 转换为知识卡片
    cards = [food_to_card(f) for f in foods]
    print(f"\n【2】转换为知识卡片: {len(cards)} 张")

    if args.report:
        print(f"\n  样例卡片:")
        for c in cards[:3]:
            print(f"    {c['card_id']}: {c['title']}")
            print(f"      内容: {c['purified_content'][:100]}...")

    # 3. 导入 ChromaDB
    print(f"\n【3】导入 ChromaDB...")
    try:
        from vector.retriever import retriever
    except ImportError as e:
        print(f"⚠️ 无法导入 retriever: {e}")
        print("  请确保 ai_service 环境正常")
        return

    before_count = retriever.count()
    print(f"  导入前 ChromaDB 总文档数: {before_count}")

    # 清理旧数据
    if args.clean:
        print(f"  清理旧食物卡片...")
        deleted = delete_existing_food_cards(retriever)
        before_count = retriever.count()
        print(f"  清理后 ChromaDB 总文档数: {before_count}")

    # 去重
    existing_ids = get_existing_food_card_ids(retriever)
    print(f"  已有食物卡片: {len(existing_ids)} 张")

    new_cards = [c for c in cards if c["card_id"] not in existing_ids]
    print(f"  需导入: {len(new_cards)} 张（跳过 {len(cards) - len(new_cards)} 张已存在）")

    if not new_cards:
        print("  无需导入，所有卡片已存在")
    else:
        # 批量导入
        batch_size = 50
        total_imported = 0
        for i in range(0, len(new_cards), batch_size):
            batch = new_cards[i:i + batch_size]
            documents = []
            metadatas = []
            ids = []
            for card in batch:
                doc = f"【标题】{card['title']}\n{card['purified_content']}"
                meta = {
                    "category": "food_data",
                    "source": card["source_channel"],
                    "target_crowd": None,
                    "card_id": card["card_id"],
                    "group": card["group"],
                    "topic": card["topic"],
                    "source_channel": card["source_channel"],
                    "source_url": card.get("source_url", ""),
                    "is_official_guide": "True",
                    "source_type": "food_data",
                    "food_name": card["food_name"],
                    "food_category": card["food_category"],
                }
                # 移除 None
                meta = {k: v for k, v in meta.items() if v is not None and v != ""}
                documents.append(doc)
                metadatas.append(meta)
                ids.append(card["card_id"])

            try:
                retriever.add(documents, metadatas, ids)
                total_imported += len(batch)
                if (i // batch_size + 1) % 4 == 0 or total_imported == len(new_cards):
                    print(f"    批次 {i // batch_size + 1}: 累计导入 {total_imported}/{len(new_cards)}")
            except Exception as e:
                logger.error(f"批次 {i // batch_size + 1} 失败: {e}")
                # 逐条导入
                for j, card in enumerate(batch):
                    try:
                        retriever.add([documents[j]], [metadatas[j]], [ids[j]])
                        total_imported += 1
                    except Exception as e2:
                        logger.error(f"  卡片 {ids[j]} 失败: {e2}")

        print(f"\n  导入完成: 新增 {total_imported} 张")

    # 4. 验证
    after_count = retriever.count()
    print(f"\n【4】验证:")
    print(f"  导入前: {before_count}")
    print(f"  导入后: {after_count}")
    print(f"  净增: {after_count - before_count}")

    # 测试检索
    print(f"\n【5】测试检索:")
    test_queries = ["小麦粉热量", "鸡蛋蛋白质", "三文鱼DHA", "菠菜叶酸"]
    for q in test_queries:
        try:
            results = retriever.hybrid_retrieve(q, top_k=2)
            print(f"  查询 '{q}':")
            for i, r in enumerate(results[:2]):
                content = r.get("content", "")[:80]
                sim = r.get("similarity", 0)
                meta = r.get("metadata", {})
                if meta.get("source_type") == "food_data":
                    print(f"    [{i+1}] 相似度:{sim:.3f} | {meta.get('food_name', '')} | {content[:60]}...")
                else:
                    print(f"    [{i+1}] 相似度:{sim:.3f} | 非食物卡片 | {content[:60]}...")
        except Exception as e:
            print(f"    ✗ 检索失败: {e}")

    print("\n" + "=" * 70)
    print("向量知识库整合完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
