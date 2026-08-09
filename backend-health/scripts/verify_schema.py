# -*- coding: utf-8 -*-
"""验证 init-schema.sql 幂等性 + SC-002 唯一索引落库"""
import sqlite3

DB = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"
SQL = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\src\main\resources\db\init-schema.sql"

conn = sqlite3.connect(DB)
c = conn.cursor()
sql = open(SQL, encoding="utf-8").read()
c.executescript(sql)
print("init-schema.sql 幂等执行成功（第1次）")
c.executescript(sql)
print("init-schema.sql 幂等执行成功（第2次）")

rows = c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'uq_%'").fetchall()
print("唯一索引:", [r[0] for r in rows])

rows2 = c.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'").fetchall()
print("普通索引数:", len(rows2))
conn.close()
