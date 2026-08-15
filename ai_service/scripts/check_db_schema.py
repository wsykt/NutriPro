"""检查食物数据库结构"""
import sqlite3
conn = sqlite3.connect(r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()

print("=== food 表结构 ===")
c.execute("PRAGMA table_info(food)")
for col in c.fetchall():
    print(f"  {col[1]} ({col[2]})")

print("\n=== 分类分布 ===")
c.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
for cat, cnt in c.fetchall():
    print(f"  {cat}: {cnt}")

print("\n=== 优先级分布 ===")
c.execute("SELECT priority, COUNT(*) FROM food WHERE priority IS NOT NULL GROUP BY priority ORDER BY priority DESC")
for p, cnt in c.fetchall():
    print(f"  priority={p}: {cnt}")

print("\n=== 记录统计 ===")
c.execute("SELECT COUNT(*) FROM food")
print(f"  总记录: {c.fetchone()[0]}")
c.execute("SELECT COUNT(*) FROM food WHERE status = 'approved'")
print(f"  已审核: {c.fetchone()[0]}")

print("\n=== 前10条食物(名称/分类/热量/优先级) ===")
c.execute("SELECT food_name, food_category, calorie, priority FROM food WHERE status='approved' ORDER BY priority DESC NULLS LAST LIMIT 10")
for r in c.fetchall():
    print(f"  {r[0]:20s} | {str(r[1] or ''):8s} | {r[2]:6.1f} kcal | priority={r[3]}")

conn.close()
