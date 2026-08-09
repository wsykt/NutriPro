"""修复 SQLite food 表中 3 条 gi_value 超范围的脏数据

问题:
- 牛奶 (food_id=1, 奶类): gi_value=111 → 应为 27.6（牛奶真实 GI）
- 奶粉 (food_id=6, 奶类): gi_value=1065 → 明显错误，置 NULL
- 白菜 (food_id=357, 蔬菜): gi_value=294.5 → 蔬菜 GI 不应如此高，置 NULL

依据: NUTRIENT_BOUNDS["gi_value"] = (0, 105)
"""
import sqlite3

DB = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

# 权威 GI 值参考（中国食物成分表 / ISO 26642:2010）
GI_FIXES = {
    1:   27.6,    # 牛奶（全脂）GI≈27.6
    6:   None,    # 奶粉 GI 数据不一，置 NULL
    357: None,    # 白菜 GI 实际很低（15-20），但 294.5 明显错误，置 NULL
}

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("修复前:")
cur.execute("SELECT food_id, food_name, food_category, gi_value FROM food WHERE food_id IN (1, 6, 357)")
for r in cur.fetchall():
    print(f"  {r}")

print("\n应用修复:")
for fid, new_gi in GI_FIXES.items():
    if new_gi is None:
        cur.execute("UPDATE food SET gi_value=NULL WHERE food_id=?", (fid,))
        print(f"  food_id={fid}: gi_value=NULL (清除错误数据)")
    else:
        cur.execute("UPDATE food SET gi_value=? WHERE food_id=?", (new_gi, fid))
        print(f"  food_id={fid}: gi_value={new_gi} (修正为权威值)")

conn.commit()

print("\n修复后:")
cur.execute("SELECT food_id, food_name, food_category, gi_value FROM food WHERE food_id IN (1, 6, 357)")
for r in cur.fetchall():
    print(f"  {r}")

# 全局检查：是否还有超范围 gi_value
print("\n全局检查（gi_value 超 [0,105] 范围）:")
cur.execute("SELECT food_id, food_name, gi_value FROM food WHERE gi_value IS NOT NULL AND (gi_value < 0 OR gi_value > 105)")
bad = cur.fetchall()
if bad:
    print(f"  仍有 {len(bad)} 条超范围:")
    for r in bad:
        print(f"    {r}")
else:
    print("  ✓ 无超范围数据")

conn.close()
print("\n修复完成")
