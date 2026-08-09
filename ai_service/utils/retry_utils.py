"""通用重试装饰器

提供三种重试风格：
1. retry_decorator — 通用指数退避重试，适用于 LLM 调用
2. chromadb_retry — ChromaDB 专用锁冲突重试
3. simple_retry — 简单固定间隔重试
"""

import time
import functools
import random
from typing import Callable, Optional, Type, Tuple


def retry_decorator(
    max_retries: int = 2,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """通用重试装饰器，支持指数退避和抖动

    参数:
        max_retries: 最大重试次数
        base_delay: 初始延迟秒数
        max_delay: 最大延迟秒数
        exponential: 是否指数退避（否则固定间隔）
        exceptions: 捕获的异常类型元组
        on_retry: 每次重试前的回调，入参为(异常对象, 当前重试次数)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        if exponential:
                            delay = min(
                                base_delay * (2 ** attempt) + random.uniform(0, 0.5),
                                max_delay
                            )
                        else:
                            delay = base_delay
                        if on_retry:
                            on_retry(e, attempt + 1)
                        time.sleep(delay)
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator


def chromadb_retry(func=None, max_retries=3, base_delay=0.5):
    """ChromaDB 专用重试装饰器

    用于处理多并发访问时的 database locked / database 异常
    仅在检测到 'database' 或 'locked' 关键字时重试，其他异常直接抛出

    用法:
        @chromadb_retry
        def search(...): ...

        @chromadb_retry(max_retries=5, base_delay=1.0)
        def add(...): ...
    """
    if func is None:
        return lambda f: chromadb_retry(f, max_retries=max_retries, base_delay=base_delay)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import chromadb.errors
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except chromadb.errors.ChromaDBError as e:
                last_exception = e
                error_lower = str(e).lower()
                if "database" in error_lower or "locked" in error_lower:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt) + 0.1
                        time.sleep(delay)
                        continue
                raise
            except Exception as e:
                # 非 ChromaDB 异常也捕获 database locked 模式
                error_lower = str(e).lower()
                if ("database" in error_lower or "locked" in error_lower) and attempt < max_retries:
                    last_exception = e
                    delay = base_delay * (2 ** attempt) + 0.1
                    time.sleep(delay)
                    continue
                raise
        raise last_exception
    return wrapper


def simple_retry(max_retries: int = 3, delay: float = 0.5):
    """简单固定间隔重试装饰器"""
    return retry_decorator(
        max_retries=max_retries,
        base_delay=delay,
        exponential=False,
    )
