# -*- coding: utf-8 -*-
"""合并 knowledge_base_channels.json（52张细分卡片）到 full_knowledge_base.json
策略：
1. card_id 不重复 → 直接追加
2. card_id 重复 → 若现有卡片缺 sub_group，则从新卡片补上细分标签
"""
import json
import os
from collections import Counter

KB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge_base")
BASE = os.path.join(KB_DIR, "full_knowledge_base.json")
CH = os.path.join(KB_DIR, "knowledge_base_channels.json")

base = json.load(open(BASE, encoding="utf-8"))
new = json.load(open(CH, encoding="utf-8"))
print(f"合并前：现有库 {len(base)} 张，新卡 {len(new)} 张")

by_id = {c.get("card_id"): c for c in base if c.get("card_id")}
added, updated = 0, 0
for c in new:
    cid = c.get("card_id")
    if not cid:
        continue
    if cid in by_id:
        # 重复卡片：补齐 sub_group 标签（如果现有卡片缺失）
        if not by_id[cid].get("sub_group") and c.get("sub_group"):
            by_id[cid]["sub_group"] = c["sub_group"]
            updated += 1
    else:
        base.append(c)
        by_id[cid] = c
        added += 1

json.dump(base, open(BASE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"合并完成：新增 {added} 张，补标签 {updated} 张，总计 {len(base)} 张")

# 统计 sub_group 分布
sg = Counter(x.get("sub_group", "(无)") for x in base)
print("\nsub_group 分布：")
for k, v in sg.most_common():
    print(f"  {k}: {v}张")
