import sqlite3

conn = sqlite3.connect('C:/Users/13425/Desktop/个人健康助手/health/ai_service/data/food.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("数据库表:", [t[0] for t in tables])

for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"\n表 {table[0]} 的列:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()