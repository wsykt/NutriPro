import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=== food表结构 ===")
cursor.execute("PRAGMA table_info(food)")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n=== 稻米类 ===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, gi_value FROM food WHERE food_name LIKE '%稻米%' OR food_name LIKE '%大米%' OR food_name LIKE '%米饭%' OR food_name LIKE '%粳米%' OR food_name LIKE '%籼米%' ORDER BY food_name")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n=== 面粉/小麦类 ===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, gi_value FROM food WHERE food_name LIKE '%小麦%' OR food_name LIKE '%面粉%' OR food_name LIKE '%富强粉%' ORDER BY food_name")
for row in cursor.fetchall():
    print(f"  {row}")

print("\n=== 总记录数 ===")
cursor.execute("SELECT COUNT(*) FROM food")
print(f"  {cursor.fetchone()[0]}")

conn.close()
