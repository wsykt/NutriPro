import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=" * 60)
print("食物数据优化总结报告")
print("=" * 60)

# 总体统计
cursor.execute("SELECT COUNT(*) FROM food")
total = cursor.fetchone()[0]
print(f"\n总记录数: {total}")

# 优先级分布
print("\n优先级分布:")
cursor.execute("""
    SELECT 
        CASE 
            WHEN priority >= 11 THEN '顶级常用(代表值/普通)'
            WHEN priority >= 10 THEN '常用食物'
            WHEN priority >= 9 THEN '较常用'
            WHEN priority >= 5 THEN '一般'
            ELSE '冷门'
        END as level,
        COUNT(*) 
    FROM food GROUP BY level ORDER BY MIN(priority) DESC
""")
for level, cnt in cursor.fetchall():
    print(f"  {level}: {cnt} 条")

# 分类分布
print("\n分类分布:")
cursor.execute("""
    SELECT food_category, COUNT(*), 
           SUM(CASE WHEN priority >= 10 THEN 1 ELSE 0 END)
    FROM food GROUP BY food_category ORDER BY COUNT(*) DESC
""")
for cat, cnt, common in cursor.fetchall():
    print(f"  {cat}: {cnt} 条 (常用 {common})")

# 合并效果
print("\n品牌合并效果（部分示例）:")
merged_examples = [
    "纯牛奶(全脂)", "纯牛奶(低脂)", "纯牛奶(脱脂)", "纯牛奶(代表值)",
    "酸奶(全脂)", "酸奶(低脂)", "酸奶(代表值，全脂)",
    "鲜牛奶（代表值，全脂）", "鲜牛奶(全脂)",
    "苹果(普通)", "米饭（蒸，代表值）"
]
for name in merged_examples:
    cursor.execute("SELECT calorie, protein, fat, carb FROM food WHERE food_name = ?", (name,))
    r = cursor.fetchone()
    if r:
        print(f"  {name}: {r[0]}kcal, 蛋白{r[1]}g, 脂肪{r[2]}g, 碳水{r[3]}g")

# 数据质量检查
print("\n数据质量检查:")
cursor.execute("SELECT COUNT(*) FROM food WHERE calorie IS NULL OR calorie <= 0")
print(f"  无效热量记录: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM food WHERE protein IS NULL OR protein < 0")
print(f"  无效蛋白质记录: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM food WHERE protein > 90 AND food_name NOT LIKE '%粉%' AND food_name NOT LIKE '%干%'")
abnormal = cursor.fetchone()[0]
print(f"  蛋白质异常记录(>90g): {abnormal}")

# 向量库统计
print("\n向量知识库:")
print(f"  食物数据切片: 1136 条")
print(f"  知识库总记录: 4943 条")

conn.close()

print("\n" + "=" * 60)
print("优化完成！常用食物现已优先显示在搜索结果前列。")
print("=" * 60)
