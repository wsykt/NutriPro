"""
合规与抓取层
============
- robots.txt 解析与缓存（遵守爬虫协议）
- UA 轮换（诚实浏览器标识）
- 限速器：令牌桶 + 随机抖动（模拟真人浏览，避免服务器过载）
- 三档限速：按域名匹配请求间隔（低/中/高）
- HTTP 抓取器：并发池、重试、超时、熔断

合规准则：
1. 如实标识 UA，不伪造身份（每条 UA 均为真实浏览器串）
2. 遵守 robots.txt，遇 Disallow 自动跳过
3. 政府站点强制使用慢速档，单次会话请求硬上限
4. 随机请求间隔，模拟真人节奏
5. 三档限速：稳定权威域名可高频（高），普通站点默认（中），敏感站点保守（低）
"""

from __future__ import annotations
import threading
import time
import random
import logging
from typing import Dict, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from crawler.config import (
    SpeedProfile, USER_AGENT_POOL, BASE_HEADERS, CONTACT_EMAIL,
    MAX_REQUESTS_PER_SOURCE,
)

logger = logging.getLogger(__name__)


# ============================================================
# 一、UA 轮换器
# ============================================================

class UARotator:
    """诚实 UA 轮换：从真实浏览器 UA 池中循环取用"""

    def __init__(self, pool: list = None):
        self._pool = pool or USER_AGENT_POOL
        self._idx = 0
        self._lock = threading.Lock()

    def next(self) -> str:
        with self._lock:
            ua = self._pool[self._idx % len(self._pool)]
            self._idx += 1
            return ua

    def headers(self, extra: dict = None) -> dict:
        """构建含诚实 UA 的请求头"""
        h = dict(BASE_HEADERS)
        h["User-Agent"] = self.next()
        h["From"] = CONTACT_EMAIL  # 礼貌标识，便于站点管理员联系
        if extra:
            h.update(extra)
        return h


# ============================================================
# 二、robots.txt 守卫
# ============================================================

class RobotsGuard:
    """robots.txt 解析与缓存，遵守爬虫协议"""

    def __init__(self):
        self._cache: Dict[str, RobotFileParser] = {}
        self._lock = threading.Lock()
        self._ua = UARotator().next()

    def _get_parser(self, base_url: str) -> Optional[RobotFileParser]:
        """获取并缓存某站点的 robots.txt 解析器"""
        parsed = urlparse(base_url)
        host_key = f"{parsed.scheme}://{parsed.netloc}"

        with self._lock:
            if host_key in self._cache:
                return self._cache[host_key]

        rp = RobotFileParser()
        robots_url = urljoin(host_key, "/robots.txt")
        try:
            resp = requests.get(
                robots_url,
                headers={"User-Agent": self._ua},
                timeout=8,
            )
            if resp.status_code == 200 and resp.text.strip():
                rp.parse(resp.text.splitlines())
                logger.info(f"robots.txt 已加载: {robots_url}")
            else:
                # 404/空 → 按 RFC 无限制，但记录为「未提供」，伦理上仍保守
                logger.info(f"robots.txt 未提供 ({resp.status_code}): {host_key}，按无限制处理（仍保守采集）")
                rp.parse([])  # 空 → 全部允许
        except Exception as e:
            logger.warning(f"robots.txt 获取失败: {robots_url} - {e}，保守视为禁止")
            # 获取失败时保守：构建一个禁止所有爬取的 parser
            rp.parse(["User-agent: *", "Disallow: /"])
            rp_disallow = rp
            with self._lock:
                self._cache[host_key] = rp_disallow
            return rp_disallow

        with self._lock:
            self._cache[host_key] = rp
        return rp

    def allowed(self, url: str, user_agent: str = "*") -> bool:
        """检查 URL 是否被 robots 允许"""
        parsed = urlparse(url)
        host_key = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._get_parser(host_key)
        if rp is None:
            return True
        try:
            return rp.can_fetch(user_agent, url)
        except Exception:
            return False  # 解析异常保守禁止

    def crawl_delay(self, base_url: str, user_agent: str = "*") -> Optional[float]:
        """读取 robots 中声明的 Crawl-delay"""
        rp = self._get_parser(base_url)
        if rp is None:
            return None
        try:
            return rp.crawl_delay(user_agent)
        except Exception:
            return None


# ============================================================
# 三、限速器（令牌桶 + 随机抖动）
# ============================================================

class RateLimiter:
    """令牌桶 + 随机抖动限速器，管控访问速度

    - interval_range: 随机请求间隔区间，模拟真人节奏
    - crawl_delay: robots 声明的 Crawl-delay（若存在则取 max(区间下界, crawl_delay)）
    - 线程安全，并发场景下统一管控
    """

    def __init__(self, profile: SpeedProfile, crawl_delay: Optional[float] = None):
        self.profile = profile
        self.crawl_delay = crawl_delay
        self._lock = threading.Lock()
        self._last_request_ts: float = 0.0
        self._request_count: int = 0
        # 政府站点强制至少 crawl_delay 或慢速下界
        self._min_interval = max(
            profile.interval_range[0],
            crawl_delay if crawl_delay else 0.0,
        )

    def acquire(self) -> float:
        """阻塞至下一次请求允许时刻，返回实际等待秒数"""
        with self._lock:
            now = time.time()
            # 随机抖动：在 [min_interval, max] 区间取值
            lo, hi = self.profile.interval_range
            target_interval = random.uniform(max(self._min_interval, lo), hi)
            elapsed = now - self._last_request_ts
            wait = max(0.0, target_interval - elapsed)
            self._last_request_ts = now + wait
            self._request_count += 1
        if wait > 0:
            time.sleep(wait)
        return wait

    @property
    def request_count(self) -> int:
        return self._request_count


# ============================================================
# 三档限速（按域名匹配的轻量限速层）
# ============================================================
# 独立于 SpeedProfile 的按域名限速能力：
#   - 低   ：外网敏感站点 / 白名单靠后的域名，请求最保守（间隔 ≥5s）
#   - 中   ：默认档，普通站点（间隔 ≥2s）
#   - 高   ：已知稳定的权威域名（如 pubmed.ncbi.nlm.nih.gov，间隔 ≥0.5s）

RATE_LIMIT_LEVELS: Dict[str, dict] = {
    "low": {
        "level": "low",
        "label": "低档",
        "interval": 5.0,
        "concurrency": 1,
        "description": "外网敏感站点/白名单靠后域名，请求保守，间隔≥5s",
    },
    "medium": {
        "level": "medium",
        "label": "中档",
        "interval": 2.0,
        "concurrency": 2,
        "description": "默认档，普通站点，间隔≥2s",
    },
    "high": {
        "level": "high",
        "label": "高档",
        "interval": 0.5,
        "concurrency": 4,
        "description": "已知稳定的权威域名，间隔≥0.5s",
    },
}

# 默认档位
DEFAULT_RATE_LEVEL = "medium"

# 域名 → 档位映射表（键为域名或其后缀，子域名自动匹配）
RATE_LIMIT_DOMAIN_MAP: Dict[str, str] = {
    # --- 高档：稳定权威域名 ---
    "pubmed.ncbi.nlm.nih.gov": "high",
    "eutils.ncbi.nlm.nih.gov": "high",
    "ncbi.nlm.nih.gov": "high",
    "ods.od.nih.gov": "high",
    "api.nal.usda.gov": "high",
    "world.openfoodfacts.org": "high",
    "openfoodfacts.org": "high",
    # --- 低档：外网敏感站点（政府/需格外克制） ---
    "chinanutri.cn": "low",
}

# 每域名上次请求时间戳（线程安全）
_last_request_ts: Dict[str, float] = {}
_last_request_lock = threading.Lock()


def _normalize_domain(domain: str) -> str:
    """从域名或完整 URL 中提取纯域名（小写、去 scheme/端口/路径）"""
    d = str(domain).strip().lower()
    if "://" in d:
        d = d.split("://", 1)[1]
    d = d.split("/", 1)[0]
    d = d.split(":", 1)[0]
    return d


def get_rate_limit(domain: str) -> dict:
    """按域名获取限速档位配置

    返回 dict: {level, label, interval, concurrency, description, matched_by}
    匹配规则：先精确匹配映射表 → 再按子域名后缀匹配（长后缀优先）→ 回退默认档。
    """
    d = _normalize_domain(domain)
    level = DEFAULT_RATE_LEVEL
    matched_by = None
    if d in RATE_LIMIT_DOMAIN_MAP:
        level = RATE_LIMIT_DOMAIN_MAP[d]
        matched_by = d
    else:
        # 后缀匹配：sub.pubmed.ncbi.nlm.nih.gov → pubmed.ncbi.nlm.nih.gov 档位
        for suffix, lv in sorted(
            RATE_LIMIT_DOMAIN_MAP.items(),
            key=lambda kv: len(kv[0]),
            reverse=True,
        ):
            if d.endswith("." + suffix):
                level = lv
                matched_by = suffix
                break
    cfg = dict(RATE_LIMIT_LEVELS[level])
    cfg["matched_by"] = matched_by
    return cfg


def wait_before_request(domain: str) -> float:
    """按域名档位等待，保证实际请求间隔 ≥ 档位间隔

    内部以「上次请求时间戳」计时，线程安全；返回实际等待秒数。
    用法：请求发出前调用 wait_before_request("pubmed.ncbi.nlm.nih.gov")
    """
    d = _normalize_domain(domain)
    interval = get_rate_limit(d)["interval"]
    with _last_request_lock:
        now = time.time()
        last = _last_request_ts.get(d, 0.0)
        wait = max(0.0, interval - (now - last))
        # 预占时间戳，避免同域名并发请求同时放行
        _last_request_ts[d] = now + wait if wait > 0 else now
    if wait > 0:
        time.sleep(wait)
    return wait


# ============================================================
# 四、HTTP 抓取器
# ============================================================

class FetchResult:
    """单次抓取结果"""
    __slots__ = ("url", "status", "ok", "text", "content", "elapsed_ms", "error", "attempts")

    def __init__(self, url, status=0, ok=False, text="", content=None,
                 elapsed_ms=0.0, error="", attempts=0):
        self.url = url
        self.status = status
        self.ok = ok
        self.text = text
        self.content = content
        self.elapsed_ms = elapsed_ms
        self.error = error
        self.attempts = attempts


class Fetcher:
    """HTTP 抓取器：集成限速、UA 轮换、重试、超时、熔断

    并发模型：ThreadPoolExecutor，并发数由速度档决定
    熔断：单数据源请求超 MAX_REQUESTS_PER_SOURCE 立即停止
    """

    def __init__(self, profile: SpeedProfile, source_key: str,
                 robots_guard: Optional[RobotsGuard] = None):
        self.profile = profile
        self.source_key = source_key
        self.ua = UARotator()
        self.robots = robots_guard or RobotsGuard()
        # 初始化限速器（含 robots Crawl-delay）
        self._crawl_delay_resolved = False
        self.rate_limiter = RateLimiter(profile)
        self._request_counter = 0
        self._counter_lock = threading.Lock()
        self._circuit_open = False

    def _resolve_crawl_delay(self, base_url: str):
        """首次请求时解析 robots Crawl-delay 并更新限速器"""
        if self._crawl_delay_resolved:
            return
        delay = self.robots.crawl_delay(base_url)
        if delay:
            logger.info(f"[{self.source_key}] robots Crawl-delay={delay}s，已纳入限速")
            self.rate_limiter = RateLimiter(self.profile, crawl_delay=delay)
        self._crawl_delay_resolved = True

    def fetch(self, url: str, expect_json: bool = False) -> FetchResult:
        """抓取单个 URL（含限速、重试、超时）"""
        # 1. robots 检查
        if not self.robots.allowed(url):
            return FetchResult(url, status=0, ok=False,
                               error=f"robots.txt 禁止抓取: {url}")

        # 2. 熔断检查
        with self._counter_lock:
            if self._request_counter >= MAX_REQUESTS_PER_SOURCE:
                self._circuit_open = True
                return FetchResult(url, ok=False, error="请求熔断：超出单源会话上限")
            self._request_counter += 1

        # 3. 限速等待
        self.rate_limiter.acquire()

        # 4. 带重试的请求
        last_err = ""
        for attempt in range(1, self.profile.max_retries + 1):
            t0 = time.time()
            try:
                resp = requests.get(
                    url,
                    headers=self.ua.headers({"Accept": "application/json" if expect_json else BASE_HEADERS["Accept"]}),
                    timeout=self.profile.timeout,
                    allow_redirects=True,
                )
                elapsed_ms = (time.time() - t0) * 1000
                if resp.status_code == 200:
                    # 编码处理（中文站点常用 GB2312）
                    if not expect_json:
                        resp.encoding = resp.apparent_encoding or "utf-8"
                    return FetchResult(
                        url=url, status=200, ok=True,
                        text=resp.text, content=resp.content,
                        elapsed_ms=elapsed_ms, attempts=attempt,
                    )
                # 4xx 不重试（除 429）
                if 400 <= resp.status_code < 500 and resp.status_code != 429:
                    return FetchResult(url, status=resp.status_code, ok=False,
                                       error=f"HTTP {resp.status_code}",
                                       elapsed_ms=elapsed_ms, attempts=attempt)
                last_err = f"HTTP {resp.status_code}"
            except requests.Timeout:
                last_err = "请求超时"
            except requests.ConnectionError as e:
                last_err = f"连接错误: {e}"
            except Exception as e:
                last_err = f"异常: {e}"

            if attempt < self.profile.max_retries:
                backoff = min(2 ** attempt, 8) + random.uniform(0, 1)
                logger.debug(f"重试 {attempt}/{self.profile.max_retries}: {url} - {last_err}，{backoff:.1f}s 后重试")
                time.sleep(backoff)

        return FetchResult(url, ok=False, error=last_err, attempts=self.profile.max_retries)

    def fetch_many(self, urls: list, expect_json: bool = False) -> list:
        """并发抓取多个 URL（并发数由速度档决定）"""
        results = [None] * len(urls)

        def _do(i, u):
            return i, self.fetch(u, expect_json=expect_json)

        with ThreadPoolExecutor(max_workers=self.profile.concurrency) as pool:
            futures = {pool.submit(_do, i, u): i for i, u in enumerate(urls)}
            for fut in as_completed(futures):
                i, res = fut.result()
                results[i] = res
        return results

    @property
    def is_circuit_open(self) -> bool:
        return self._circuit_open

    @property
    def total_requests(self) -> int:
        return self._request_counter
