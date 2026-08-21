# -*- coding: utf-8 -*-
"""
为 yyy(user_id=9) 插入 2026-07-01 ~ 2026-08-18 一个多月的健康数据：
- 每日三餐饮食（diet_meal + diet_item）
- 每周 4 次运动（exercise_record）
- 每周 2 条体重记录（body_metrics_history，67.2 -> 65.2 平缓下降）
先删除该用户原有相关数据，保证无重复。
"""
import sqlite3, random, datetime

DB = r'c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db'
UID = 9

conn = sqlite3.connect(DB, timeout=60)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def ts(d: datetime.date, hh, mm):
    dt = datetime.datetime(d.year, d.month, d.day, hh, mm)
    return int(dt.timestamp() * 1000)

# ---------- 1. 删除 yyy 原有数据 ----------
cur.execute("DELETE FROM diet_item WHERE meal_id IN (SELECT meal_id FROM diet_meal WHERE user_id=?)", (UID,))
cur.execute("DELETE FROM diet_meal WHERE user_id=?", (UID,))
cur.execute("DELETE FROM exercise_record WHERE user_id=?", (UID,))
cur.execute("DELETE FROM body_metrics_history WHERE user_id=?", (UID,))
print('deleted old data for user 9')

# ---------- 2. 饮食 ----------
# 餐食模板：(食物id, 克数)
breakfasts = [
    [(1, 250), (21, 50), (613, 100)],          # 牛奶+鸡蛋+馒头
    [(4, 150), (21, 50), (613, 100)],          # 酸奶+鸡蛋+馒头
    [(334, 200), (21, 50), (283, 150)],        # 豆浆+鸡蛋+红薯
    [(1, 250), (21, 50), (288, 200)],          # 牛奶+鸡蛋+小米粥
    [(3, 250), (21, 50), (613, 100), (499, 100)],  # 脱脂奶+鸡蛋+馒头+苹果
]
lunches = [
    [(287, 300), (144, 200), (383, 200), (897, 100)],   # 米饭+鸡胸+西兰花+番茄
    [(287, 250), (17, 100), (330, 100), (361, 150)],    # 米饭+牛肉+豆腐+黄瓜
    [(287, 250), (162, 150), (912, 100), (358, 100)],   # 米饭+虾+胡萝卜+菠菜
    [(286, 150), (145, 100), (361, 100), (897, 100)],   # 面条+鸡腿+黄瓜+番茄
    [(287, 250), (161, 150), (383, 150), (897, 100)],   # 米饭+三文鱼+西兰花+番茄
]
dinners = [
    [(287, 250), (165, 200), (383, 200), (897, 100)],   # 米饭+鲈鱼+西兰花+番茄
    [(283, 250), (144, 150), (361, 150)],               # 红薯+鸡胸+黄瓜
    [(286, 100), (21, 50), (358, 100), (897, 100)],     # 面条+鸡蛋+菠菜+番茄
    [(287, 200), (145, 150), (383, 150), (874, 100)],   # 米饭+鸡腿+西兰花+樱桃番茄
    [(287, 250), (16, 100), (361, 100), (383, 150)],    # 米饭+猪肉+黄瓜+西兰花
]
snacks = [   # 加餐（部分天）
    [(499, 150)], [(500, 100)], [(501, 150)], [(502, 100)],
]
meal_slots = [('早餐', breakfasts, (8, 0)), ('午餐', lunches, (12, 0)), ('晚餐', dinners, (18, 30))]

random.seed(9)
d = datetime.date(2026, 7, 1)
end = datetime.date(2026, 8, 17)
meal_count = 0
item_count = 0
while d <= end:
    pick_idx = {}
    for name, tpls, (hh, mm) in meal_slots:
        day_key = (d - datetime.date(2026, 7, 1)).days
        idx = (day_key + (0 if name == '早餐' else 1 if name == '午餐' else 2)) % len(tpls)
        cur.execute(
            "INSERT INTO diet_meal (created_at, eat_date, meal_type, remark, user_id) VALUES (?,?,?,?,?)",
            (ts(d, hh, mm), d.isoformat(), name, '', UID))
        mid = cur.lastrowid
        meal_count += 1
        for food_id, grams in tpls[idx]:
            cur.execute("INSERT INTO diet_item (eat_weight, food_id, meal_id) VALUES (?,?,?)",
                        (grams, food_id, mid))
            item_count += 1
    # 周末加餐（周六/周日 15:00）
    if d.weekday() in (5, 6):
        cur.execute("INSERT INTO diet_meal (created_at, eat_date, meal_type, remark, user_id) VALUES (?,?,?,?,?)",
                    (ts(d, 15, 0), d.isoformat(), '加餐', '', UID))
        mid = cur.lastrowid
        meal_count += 1
        for food_id, grams in random.choice(snacks):
            cur.execute("INSERT INTO diet_item (eat_weight, food_id, meal_id) VALUES (?,?,?)",
                        (grams, food_id, mid))
            item_count += 1
    d += datetime.timedelta(days=1)

# ---------- 3. 运动：每周 4 次（一/三/五/六），类型轮换 ----------
exercises = [
    ('跑步', 30, 280), ('跳绳', 20, 220), ('快走', 40, 180),
    ('游泳', 40, 300), ('骑行', 45, 260),
]
ex_count = 0
d = datetime.date(2026, 7, 1)
ex_day = 0
while d <= end:
    if d.weekday() in (0, 2, 4, 5):  # 一 三 五 六
        name, dur, kcal = exercises[ex_day % len(exercises)]
        cur.execute(
            "INSERT INTO exercise_record (calories_burned, created_at, duration_min, exercise_type, note, record_date, status, user_id) VALUES (?,?,?,?,?,?,?,?)",
            (kcal, ts(d, 19, 0), dur, name, '日常锻炼', d.isoformat(), 'approved', UID))
        ex_count += 1
        ex_day += 1
    d += datetime.timedelta(days=1)

# ---------- 4. 体重：每周 2 条（一/四），67.2 -> 65.2 线性下降 ----------
w0, w1 = 67.2, 65.2
start, stop = datetime.date(2026, 7, 1), datetime.date(2026, 8, 14)
total_days = (stop - start).days
wt_count = 0
d = start
while d <= stop:
    if d.weekday() in (0, 3):
        frac = (d - start).days / total_days
        w = round(w0 + (w1 - w0) * frac, 1)
        cur.execute(
            "INSERT INTO body_metrics_history (age, bmr, crowd_type, height, record_date, user_id, weight) VALUES (?,?,?,?,?,?,?)",
            (25, 1592.5, '普通人', 170.0, d.isoformat(), UID, w))
        wt_count += 1
    d += datetime.timedelta(days=1)

conn.commit()
print(f'done: meals={meal_count}, items={item_count}, exercises={ex_count}, weights={wt_count}')
conn.close()
