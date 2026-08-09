#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 food 表新增 show_gi / show_folic_acid / show_dha 字段
并根据食物类别回填可见性标记
"""
import os
import sqlite3

DB_PATH = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

CATEGORY_VISIBILITY = {
    "主食": (1, 1, 0),
    "肉蛋类": (0, 0, 0),
    "水产": (0, 1, 1),
    "蔬菜": (1, 1, 0),
    "水果": (1, 0, 0),
    "豆制品": (1, 1, 0),
    "奶类": (1, 0, 0),
    "油脂类": (0, 0, 0),
    "零食": (1, 0, 0),
}


def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols


def ensure_column(conn, table, column, col_type, default=None):
    if column_exists(conn, table, column):
        print(f"  列 {column} 已存在，跳过")
        return
    sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
    if default is not None:
        sql += f" DEFAULT {default}"
    print(f"  新增列: {sql}")
    conn.execute(sql)


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"数据库不存在: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    print("=" * 50)
    print("Food 表字段可见性迁移")
    print("=" * 50)

    ensure_column(conn, "food", "show_gi", "INTEGER", 0)
    ensure_column(conn, "food", "show_folic_acid", "INTEGER", 0)
    ensure_column(conn, "food", "show_dha", "INTEGER", 0)
    conn.commit()

    print("\n按类别回填 show_gi / show_folic_acid / show_dha：")
    total_updated = 0
    for cat, (sg, sf, sd) in CATEGORY_VISIBILITY.items():
        cur = conn.execute(
            "UPDATE food SET show_gi=?, show_folic_acid=?, show_dha=? WHERE food_category=?",
            (sg, sf, sd, cat),
        )
        print(f"  {cat:8s}: 更新 {cur.rowcount:4d} 条 -> show_gi={sg} show_folic_acid={sf} show_dha={sd}")
        total_updated += cur.rowcount
    conn.commit()

    # 未覆盖的类别统一设为 0/0/0
    cur = conn.execute(
        "UPDATE food SET show_gi=0, show_folic_acid=0, show_dha=0 "
        "WHERE food_category NOT IN (?,?,?,?,?,?,?,?,?)",
        tuple(CATEGORY_VISIBILITY.keys()),
    )
    if cur.rowcount:
        print(f"  其他类别: 更新 {cur.rowcount} 条 -> 全部设为 0")
        total_updated += cur.rowcount
    conn.commit()

    print(f"\n共更新 {total_updated} 条记录")

    # 统计
    print("\n迁移后各字段分布：")
    for col in ("show_gi", "show_folic_acid", "show_dha"):
        cur = conn.execute(f"SELECT COUNT(*) FROM food WHERE {col}=1")
        count = cur.fetchone()[0]
        print(f"  {col}=1 的记录数: {count}")

    conn.close()
    print("\n迁移完成！")


if __name__ == "__main__":
    migrate()
