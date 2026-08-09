"""SQLite 连接统一封装（稳定性优化）

为项目内全部 SQLite 库统一提供：
- WAL 日志模式（读写并发，避免 database is locked）
- busy_timeout（写锁冲突时等待而非直接抛异常）
- 统一错误处理

用法：
    from utils.sqlite_utils import get_conn
    conn = get_conn(db_path)
    try:
        ...
    finally:
        conn.close()
"""
import sqlite3
import os
from typing import Optional


def get_conn(db_path: str, busy_timeout_ms: int = 5000) -> sqlite3.Connection:
    """创建带 WAL + busy_timeout 的 SQLite 连接"""
    if db_path and os.path.dirname(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    # 写锁冲突时最多等待 5s，避免并发写入直接抛 database is locked
    conn.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
    return conn


def init_db(db_path: str, ddl_statements: list, indexes: Optional[list] = None):
    """初始化数据库：建表 + 建索引（幂等）"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        for ddl in ddl_statements:
            cur.execute(ddl)
        for idx in (indexes or []):
            try:
                cur.execute(idx)
            except sqlite3.OperationalError:
                pass  # 索引已存在
        conn.commit()
    finally:
        conn.close()
