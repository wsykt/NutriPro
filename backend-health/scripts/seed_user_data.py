# -*- coding: utf-8 -*-
"""
单用户真实测试环境数据填充脚本（seed_user_data.py）
====================================================
为「单用户本地真实测试环境」准备完整的测试数据：
  1. 检查/创建测试用户（张三，密码 123456）
  2. 近 7 天身体指标历史（weight/height/bmr）
  3. 今日三餐饮食记录（diet_meal + diet_item 通过 food_id 关联 food 表）
  4. 近 7 天运动记录

用法：
    python scripts/seed_user_data.py            # 填充到 health.db
    python scripts/seed_user_data.py --dry-run  # 仅预览

表结构说明（health.db 实际 schema）：
    user(id, username, password, gender, age, height, weight, crowd_type, role)
    body_metrics_history(history_id, user_id, record_date, weight, height, age, crowd_type, bmr)
    diet_meal(meal_id, user_id, eat_date, meal_type, remark)
    diet_item(item_id, meal_id, food_id, eat_weight)
    exercise_record(id, user_id, record_date, exercise_type, duration_min, calories_burned, note, status)
    food(food_id, food_name, food_category, calorie, protein, carb, fat, ...)
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import date, timedelta

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE, "data", "health.db")

# ============ 测试用户画像（可在此处替换为任意单用户） ============
TEST_USER = {
    "username": "张三",
    "password": "123456",
    "gender": "男",
    "age": 28,
    "height": 175.0,
    "weight": 70.0,
    "crowd_type": "普通人",
    "role": "user",
}

# ============ 近 7 天身体指标（体重缓慢下降趋势） ============
def weight_series():
    series = []
    start = 70.5
    for i in range(7):
        d = date.today() - timedelta(days=6 - i)
        w = round(start - i * 0.15, 1)
        bmr = round(10 * w + 6.25 * 175 - 5 * 28 + 5, 1)  # 男性 BMR
        series.append({"record_date": d.isoformat(), "weight": w, "height": 175.0,
                       "age": 28, "crowd_type": "普通人", "bmr": bmr})
    return series

# ============ 今日三餐（food_name → 克数） ============
MEALS = [
    {"eat_date": date.today().isoformat(), "meal_type": "早餐", "remark": "测试早餐",
     "items": [("牛奶", 250), ("鸡蛋", 50), ("小米粥", 60)]},
    {"eat_date": date.today().isoformat(), "meal_type": "午餐", "remark": "测试午餐",
     "items": [("鸡胸脯肉", 120), ("米饭", 150), ("西兰花", 120)]},
    {"eat_date": date.today().isoformat(), "meal_type": "晚餐", "remark": "测试晚餐",
     "items": [("三文鱼", 100), ("荞麦", 80), ("菠菜", 100)]},
]

# ============ 近 7 天运动记录 ============
EXERCISES = [
    ("跑步", 30, 280, "晨跑"),
    ("力量训练", 45, 210, "胸背核心训练"),
    ("散步", 60, 150, "晚饭后散步"),
    ("游泳", 40, 330, "游泳馆自由泳"),
    ("骑行", 50, 290, "通勤骑行"),
    ("瑜伽", 35, 90, "睡前拉伸"),
    ("篮球", 60, 360, "小区球场半场"),
]


def md5hex(s):
    import hashlib
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def bcrypt_hash(password: str) -> str:
    """BCrypt 哈希（$2a$ 前缀，兼容 Spring Security BCryptPasswordEncoder）"""
    if not HAS_BCRYPT:
        raise SystemExit("缺少 bcrypt 库，请先: pip install bcrypt")
    # prefix=b'2a' 与 Java BCryptPasswordEncoder 输出兼容
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10, prefix=b"2a")).decode("utf-8")


def dry_run_preview():
    print("=" * 60)
    print("单用户真实测试数据预览（--dry-run）")
    print("=" * 60)
    u = TEST_USER
    print(f"\n[用户] {u['username']} / {u['crowd_type']} / {u['gender']} {u['age']}岁 / "
          f"{u['height']}cm {u['weight']}kg")
    print("\n[近7天身体指标]")
    for s in weight_series():
        print(f"  {s['record_date']}: {s['weight']}kg BMR={s['bmr']}")
    print("\n[饮食记录]")
    for m in MEALS:
        print(f"  {m['eat_date']} {m['meal_type']}: {len(m['items'])}种食物")
        for name, g in m["items"]:
            print(f"      {name} {g}g")
    print("\n[运动记录]")
    for i, (t, dur, kcal, note) in enumerate(EXERCISES):
        d = (date.today() - timedelta(days=6 - i)).isoformat()
        print(f"  {d}: {t} {dur}min ~{kcal}kcal")
    print("\n提示: 去掉 --dry-run 即可写入数据库。")


def get_food_id(cur, food_name):
    """按名称查 food 表；支持模糊匹配（去除 生/熟 后缀差异）"""
    cur.execute("SELECT food_id FROM food WHERE food_name=? LIMIT 1", (food_name,))
    row = cur.fetchone()
    if row:
        return row[0]
    # 模糊匹配：food_name LIKE %关键词%
    cur.execute("SELECT food_id FROM food WHERE food_name LIKE ? LIMIT 1",
                (f"%{food_name}%",))
    row = cur.fetchone()
    if row:
        return row[0]
    print(f"  ⚠️ 未在 food 表找到: {food_name}（跳过该项）")
    return None


def seed():
    if not os.path.exists(os.path.dirname(DB)):
        os.makedirs(os.path.dirname(DB), exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 用户（幂等：存在则更新资料，同时刷新 BCrypt 密码）
    cur.execute("SELECT user_id FROM user WHERE username=?", (TEST_USER["username"],))
    row = cur.fetchone()
    pwd_hash = bcrypt_hash(TEST_USER["password"])
    if row:
        uid = row["user_id"]
        cur.execute(
            """UPDATE user SET gender=?, age=?, height=?, weight=?, crowd_type=?, role=?, password=?
               WHERE user_id=?""",
            (TEST_USER["gender"], TEST_USER["age"], TEST_USER["height"],
             TEST_USER["weight"], TEST_USER["crowd_type"], TEST_USER["role"], pwd_hash, uid),
        )
        print(f"[用户] 已更新: {TEST_USER['username']} (id={uid})")
    else:
        cur.execute(
            """INSERT INTO user (username, password, gender, age, height, weight, crowd_type, role)
               VALUES (?,?,?,?,?,?,?,?)""",
            (TEST_USER["username"], pwd_hash, TEST_USER["gender"], TEST_USER["age"],
             TEST_USER["height"], TEST_USER["weight"], TEST_USER["crowd_type"],
             TEST_USER["role"]),
        )
        uid = cur.lastrowid
        print(f"[用户] 已创建: {TEST_USER['username']} (id={uid})")

    # 2. 身体指标历史（幂等：同用户同日期覆盖）
    for s in weight_series():
        cur.execute("DELETE FROM body_metrics_history WHERE user_id=? AND record_date=?",
                    (uid, s["record_date"]))
        cur.execute(
            """INSERT INTO body_metrics_history
               (user_id, record_date, weight, height, age, crowd_type, bmr)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, s["record_date"], s["weight"], s["height"], s["age"],
             s["crowd_type"], s["bmr"]),
        )
    print(f"[身体指标] 已写入 {len(weight_series())} 天")

    # 3. 饮食记录（幂等：先删同用户同日期同餐次）
    meal_count = 0
    for m in MEALS:
        cur.execute("DELETE FROM diet_meal WHERE user_id=? AND eat_date=? AND meal_type=?",
                    (uid, m["eat_date"], m["meal_type"]))
        cur.execute(
            """INSERT INTO diet_meal (user_id, eat_date, meal_type, remark)
               VALUES (?,?,?,?)""",
            (uid, m["eat_date"], m["meal_type"], m.get("remark")),
        )
        meal_id = cur.lastrowid
        for food_name, eat_weight in m["items"]:
            food_id = get_food_id(cur, food_name)
            if food_id is None:
                continue
            cur.execute(
                """INSERT INTO diet_item (meal_id, food_id, eat_weight)
                   VALUES (?,?,?)""",
                (meal_id, food_id, eat_weight),
            )
        meal_count += 1
    print(f"[饮食] 已写入 {meal_count} 餐次（diet_item 关联 food_id）")

    # 4. 运动记录（幂等：先删同用户同日期）
    for i, (t, dur, kcal, note) in enumerate(EXERCISES):
        d = (date.today() - timedelta(days=6 - i)).isoformat()
        cur.execute("DELETE FROM exercise_record WHERE user_id=? AND record_date=?",
                    (uid, d))
        cur.execute(
            """INSERT INTO exercise_record
               (user_id, record_date, exercise_type, duration_min, calories_burned, note, status)
               VALUES (?,?,?,?,?,?,?)""",
            (uid, d, t, dur, kcal, note, "已完成"),
        )
    print(f"[运动] 已写入 {len(EXERCISES)} 天")

    conn.commit()
    conn.close()
    print(f"\n完成！数据库: {DB}")
    print("测试账号: " + TEST_USER["username"] + " / " + TEST_USER["password"])


def main():
    ap = argparse.ArgumentParser(description="单用户真实测试环境数据填充")
    ap.add_argument("--dry-run", action="store_true", help="仅预览不写入")
    args = ap.parse_args()
    if args.dry_run:
        dry_run_preview()
    else:
        seed()


if __name__ == "__main__":
    main()
