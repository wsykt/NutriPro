import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=== 酸奶类（合并后）===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, priority FROM food WHERE food_name LIKE '%酸奶%' AND food_name NOT LIKE '%疙瘩%' ORDER BY priority DESC, food_name")
for r in cursor.fetchall():
    print(f"  [P{r[5]}] {r[0]}: {r[1]}kcal, 蛋白{r[2]}, 脂肪{r[3]}, 碳水{r[4]}")

print("\n=== 纯牛奶类（合并后）===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, priority FROM food WHERE food_name LIKE '%纯牛奶%' ORDER BY priority DESC, food_name")
for r in cursor.fetchall():
    print(f"  [P{r[5]}] {r[0]}: {r[1]}kcal, 蛋白{r[2]}, 脂肪{r[3]}, 碳水{r[4]}")

print("\n=== 苹果类（合并后）===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, priority FROM food WHERE food_name LIKE '%苹果%' ORDER BY priority DESC, food_name")
for r in cursor.fetchall():
    print(f"  [P{r[5]}] {r[0]}: {r[1]}kcal, 蛋白{r[2]}, 脂肪{r[3]}, 碳水{r[4]}")

print("\n=== 鲜牛奶类（合并后）===")
cursor.execute("SELECT food_name, calorie, protein, fat, carb, priority FROM food WHERE food_name LIKE '%鲜牛奶%' ORDER BY priority DESC, food_name")
for r in cursor.fetchall():
    print(f"  [P{r[5]}] {r[0]}: {r[1]}kcal, 蛋白{r[2]}, 脂肪{r[3]}, 碳水{r[4]}")

print("\n=== 搜索'牛奶'前10条（按优先级）===")
cursor.execute("SELECT food_name, calorie, priority FROM food WHERE food_name LIKE '%牛奶%' ORDER BY priority DESC, food_id ASC LIMIT 10")
for r in cursor.fetchall():
    print(f"  [P{r[2]}] {r[0]}: {r[1]}kcal")

print("\n=== 搜索'米饭'前10条（按优先级）===")
cursor.execute("SELECT food_name, calorie, priority FROM food WHERE food_name LIKE '%米饭%' OR food_name LIKE '%大米%' OR food_name LIKE '%稻米%' ORDER BY priority DESC, food_id ASC LIMIT 10")
for r in cursor.fetchall():
    print(f"  [P{r[2]}] {r[0]}: {r[1]}kcal")

conn.close()
