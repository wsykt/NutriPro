"""AI 服务异步任务管理（阶段一·举措5）

将耗时的 LLM 任务（科普文章生成 / 一日饮食方案 / 食材菜谱推荐 / 个性化运动方案 /
营养分析等）从 FastAPI 事件循环卸载到受控线程池执行，避免同步 LLM 调用阻塞整个服务：

1. 通用异步任务接口：
   - POST /api/v1/tasks/submit     → 立即返回 task_id
   - GET  /api/v1/tasks/{task_id}  → 轮询进度与结果
2. 现有长任务端点统一经 run_in_thread 卸载（等价 asyncio.to_thread，但线程数受控）

线程池大小 = MAX_LLM_CONCURRENCY（默认 5），与 LLM 并发上限对齐，
防止并发请求打爆本地 Ollama / 云端 DeepSeek。

状态机：PENDING → RUNNING → SUCCESS / FAILED
"""

import asyncio
import functools
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional

from config.settings import settings
from utils.log_config import get_logger

logger = get_logger("async_task")

_MAX_RETAINED_TASKS = 200
_MAX_WORKERS = max(2, getattr(settings, "MAX_LLM_CONCURRENCY", 5))


class AsyncTaskService:
    """线程池任务管理：提交即返回 task_id，后台线程执行并登记状态"""

    def __init__(self) -> None:
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=_MAX_WORKERS,
            thread_name_prefix="ai-task",
        )

    # ---------------- 对外接口 ----------------

    def submit(self, task_type: str, fn: Callable, *args, **kwargs) -> str:
        """提交任务到后台线程池，立即返回 task_id"""
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._tasks[task_id] = {
                "task_id": task_id,
                "type": task_type,
                "status": "PENDING",
                "message": "任务已提交，等待线程池调度",
                "submit_time": time.time(),
                "finish_time": None,
                "elapsed_ms": None,
            }
            self._trim_locked()
        logger.info(f"异步任务已提交 task_id={task_id} type={task_type}")
        self._executor.submit(self._run, task_id, fn, args, kwargs)
        return task_id

    def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """查询任务状态（返回快照副本，防止外部修改内部状态）"""
        with self._lock:
            task = self._tasks.get(task_id)
            return dict(task) if task else None

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """最近任务列表（按提交时间倒序）"""
        with self._lock:
            items = [dict(t) for t in self._tasks.values()]
        items.sort(key=lambda t: t.get("submit_time", 0), reverse=True)
        return items[:limit]

    def shutdown(self) -> None:
        """关闭线程池（应用退出时调用）"""
        self._executor.shutdown(wait=False, cancel_futures=True)

    # ---------------- 内部实现 ----------------

    def _run(self, task_id: str, fn: Callable, args: tuple, kwargs: dict) -> None:
        self._update(task_id, status="RUNNING", message="任务执行中...")
        start = time.time()
        try:
            result = fn(*args, **kwargs)
            elapsed_ms = round((time.time() - start) * 1000, 1)
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.update(
                        status="SUCCESS", message="任务执行成功",
                        result=result, finish_time=time.time(), elapsed_ms=elapsed_ms,
                    )
            logger.info(f"异步任务完成 task_id={task_id} elapsed_ms={elapsed_ms}")
        except Exception as e:
            elapsed_ms = round((time.time() - start) * 1000, 1)
            logger.exception(f"异步任务失败 task_id={task_id}")
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.update(
                        status="FAILED", message="任务执行失败",
                        error=str(e), finish_time=time.time(), elapsed_ms=elapsed_ms,
                    )

    def _update(self, task_id: str, **fields) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                task.update(fields)

    def _trim_locked(self) -> None:
        """容量控制：仅清理已完成任务，运行中任务不受影响（调用方需持有锁）"""
        if len(self._tasks) <= _MAX_RETAINED_TASKS:
            return
        done = [k for k, v in self._tasks.items()
                if v.get("status") in ("SUCCESS", "FAILED")]
        overflow = len(self._tasks) - _MAX_RETAINED_TASKS
        for key in done[:overflow]:
            del self._tasks[key]


async_task_service = AsyncTaskService()


async def run_in_thread(fn: Callable, *args, **kwargs) -> Any:
    """将阻塞调用卸载到受控线程池执行。

    等价于 asyncio.to_thread，但复用 AI 服务的受控线程池，
    并发上限与 MAX_LLM_CONCURRENCY 对齐，避免并发请求打爆模型服务。
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        async_task_service._executor,
        functools.partial(fn, *args, **kwargs),
    )
