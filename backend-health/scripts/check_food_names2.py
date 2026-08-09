# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()
for kw in ["面包", "麦", "粥", "面"]:
    rows = c.execute("SELECT food_id, food_name, food_category, priority FROM food WHERE food_name LIKE ? AND status='approved' LIMIT 15",
                     (f"%{kw}%",)).fetchall()
    print(f"[{kw}] {rows}")
conn.close()
