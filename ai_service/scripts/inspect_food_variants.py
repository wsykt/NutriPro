import sqlite3
import os

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

def inspect():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    keywords = ["大米", "稻米", "酸奶", "牛奶", "苹果", "鸡蛋", "鸡胸", "猪肉", "牛肉", "面条", "面粉", "白菜", "豆腐", "番茄", "黄瓜"]
    for kw in keywords:
        cursor.execute("""
            SELECT food_name, food_category, calorie, protein, fat, carb, diet_fiber, gi_value, calcium
            FROM food WHERE food_name LIKE ? ORDER BY food_name
        """, (f"%{kw}%",))
        rows = cursor.fetchall()
        print(f"\n=== {kw} ({len(rows)}条) ===")
        for r in rows:
            print(f"  {r[0]} | {r[1]} | {r[2]}kcal | 蛋白{r[3]} | 脂肪{r[4]} | 碳水{r[5]} | 纤维{r[6]} | GI{r[7]} | 钙{r[8]}")

    conn.close()

if __name__ == "__main__":
    inspect()
