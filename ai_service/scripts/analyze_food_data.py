import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
categories = cursor.fetchall()
print("各类别分布:")
for cat, count in categories:
    print(f"  {cat}: {count} 条")

cursor.execute("SELECT food_name, food_category, calorie FROM food WHERE food_category = '其他' LIMIT 20")
other_foods = cursor.fetchall()
print("\n'其他'类别示例:")
for name, cat, cal in other_foods:
    print(f"  {name} ({cat}) - {cal}kcal")

cursor.execute("SELECT food_name, food_category, calorie FROM food WHERE food_category = '水果' LIMIT 20")
fruits = cursor.fetchall()
print("\n'水果'类别示例:")
for name, cat, cal in fruits:
    print(f"  {name} ({cat}) - {cal}kcal")

cursor.execute("SELECT AVG(calorie), AVG(protein), AVG(fat), AVG(carb) FROM food")
avg_nutrients = cursor.fetchone()
print(f"\n平均营养成分:")
print(f"  热量: {avg_nutrients[0]:.1f} kcal")
print(f"  蛋白质: {avg_nutrients[1]:.1f} g")
print(f"  脂肪: {avg_nutrients[2]:.1f} g")
print(f"  碳水: {avg_nutrients[3]:.1f} g")

conn.close()