"""五库物理隔离数据迁移脚本

将旧的单集合 health_knowledge（4625 条）按 metadata 路由拆分为 5 个物理集合：
- kb_food       食物营养（food_data / food_knowledge）
- kb_guide      膳食指南（dietary_guideline / nutrition_standard / health_standard / meal_guidance）
- kb_crowd      人群建议（crowd_specific）
- kb_literature 文献（source_type=literature）
- kb_templates  AI 模板（template_type=ai_template）

旧集合保留只读备份（不删除）。迁移完成后可通过 retriever.count() 验证五库数据量。
幂等：可在迁移中断后重复执行（按 id 跳过已迁移的文档）。
"""

import sys
import os

# 注入项目根路径，保证 scripts/ 子目录下可直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chromadb
from chromadb.config import Settings as ChromaSettings
from vector.embedder import embedder
from config.settings import settings
from vector.retriever import ChromaRetriever
from utils.log_config import get_logger

_logger = get_logger("migrate_multi_collection")

# 与 retriever 保持同一路由规则（复用类级配置，保证一致）
ROUTING = ChromaRetriever.COLLECTION_ROUTING
DEFAULT = ChromaRetriever.DEFAULT_COLLECTION
LEGACY = ChromaRetriever.LEGACY_COLLECTION

# ChromaDB 集合的 embedding function（复用 retriever 的 BGE 嵌入，保证语义一致）
from vector.retriever import BGEEmbeddingFunction


def route(meta: dict) -> str:
    meta = meta or {}
    for rule, col_name in ROUTING:
        if all(meta.get(k) == v for k, v in rule.items()):
            return col_name
    if meta.get("template_type"):
        return "kb_templates"
    return DEFAULT


def migrate(batch_size: int = 200, dry_run: bool = False) -> dict:
    client = chromadb.PersistentClient(
        path=settings.CHROMA_DB_PATH,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    legacy = client.get_collection(LEGACY, embedding_function=BGEEmbeddingFunction())
    targets = {}
    for col_def in ChromaRetriever.COLLECTION_DEFS:
        targets[col_def["name"]] = client.get_or_create_collection(
            col_def["name"], embedding_function=BGEEmbeddingFunction()
        )

    # 已迁移的 id 记录（幂等：跳过已存在 id）
    migrated_ids = set()
    for col in targets.values():
        data = col.get(include=[])
        migrated_ids.update(data.get("ids", []) or [])
    _logger.info(f"已存在 {len(migrated_ids)} 条已迁移记录（跳过）")

    total = legacy.count()
    _logger.info(f"旧集合 {LEGACY} 共 {total} 条，开始迁移...")

    offset = 0
    stats = {c: 0 for c in targets}
    skipped = 0
    while offset < total:
        data = legacy.get(
            offset=offset, limit=batch_size,
            include=["documents", "metadatas", "embeddings"],
        )
        ids = data.get("ids", []) or []
        docs = data.get("documents", []) or []
        metas = data.get("metadatas", []) or []
        embs = data.get("embeddings")
        embs = list(embs) if embs is not None else []

        # 分组
        buckets = {}
        for i, doc_id in enumerate(ids):
            if doc_id in migrated_ids:
                skipped += 1
                continue
            col_name = route(metas[i] if i < len(metas) else {})
            buckets.setdefault(col_name, {"ids": [], "docs": [], "metas": [], "embs": []})
            buckets[col_name]["ids"].append(doc_id)
            buckets[col_name]["docs"].append(docs[i] if i < len(docs) else "")
            buckets[col_name]["metas"].append(metas[i] if i < len(metas) else {})
            buckets[col_name]["embs"].append(embs[i] if i < len(embs) else None)

        for col_name, bucket in buckets.items():
            if not bucket["ids"]:
                continue
            if dry_run:
                _logger.info(f"[dry-run] {col_name}: 将写入 {len(bucket['ids'])} 条")
                stats[col_name] += len(bucket["ids"])
                continue
            targets[col_name].add(
                ids=bucket["ids"],
                documents=bucket["docs"],
                metadatas=bucket["metas"],
                embeddings=bucket["embs"],
            )
            stats[col_name] += len(bucket["ids"])

        offset += batch_size
        _logger.info(f"进度 {min(offset, total)}/{total}")

    if dry_run:
        _logger.info(f"[dry-run] 预计迁移 {sum(stats.values())} 条，跳过 {skipped}")
    else:
        _logger.info(f"迁移完成：{sum(stats.values())} 条，跳过 {skipped} 条")
    _logger.info(f"五库分布：{stats}")
    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="五库物理隔离迁移脚本")
    parser.add_argument("--dry-run", action="store_true", help="仅预览迁移分布，不写入")
    parser.add_argument("--batch", type=int, default=200, help="批量大小")
    args = parser.parse_args()
    stats = migrate(batch_size=args.batch, dry_run=args.dry_run)
    print(f"\n迁移结果：{stats}")
