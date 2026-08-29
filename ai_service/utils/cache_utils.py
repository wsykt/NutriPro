"""SQLite 持久化缓存

替代原有纯内存字典 SimpleCache，提供：
- SQLite 持久化存储（服务重启不丢失）
- TTL 过期自动清理（后台线程每 60s 扫描）
- LRU 淘汰策略（超出 max_size 时淘汰 access_count 最少条目）
- 保持原有 API 兼容：get() / set() / clear() / size() / has()
"""

import sqlite3
import json
import time
import threading
import hashlib
import os
from typing import Any, Optional
from config.settings import settings
from utils.sqlite_utils import get_conn


class PersistentCache:
    """基于 SQLite 的持久化缓存"""

    def __init__(self, cache_name: str, max_size: int = 1000, ttl_seconds: int = 3600):
        self.cache_name = cache_name
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._db_path = settings.CACHE_DB_PATH

        # 确保缓存目录存在
        cache_dir = os.path.dirname(self._db_path)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

        self._init_db()
        self._start_cleanup_thread()

    def _init_db(self):
        self._execute(
            """CREATE TABLE IF NOT EXISTS cache_entries (
                id TEXT PRIMARY KEY,
                cache_name TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )"""
        )
        self._execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_name ON cache_entries(cache_name)"
        )

    def _get_conn(self) -> sqlite3.Connection:
        return get_conn(self._db_path)

    def _execute(self, sql: str, params: tuple = ()):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _query(self, sql: str, params: tuple = ()) -> list:
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        finally:
            conn.close()

    def _get_key(self, *args, **kwargs) -> str:
        key_parts = []
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _start_cleanup_thread(self):
        def cleanup():
            backoff = 1  # 秒；异常时指数退避重启
            while True:
                try:
                    cutoff = time.time() - self.ttl_seconds
                    self._execute(
                        "DELETE FROM cache_entries WHERE cache_name=? AND created_at < ?",
                        (self.cache_name, cutoff)
                    )
                    # LRU 淘汰：超出 max_size 时删除 access_count 最少的条目
                    count_row = self._query(
                        "SELECT COUNT(*) FROM cache_entries WHERE cache_name=?",
                        (self.cache_name,)
                    )
                    if count_row and count_row[0][0] > self.max_size:
                        excess = count_row[0][0] - self.max_size
                        self._execute(
                            """DELETE FROM cache_entries WHERE id IN (
                                SELECT id FROM cache_entries WHERE cache_name=?
                                ORDER BY access_count ASC LIMIT ?
                            )""",
                            (self.cache_name, excess)
                        )
                    backoff = 1  # 成功一轮后重置
                except Exception:
                    # 单轮失败不终止线程，指数退避后继续
                    backoff = min(backoff * 2, 60)
                time.sleep(60 + backoff)

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def get(self, *args, **kwargs) -> Optional[Any]:
        key = self._get_key(*args, **kwargs)
        rows = self._query(
            "SELECT value, created_at FROM cache_entries WHERE id=? AND cache_name=?",
            (key, self.cache_name)
        )
        if not rows:
            return None
        value_json, created_at = rows[0]
        if time.time() - created_at > self.ttl_seconds:
            self._execute("DELETE FROM cache_entries WHERE id=?", (key,))
            return None
        # 更新访问计数（LRU 跟踪）
        self._execute(
            "UPDATE cache_entries SET access_count = access_count + 1 WHERE id=?",
            (key,)
        )
        try:
            return json.loads(value_json)
        except json.JSONDecodeError:
            return None

    def set(self, value: Any, *args, **kwargs) -> None:
        key = self._get_key(*args, **kwargs)
        value_json = json.dumps(value, ensure_ascii=False)
        now = time.time()
        self._execute(
            """INSERT OR REPLACE INTO cache_entries (id, cache_name, value, created_at, access_count)
               VALUES (?, ?, ?, ?, 0)""",
            (key, self.cache_name, value_json, now)
        )

    def clear(self) -> None:
        self._execute("DELETE FROM cache_entries WHERE cache_name=?", (self.cache_name,))

    def size(self) -> int:
        rows = self._query(
            "SELECT COUNT(*) FROM cache_entries WHERE cache_name=?",
            (self.cache_name,)
        )
        return rows[0][0] if rows else 0

    def has(self, *args, **kwargs) -> bool:
        key = self._get_key(*args, **kwargs)
        rows = self._query(
            "SELECT created_at FROM cache_entries WHERE id=? AND cache_name=?",
            (key, self.cache_name)
        )
        if not rows:
            return False
        if time.time() - rows[0][0] > self.ttl_seconds:
            self._execute("DELETE FROM cache_entries WHERE id=?", (key,))
            return False
        return True


# ===== 全局缓存实例（替换原有 SimpleCache，保持 API 兼容）=====

conversation_cache = PersistentCache("conversation", max_size=500, ttl_seconds=3600)
retrieve_cache = PersistentCache("retrieve", max_size=200, ttl_seconds=1800)
agent_result_cache = PersistentCache("agent_result", max_size=300, ttl_seconds=7200)


def cache_conversation_response(user_id: int, message: str, response: Any) -> None:
    conversation_cache.set(response, user_id=user_id, message=message)


def get_cached_conversation_response(user_id: int, message: str) -> Optional[Any]:
    return conversation_cache.get(user_id=user_id, message=message)


def cache_retrieve_result(query: str, target_crowd: str, results: Any) -> None:
    retrieve_cache.set(results, query=query, target_crowd=target_crowd)


def get_cached_retrieve_result(query: str, target_crowd: str) -> Optional[Any]:
    return retrieve_cache.get(query=query, target_crowd=target_crowd)


def cache_agent_result(agent_name: str, user_id: int, params_hash: str, result: Any) -> None:
    agent_result_cache.set(result, agent_name=agent_name, user_id=user_id, params_hash=params_hash)


def get_cached_agent_result(agent_name: str, user_id: int, params_hash: str) -> Optional[Any]:
    return agent_result_cache.get(agent_name=agent_name, user_id=user_id, params_hash=params_hash)
