"""临时数据库检查脚本"""
import sqlite3
import os

DB = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 60)
print(f"数据库: {DB}")
print(f"文件大小: {os.path.getsize(DB)/1024:.1f} KB")
print("=" * 60)

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"\n所有表 ({len(tables)}): {tables}")

print("\n" + "=" * 60)
print("food 表结构:")
print("=" * 60)
cur.execute("PRAGMA table_info(food)")
for col in cur.fetchall():
    print(f"  {col}")

print("\n" + "=" * 60)
print("food 表统计:")
print("=" * 60)
cur.execute("SELECT COUNT(*) FROM food")
print(f"总条数: {cur.fetchone()[0]}")

cur.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
print("\n按类别统计:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\n前 5 条样例:")
cur.execute("SELECT food_id, food_name, food_category, calorie, protein, fat, carb FROM food LIMIT 5")
for row in cur.fetchall():
    print(f"  {row}")

print("\n营养字段非空统计:")
for field in ["calorie", "protein", "fat", "carb", "diet_fiber", "calcium", "folic_acid", "dha", "gi_value"]:
    cur.execute(f"SELECT COUNT(*) FROM food WHERE {field} IS NOT NULL")
    print(f"  {field}: {cur.fetchone()[0]}")

print("\npriority 分布:")
cur.execute("SELECT priority, COUNT(*) FROM food GROUP BY priority ORDER BY priority")
for row in cur.fetchall():
    print(f"  priority={row[0]}: {row[1]}")

conn.close()
