# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db")
c = conn.cursor()
print("=== 用户 ===")
for r in c.execute("SELECT user_id, username, gender, age, height, weight, crowd_type FROM user WHERE username='张三'"):
    print(" ", r)
print("=== 身体指标 ===")
for r in c.execute("SELECT user_id, record_date, weight, height, bmr FROM body_metrics_history WHERE user_id=10 ORDER BY record_date"):
    print(" ", r)
print("=== 饮食（join）===")
for r in c.execute("""SELECT dm.meal_type, f.food_name, di.eat_weight
    FROM diet_meal dm JOIN diet_item di ON dm.meal_id=di.meal_id
    JOIN food f ON di.food_id=f.food_id WHERE dm.user_id=10"""):
    print(" ", r)
print("=== 运动 ===")
for r in c.execute("SELECT record_date, exercise_type, duration_min, calories_burned FROM exercise_record WHERE user_id=10 ORDER BY record_date"):
    print(" ", r)
conn.close()
