import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=" * 60)
print("数据库健康检查")
print("=" * 60)

cursor.execute("PRAGMA table_info(food)")
columns = cursor.fetchall()
print("\nfood表结构:")
for col in columns:
    print(f"  {col}")

cursor.execute("SELECT COUNT(*) FROM food")
count = cursor.fetchone()[0]
print(f"\nfood表总记录数: {count}")

cursor.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
categories = cursor.fetchall()
print("\n各类别分布:")
for cat, cnt in categories:
    print(f"  {cat}: {cnt}")

cursor.execute("SELECT * FROM food WHERE food_category IN ('主食', '蔬菜', '水果', '肉类') LIMIT 10")
rows = cursor.fetchall()
print("\n示例数据:")
for row in rows:
    print(f"  {row[8]} - {row[9]}: 热量={row[2]}, 蛋白质={row[11]}, 脂肪={row[6]}, 碳水={row[3]}, GI={row[10]}")

cursor.execute("SELECT COUNT(*) FROM food WHERE gi_value IS NOT NULL AND gi_value > 0")
gi_count = cursor.fetchone()[0]
print(f"\n有GI值的记录数: {gi_count}")

cursor.execute("SELECT COUNT(*) FROM food WHERE calorie IS NOT NULL AND calorie > 0")
calorie_count = cursor.fetchone()[0]
print(f"有热量的记录数: {calorie_count}")

conn.close()