# -*- coding: utf-8 -*-
"""
历史元数据修复脚本
==================
为早期入库的官方指南和 PubMed 文献补充 target_crowd、group、topic 字段
基于来源名称和文档内容智能推断分类
"""
from __future__ import annotations
import sys
import os
import re
import logging
from typing import Dict, Optional

AI_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_DIR)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ============================================================
# 来源 → 人群/主题映射规则
# ============================================================
SOURCE_RULES = [
    # 糖尿病相关
    (r"糖尿病|血糖|GI值|血糖生成指数", {
        "target_crowd": "糖尿病患者", "group": "糖尿病患者",
        "topic": "糖尿病膳食指南", "category": "dietary_guideline",
    }),
    # 孕妇相关
    (r"妊娠|孕产|孕期|哺乳", {
        "target_crowd": "孕妇", "group": "孕妇",
        "topic": "孕期膳食指南", "category": "dietary_guideline",
    }),
    # 老年人相关
    (r"老年|高龄|肌少症", {
        "target_crowd": "老年人", "group": "老年人",
        "topic": "老年人膳食指南", "category": "dietary_guideline",
    }),
    # 青少年相关
    (r"儿童|青少年|学生餐|生长迟缓|学生", {
        "target_crowd": "青少年", "group": "青少年",
        "topic": "儿童青少年膳食指南", "category": "dietary_guideline",
    }),
    # 高血压相关
    (r"减盐|高血压|DASH", {
        "target_crowd": "高血压患者", "group": "高血压患者",
        "topic": "高血压膳食指南", "category": "dietary_guideline",
    }),
    # 肥胖相关
    (r"肥胖|超重|减重", {
        "target_crowd": "普通人", "group": "普通人",
        "topic": "肥胖食养指南", "category": "dietary_guideline",
    }),
    # 膳食指南通用
    (r"膳食指南|居民膳食", {
        "target_crowd": "普通人", "group": "普通人",
        "topic": "中国居民膳食指南", "category": "dietary_guideline",
    }),
    # 营养素通用
    (r"宏量营养素|微量元素|常量元素|水溶性维生素|脂溶性维生素|蛋白质质量", {
        "target_crowd": "通用", "group": "通用",
        "topic": "营养素参考标准", "category": "nutrition_standard",
    }),
    # 食品标签/规范
    (r"预包装食品|标示|嘌呤|健康食堂|食物成分", {
        "target_crowd": "通用", "group": "通用",
        "topic": "食品标准与规范", "category": "nutrition_standard",
    }),
    # 科学报告
    (r"科学营养|全民高质量|膳食促进", {
        "target_crowd": "普通人", "group": "普通人",
        "topic": "国民营养报告", "category": "dietary_guideline",
    }),
    # 美国膳食指南
    (r"美国膳食指南|USDA", {
        "target_crowd": "普通人", "group": "普通人",
        "topic": "美国膳食指南", "category": "dietary_guideline",
    }),
]


def infer_crowd_from_source(source: str) -> Optional[Dict]:
    """根据来源名称推断人群/主题"""
    if not source:
        return None
    for pattern, fields in SOURCE_RULES:
        if re.search(pattern, source):
            return fields
    return None


def infer_crowd_from_content(doc: str) -> Optional[Dict]:
    """根据文档内容推断人群（兜底策略）"""
    if not doc:
        return None
    # 取前 300 字判断
    head = doc[:300]
    for pattern, fields in SOURCE_RULES:
        if re.search(pattern, head):
            return fields
    return None


# ============================================================
# 主修复流程
# ============================================================
def main():
    from vector.retriever import retriever

    print("=" * 70)
    print("历史元数据修复")
    print("=" * 70)

    all_data = retriever.collection.get(include=["metadatas", "documents"])
    metas = all_data.get("metadatas", []) or []
    docs = all_data.get("documents", []) or []
    ids = all_data.get("ids", []) or []

    print(f"总文档: {len(metas)}")

    # 找出需要修复的文档（缺少 target_crowd 或为空）
    to_fix = []
    for i, m in enumerate(metas):
        crowd = m.get("target_crowd", "")
        # 食物数据跳过（合理的无 target_crowd）
        if m.get("source_type") == "food_data" or m.get("category") == "food_knowledge":
            continue
        if m.get("food_name"):
            continue
        if not crowd or crowd == "未分类":
            to_fix.append((i, ids[i] if i < len(ids) else "", m, docs[i] if i < len(docs) else ""))

    print(f"需修复元数据文档: {len(to_fix)} 条（已排除食物数据）")

    if not to_fix:
        print("无需修复")
        return

    # 推断并修复
    fixed = 0
    failed = 0
    batch_updates = []  # (id, new_metadata)

    for idx, doc_id, meta, doc in to_fix:
        source = meta.get("source_channel") or meta.get("source") or ""
        fields = infer_crowd_from_source(source)
        if not fields:
            fields = infer_crowd_from_content(doc)

        if not fields:
            failed += 1
            continue

        # 合并新字段（保留原有字段，仅补充缺失的）
        new_meta = dict(meta)
        new_meta["target_crowd"] = fields["target_crowd"]
        new_meta["group"] = fields["group"]
        new_meta["topic"] = fields["topic"]
        # category 仅在缺失时补充
        if not new_meta.get("category"):
            new_meta["category"] = fields["category"]
        # source_channel 仅在缺失时补充
        if not new_meta.get("source_channel") and source:
            new_meta["source_channel"] = source

        batch_updates.append((doc_id, new_meta))
        fixed += 1

    print(f"\n推断成功: {fixed} 条")
    print(f"推断失败: {failed} 条")

    # 统计修复后的人群分布
    from collections import Counter
    crowd_dist = Counter()
    for _, m in batch_updates:
        crowd_dist[m["target_crowd"]] += 1
    print("\n修复后人群分布:")
    for k, v in crowd_dist.most_common():
        print(f"  {v:4d}  {k}")

    # 写入 ChromaDB
    print(f"\n{'=' * 70}")
    print(f"写入 ChromaDB（{len(batch_updates)} 条更新）")
    print(f"{'=' * 70}")

    # ChromaDB 更新元数据：先删除再添加（保留文档内容）
    success = 0
    batch_size = 50
    for i in range(0, len(batch_updates), batch_size):
        batch = batch_updates[i:i + batch_size]
        try:
            # 获取原文档
            batch_ids = [b[0] for b in batch]
            existing = retriever.collection.get(ids=batch_ids, include=["documents"])
            existing_docs = existing.get("documents", []) or []

            # 删除旧记录
            retriever.collection.delete(ids=batch_ids)

            # 重新添加（带新元数据）
            new_metas = [b[1] for b in batch]
            retriever.collection.add(
                ids=batch_ids,
                documents=existing_docs,
                metadatas=new_metas,
            )
            success += len(batch)
            print(f"  批次 {i // batch_size + 1}: 累计更新 {success}/{len(batch_updates)}")
        except Exception as e:
            logger.error(f"批次 {i // batch_size + 1} 失败: {e}")
            # 单条重试
            for doc_id, new_meta in batch:
                try:
                    existing = retriever.collection.get(ids=[doc_id], include=["documents"])
                    doc = (existing.get("documents") or [""])[0]
                    retriever.collection.delete(ids=[doc_id])
                    retriever.collection.add(ids=[doc_id], documents=[doc], metadatas=[new_meta])
                    success += 1
                except Exception as e2:
                    logger.error(f"  单条 {doc_id} 失败: {e2}")

    print(f"\n修复完成: 成功 {success} 条")
    print(f"{'=' * 70}")
    print("元数据修复完成")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
