# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()
for kw in ["面包", "鸡胸", "鸡", "米饭", "大米", "藜", "三文鱼", "鲑鱼", "西兰花", "花椰菜", "菠菜", "牛奶", "鸡蛋", "蛋"]:
    rows = c.execute("SELECT food_id, food_name, food_category FROM food WHERE food_name LIKE ? AND status='approved'",
                     (f"%{kw}%",)).fetchall()
    print(f"[{kw}] {rows}")
conn.close()
