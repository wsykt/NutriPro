# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()
for t in ["user", "body_metrics_history", "diet_meal", "diet_item", "exercise_record"]:
    print(f"\n=== {t} ===")
    cols = c.execute(f"PRAGMA table_info({t})").fetchall()
    for col in cols:
        print("  ", col[1], col[2])
conn.close()
