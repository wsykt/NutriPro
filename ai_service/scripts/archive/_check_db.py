# -*- coding: utf-8 -*-
"""查看食材库和食谱库完整数据"""
import sqlite3
import json

DB = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# ===== 食材库 =====
print("=" * 80)
print("【食材库】")
print("=" * 80)

cur.execute("SELECT food_category, COUNT(*) as cnt FROM food GROUP BY food_category ORDER BY cnt DESC")
cats = cur.fetchall()
print(f"\n分类统计 ({sum(c['cnt'] for c in cats)} 条):")
for c in cats:
    print(f"  {c['food_category']}: {c['cnt']} 条")

# 每类挑5个高优先级食材
print("\n各类常用食材:")
for c in cats:
    cat = c['food_category']
    cur.execute("SELECT food_id, food_name, priority FROM food WHERE food_category=? ORDER BY priority DESC LIMIT 5", (cat,))
    rows = cur.fetchall()
    names = [f"{r['food_name']}(p={r['priority']})" for r in rows]
    print(f"  [{cat}] {names}")

# ===== 食谱库 =====
print("\n" + "=" * 80)
print("【食谱库】")
print("=" * 80)

cur.execute("SELECT COUNT(*) as cnt FROM recipes")
total = cur.fetchone()['cnt']
print(f"\n总数: {total} 条")

# recipe_ingredients 表结构
cur.execute("PRAGMA table_info(recipe_ingredients)")
print("\nrecipe_ingredients 表结构:")
for col in cur.fetchall():
    print(f"  {col[1]} ({col[2]})")

# 查食谱+食材
cur.execute("""
    SELECT r.recipe_id, r.recipe_name, r.description, r.tags,
           GROUP_CONCAT(ri.ingredient_name || ' ' || COALESCE(ri.amount,'') || ri.unit, ', ') as ings
    FROM recipes r
    LEFT JOIN recipe_ingredients ri ON r.recipe_id = ri.recipe_id
    GROUP BY r.recipe_id
    ORDER BY r.recipe_id
""")
recipes = cur.fetchall()
for r in recipes:
    print(f"\n  [{r['recipe_id']}] {r['recipe_name']}")
    print(f"      tags: {r['tags']}")
    print(f"      desc: {(r['description'] or '')[:80]}")
    print(f"      食材: {r['ings'] or '(空)'}")

conn.close()
