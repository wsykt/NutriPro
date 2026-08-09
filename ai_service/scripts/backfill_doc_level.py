"""回填 doc_level 元数据（幂等，可重复执行）

三级检索粒度标记：
- document:  整篇权威文档（指南全文等，无 chunk_index 的 guide/crowd 条目）
- paragraph: 分块后的段落（有 chunk_index 的 guide/crowd 条目）
- fact:      单条事实/卡片（food / literature / templates 全部条目）

仅新增 doc_level 字段，不修改已有字段；无 doc_level 的旧数据
在检索过滤时会被视为不限粒度（兼容）。
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import logging

logging.disable(logging.CRITICAL)

from vector.retriever import retriever

# 无分段的集合默认全部标记为 fact
FACT_COLLECTIONS = {"kb_food", "kb_literature", "kb_templates"}
# 有分段的集合：按 chunk_index 判断 paragraph / document
CHUNKED_COLLECTIONS = {"kb_guide", "kb_crowd"}


def infer_doc_level(col_name: str, meta: dict) -> str:
    if col_name in FACT_COLLECTIONS:
        return "fact"
    if col_name in CHUNKED_COLLECTIONS:
        return "paragraph" if meta.get("chunk_index") is not None else "document"
    return "fact"


def main():
    total_updated = 0
    for col_name, col in retriever.collections.items():
        n = col.count()
        if n == 0:
            continue
        all_data = col.get(include=["metadatas"])
        ids = all_data.get("ids", []) or []
        metas = all_data.get("metadatas", []) or []
        batch_ids, batch_metas = [], []
        for i, cid in enumerate(ids):
            meta = dict(metas[i] or {})
            level = infer_doc_level(col_name, meta)
            if meta.get("doc_level") != level:
                meta["doc_level"] = level
                batch_ids.append(cid)
                batch_metas.append(meta)
        if batch_ids:
            col.update(ids=batch_ids, metadatas=batch_metas)
            total_updated += len(batch_ids)
            print(f"[{col_name}] 回填 doc_level: {len(batch_ids)} 条")
        else:
            print(f"[{col_name}] 无需回填")
    print(f"总计回填 {total_updated} 条")


if __name__ == "__main__":
    main()
