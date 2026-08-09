# -*- coding: utf-8 -*-
"""导出 health.db 的完整建表 SQL 基线（SC-003 产物 init-schema.sql）"""
import sqlite3

DB = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"
OUT = r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\src\main\resources\db\init-schema.sql"

conn = sqlite3.connect(DB)
c = conn.cursor()

# 按 sqlite_master 中的 sql 原文导出（保持与 Hibernate 自动建表一致的 DDL）
rows = c.execute(
    "SELECT type, name, sql FROM sqlite_master "
    "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
).fetchall()

lines = []
lines.append("-- ============================================================")
lines.append("-- SC-003 建表 SQL 基线（init-schema.sql）")
lines.append("-- 记录：SQL建表演进报告.md → 四、持续优化记录 → SC-003")
lines.append("-- 来源：由 health.db 的 sqlite_master 自动导出（2026-08-09）")
lines.append("-- 定位：阶段二交付物，冻结期切换 ddl-auto: none 后用于幂等建表")
lines.append("-- 注意：Hibernate 后续新增字段时需同步更新本文件")
lines.append("-- ============================================================")
lines.append("")

for type_, name, sql in rows:
    if not sql:
        continue
    lines.append("-- ------------------------------------------------------------")
    lines.append(f"-- {type_.upper()} : {name}")
    lines.append("-- ------------------------------------------------------------")
    # 幂等化：CREATE TABLE/INDEX/UNIQUE INDEX → IF NOT EXISTS
    s = sql.rstrip(";")
    if s.strip().upper().startswith("CREATE TABLE"):
        s = s.replace("CREATE TABLE", "CREATE TABLE IF NOT EXISTS", 1)
    elif s.strip().upper().startswith("CREATE UNIQUE INDEX"):
        s = s.replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS", 1)
    elif s.strip().upper().startswith("CREATE INDEX"):
        s = s.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS", 1)
    lines.append(s + ";")
    lines.append("")

# 附加 SC-001 索引 与 SC-002 唯一约束（合并进基线，保证基线完整）
index_sql = open(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\src\main\resources\db\index_optimizations.sql", encoding="utf-8").read()
unique_sql = open(r"c:\Users\13425\Desktop\个人健康助手\health\backend-health\src\main\resources\db\unique_constraints.sql", encoding="utf-8").read()
lines.append("")
lines.append("-- ============================================================")
lines.append("-- SC-001 高频查询索引（合并自 index_optimizations.sql）")
lines.append("-- ============================================================")
lines.append("")
for line in index_sql.splitlines():
    if line.strip() and not line.strip().startswith("--"):
        lines.append(line)
lines.append("")
lines.append("-- ============================================================")
lines.append("-- SC-002 唯一约束（合并自 unique_constraints.sql）")
lines.append("-- ============================================================")
lines.append("")
for line in unique_sql.splitlines():
    if line.strip() and not line.strip().startswith("--"):
        lines.append(line)
lines.append("")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"已导出 {len(rows)} 个对象到 {OUT}")
conn.close()
