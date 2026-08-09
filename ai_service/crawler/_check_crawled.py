"""检查刚爬取的数据质量"""
import json
import os

RAW_ROOT = r"c:\Users\13425\Desktop\个人健康助手\health\ai_service\knowledge_base\raw_crawled"
MANIFEST = os.path.join(RAW_ROOT, "manifest.jsonl")

print("=" * 70)
print("爬取数据质量检查")
print("=" * 70)

records = []
with open(MANIFEST, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                rec = json.loads(line)
                records.append(rec)
            except:
                pass

# 去重（同 raw_id 取最新版本）
latest = {}
for r in records:
    rid = r["raw_id"]
    if rid not in latest or r["version"] > latest[rid]["version"]:
        latest[rid] = r

print(f"\n总记录数: {len(latest)} (历史版本总数: {len(records)})")

print("\n--- 解析后的食物数据 ---")
for i, (rid, rec) in enumerate(latest.items()):
    parsed = rec.get("parsed_item", {})
    name = parsed.get("name", "?")
    category = parsed.get("category", "?")
    nutrients = parsed.get("nutrients", {})
    source_url = rec.get("source_url", "")

    print(f"\n[{i+1}] {name} (类别: {category})")
    print(f"    URL: {source_url}")
    print(f"    版本: v{rec['version']}, 首次: {rec['first_seen']}")
    print(f"    营养素:")
    for k, v in nutrients.items():
        print(f"      {k}: {v}")
