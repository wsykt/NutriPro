# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()
print("=== food ===")
for col in c.execute("PRAGMA table_info(food)").fetchall():
    print("  ", col[1], col[2])
print("\n=== food 示例 ===")
for r in c.execute("SELECT * FROM food LIMIT 5").fetchall():
    print("  ", r)
conn.close()
