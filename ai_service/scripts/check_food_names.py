"""查找数据库中的零食/饮料类食物"""
import sqlite3
conn = sqlite3.connect(r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()

keywords = ["可乐", "奶茶", "巧克力", "全麦", "薯片", "面包", "饮料", "蛋糕", "饼干", "糖果", "冰淇淋", "雪糕", "啤酒", "红酒", "白酒"]
for kw in keywords:
    c.execute("SELECT food_name, calorie, food_category FROM food WHERE food_name LIKE ? LIMIT 5", (f"%{kw}%",))
    rows = c.fetchall()
    if rows:
        for r in rows:
            print(f"  {kw:8s} -> {r[0]:30s} {r[1]:6.1f} kcal | {r[2]}")
    else:
        print(f"  {kw:8s} -> 数据库不存在")

conn.close()
