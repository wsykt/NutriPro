"""日志统一配置工具

基于 loguru 提供结构化 JSON 日志，支持：
- 按日期自动分割日志文件
- 30 天后自动清理过期日志
- 区分 INFO/ERROR 日志文件
- TraceID 自动注入
"""

import os
import sys
import json
import logging
from pathlib import Path

# 尝试导入 loguru，失败则降级到标准 logging
try:
    from loguru import logger as _logger
    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    _logger = logging.getLogger("ai_core")


# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


def setup_logging(env: str = "dev", trace_id: str = ""):
    """初始化日志系统

    参数:
        env: 环境标识（dev / demo / prod）
        trace_id: 当前请求的 TraceID
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    if HAS_LOGURU:
        _configure_loguru(env, trace_id)
        _bridge_stdlib_logging()
    else:
        _configure_std_logging(env)

    return get_logger(trace_id)


def _bridge_stdlib_logging():
    """桥接 stdlib logging → loguru

    让 requests / urllib / uvicorn 等第三方库通过 stdlib logging 输出的日志
    统一进入 loguru 的处理器（控制台 + 文件），避免日志分散、格式不一致。
    """
    import logging as _stdlib_logging

    from loguru import logger as _loguru_logger

    class _LoguruHandler(_stdlib_logging.Handler):
        """将 stdlib LogRecord 转发给 loguru"""

        _LEVEL_MAP = {
            "CRITICAL": "CRITICAL",
            "FATAL": "CRITICAL",
            "ERROR": "ERROR",
            "WARN": "WARNING",
            "WARNING": "WARNING",
            "INFO": "INFO",
            "DEBUG": "DEBUG",
            "NOTSET": "DEBUG",
        }

        def emit(self, record):
            try:
                level = self._LEVEL_MAP.get(record.levelname, "INFO")
                frame = record.__dict__.get("_loguru_frame")
                message = self.format(record)
                if frame is not None:
                    _loguru_logger.opt(depth=0, exception=record.exc_info).log(level, message)
                else:
                    _loguru_logger.opt(exception=record.exc_info).log(level, message)
            except Exception:
                self.handleError(record)

    handler = _LoguruHandler()
    _stdlib_logging.root.addHandler(handler)
    # 屏蔽根日志器默认的 stderr 输出，统一交由 loguru 控制台输出
    _stdlib_logging.root.handlers = [h for h in _stdlib_logging.root.handlers if h is handler]


def _configure_loguru(env: str, trace_id: str):
    """配置 loguru"""
    # 移除默认处理器
    _logger.remove()

    # 日志格式：结构化 JSON
    log_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<7} | {extra[trace_id]:<16} | "
        "{module}:{function}:{line} | {message}"
    )

    # 控制台输出（开发环境带颜色）
    if env == "prod":
        _logger.add(sys.stderr, format=log_format, level="WARNING")
    else:
        _logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | "
                   "<cyan>{extra[trace_id]:<16}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True,
        )

    # INFO 日志文件（按天分割，保留 30 天）
    _logger.add(
        os.path.join(LOG_DIR, "ai_core_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="INFO",
        rotation="00:00",  # 每天零点分割
        retention="30 days",
        compression="gz",
        encoding="utf-8",
    )

    # ERROR 日志文件（单独存储，方便排错）
    _logger.add(
        os.path.join(LOG_DIR, "ai_core_error_{time:YYYY-MM-DD}.log"),
        format=log_format,
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
    )

    # 设置默认 trace_id
    _logger.configure(extra={"trace_id": trace_id or "-"})


def _configure_std_logging(env: str):
    """loguru 不可用时的降级方案"""
    level = logging.DEBUG if env != "prod" else logging.WARNING
    _logger.setLevel(level)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)

    # 文件日志
    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, "ai_core.log"), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)


def get_logger(trace_id: str = "") -> "LoggerProxy":
    """获取带 TraceID 的 Logger 代理"""
    return LoggerProxy(trace_id or "-")


class LoggerProxy:
    """Logger 代理——自动携带 trace_id"""

    def __init__(self, trace_id: str):
        self._trace_id = trace_id

    def _bind(self):
        if HAS_LOGURU:
            return _logger.bind(trace_id=self._trace_id)
        return _logger

    def debug(self, msg, *args, **kwargs):
        self._bind().debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._bind().info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._bind().warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._bind().error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """记录异常堆栈"""
        if HAS_LOGURU:
            self._bind().exception(msg, *args, **kwargs)
        else:
            self._bind().error(msg, *args, **kwargs, exc_info=True)


# 全局默认 Logger
logger = get_logger("-")
