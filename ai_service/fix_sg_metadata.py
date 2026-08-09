# -*- coding: utf-8 -*-
"""为 ChromaDB 中已存在但缺 sub_group 的卡片补上细分标签"""
import json
import os
from collections import Counter

os.chdir(os.path.dirname(os.path.abspath(__file__)))
from vector.retriever import retriever

cards = json.load(open("knowledge_base/full_knowledge_base.json", encoding="utf-8"))
sg_map = {c.get("card_id"): c.get("sub_group") for c in cards if c.get("card_id") and c.get("sub_group")}

all_d = retriever.collection.get(include=["metadatas"])
ids, metas = all_d.get("ids", []), all_d.get("metadatas", [])
upd_ids, upd_metas = [], []
for i, m in zip(ids, metas):
    cid = m.get("card_id", "")
    sg = sg_map.get(cid)
    if sg and not m.get("sub_group"):
        m2 = dict(m)
        m2["sub_group"] = sg
        upd_ids.append(i)
        upd_metas.append(m2)

if upd_ids:
    retriever.collection.update(ids=upd_ids, metadatas=upd_metas)
    print(f"已更新 {len(upd_ids)} 条文档的 sub_group")
else:
    print("无需更新")

d = retriever.collection.get(include=["metadatas"])
sg = Counter(m.get("sub_group", "(无)") for m in d.get("metadatas", []))
print("更新后 sub_group 分布:")
for k, v in sg.most_common():
    print(f"  {k}: {v}")
