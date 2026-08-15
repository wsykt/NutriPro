"""清理婴幼儿食品和调整剩余问题"""
import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# 降低婴幼儿辅食的优先级（这些不是常用食物）
cursor.execute("""
    UPDATE food SET priority = 0 
    WHERE (food_name LIKE '%泥%' OR food_name LIKE '%阶段%' OR food_name LIKE '%亨氏%')
    AND food_name NOT LIKE '%土豆泥%' AND food_name NOT LIKE '%南瓜泥%'
""")
print(f"降低婴幼儿辅食优先级: {cursor.rowcount} 条")

# 合并鲜牛奶（代表值和全脂营养值几乎相同）
cursor.execute("""
    SELECT food_id, food_name, calorie, protein, fat, carb 
    FROM food WHERE food_name LIKE '鲜牛奶%' ORDER BY food_id
""")
milk_records = cursor.fetchall()
print(f"\n鲜牛奶记录:")
for r in milk_records:
    print(f"  {r}")

# 删除重复的鲜牛奶(全脂)，保留代表值
cursor.execute("""
    DELETE FROM food WHERE food_name = '鲜牛奶(全脂)' 
    AND food_id NOT IN (SELECT MIN(food_id) FROM food WHERE food_name = '鲜牛奶(全脂)')
""")
print(f"删除重复鲜牛奶: {cursor.rowcount} 条")

# 最终统计
cursor.execute("SELECT COUNT(*) FROM food")
total = cursor.fetchone()[0]
print(f"\n最终记录数: {total}")

# 显示前20条常用食物
print("\n顶级常用食物(优先级11, 前15条):")
cursor.execute("""
    SELECT food_name, food_category, calorie, protein 
    FROM food WHERE priority = 11 
    ORDER BY food_category, food_name LIMIT 15
""")
for name, cat, cal, prot in cursor.fetchall():
    print(f"  [{cat}] {name}: {cal}kcal, 蛋白{prot}g")

conn.commit()
conn.close()
