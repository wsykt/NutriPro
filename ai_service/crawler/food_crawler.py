"""
网页爬虫主调度器 & CLI 入口
============================
编排 fetcher + parsers + raw_store + ingest_to_sqlite + verify，
提供完整的数据采集 → 清洗 → 入库 → 核验流程。

用法:
    # 三档速度系统化测试（本地仿真，零外部压力）
    python -m crawler.food_crawler benchmark

    # 采集（默认适中档，开放数据源 OFF）
    python -m crawler.food_crawler crawl --speed medium --source off --max 30

    # 慢速采集政府站（人道准则，严格限速）
    python -m crawler.food_crawler crawl --speed slow --source chinanutri --max 10

    # 仅采集入原始库（默认行为，不入 SQLite，先整理再导入）
    python -m crawler.food_crawler crawl --source chinanutri --max 1000

    # 强制按指定速度采集政府站（跳过人道降级）
    python -m crawler.food_crawler crawl --speed fast --source chinanutri --max 1000 --force-speed

    # 采集后直接入 SQLite
    python -m crawler.food_crawler crawl --source off --ingest

    # 核验 SQLite 与原始库一致性
    python -m crawler.food_crawler verify

合规说明:
    - 政府站点（chinanutri）强制 slow 档，单次上限 50 条
    - 遵守 robots.txt，UA 诚实标识
    - 随机请求间隔模拟真人浏览
    - 单源会话硬上限 500 请求，超限熔断
"""

from __future__ import annotations
import os
import sys
import json
import time
import logging
import argparse
from typing import List, Optional

# 确保 ai_service 在 sys.path
_AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, _AI_SERVICE_DIR)

from crawler.config import (
    SPEED_PROFILES, get_speed, DATA_SOURCES, DataSource,
    MAX_ITEMS_PER_RUN,
)
from crawler.compliance import Fetcher, RobotsGuard
from crawler.parsers import get_parser, RawFoodItem
from crawler.raw_store import get_raw_store
from crawler.ingest_to_sqlite import ingest_items, IngestResult
from crawler.verify import verify_all

logger = logging.getLogger(__name__)


# ============================================================
# 主调度器
# ============================================================

class CrawlOrchestrator:
    """爬虫主调度器：编排多源采集、原始存储、SQLite 接入"""

    def __init__(self, speed_name: str = "medium", source_keys: List[str] = None,
                 force_speed: bool = False):
        self.profile = get_speed(speed_name)
        self.source_keys = source_keys or [k for k, s in DATA_SOURCES.items() if s.enabled_by_default]
        self.robots = RobotsGuard()
        self.raw_store = get_raw_store()
        self.force_speed = force_speed  # True=跳过政府站强制降级

    def _resolve_speed_for_source(self, source: DataSource) -> "SpeedProfile":
        """政府站点强制降级为 slow 档（人道准则），除非 force_speed"""
        if source.is_government and self.profile.name != "slow" and not self.force_speed:
            logger.info(f"[{source.key}] 为政府站点，强制降级为 slow 档（人道准则）")
            return SPEED_PROFILES["slow"]
        return self.profile

    def crawl_source(self, source: DataSource, max_items: int,
                     write_raw: bool = True) -> List[dict]:
        """采集单个数据源，返回 RawFoodItem 字典列表"""
        print(f"\n[{source.key}] 开始采集: {source.name}")
        print(f"  许可: {source.license}")

        profile = self._resolve_speed_for_source(source)
        parser = get_parser(source.key)
        fetcher = Fetcher(profile, source_key=source.key, robots_guard=self.robots)

        # 1. 获取待抓取 URL 列表
        if source.key == "chinanutri":
            # 政府站：从列表页解析详情链接
            raw_items = self._crawl_chinanutri(parser, fetcher, source, max_items, write_raw)
        elif source.key == "off":
            raw_items = self._crawl_off(parser, fetcher, source, max_items, write_raw)
        elif source.key == "usda":
            api_key = os.getenv("USDA_API_KEY", "")
            if not api_key:
                logger.warning(f"[{source.key}] 未配置 USDA_API_KEY，跳过")
                return []
            parser = get_parser(source.key, api_key=api_key)
            raw_items = self._crawl_usda(parser, fetcher, source, max_items, write_raw)
        else:
            raw_items = []

        print(f"  采集完成: {len(raw_items)} 条")
        if fetcher.is_circuit_open:
            print(f"  ⚠️ 触发熔断（超出单源会话上限）")
        return raw_items

    def _crawl_chinanutri(self, parser, fetcher, source, max_items, write_raw):
        """采集中国食物营养成分查询平台

        流程:
        1. 对每个大类，POST AJAX API 获取列表（含基础营养素）
        2. 对列表中每个食物，GET 详情页补充叶酸/DHA/GI
        3. 合并基础营养素 + 详情页补充字段
        4. 爬取每个类别的全部页面（不限制页数，受 max_items 总量控制）
        """
        import requests as req
        from crawler.parsers import CHINANUTRI_CATEGORY_MAP, KJ_TO_KCAL

        all_items = []
        categories = parser.CATEGORIES_TO_CRAWL

        api_headers = {
            "User-Agent": fetcher.ua.next(),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": parser.BASE_URL,
            "Origin": "https://nlc.chinanutri.cn",
        }

        for cat_code in categories:
            if len(all_items) >= max_items:
                break
            our_category = CHINANUTRI_CATEGORY_MAP.get(cat_code)
            if not our_category:
                continue

            print(f"  采集分类: {our_category} (chinanutri code={cat_code})")

            # 翻页采集：读取第一页获取 totalPages，然后爬全部页
            page_num = 1
            total_pages = 1
            while page_num <= total_pages and len(all_items) < max_items:
                # 限速等待
                fetcher.rate_limiter.acquire()

                # POST AJAX API
                payload = parser.api_request_payload(cat_code, page_num=page_num)
                try:
                    api_resp = req.post(
                        parser.API_URL,
                        data=payload.encode("utf-8"),
                        headers=api_headers,
                        timeout=fetcher.profile.timeout,
                    )
                    if api_resp.status_code != 200:
                        logger.warning(f"  API 失败 cat={cat_code} page={page_num}: HTTP {api_resp.status_code}")
                        break
                    api_resp.encoding = "utf-8"
                except Exception as e:
                    logger.warning(f"  API 异常 cat={cat_code} page={page_num}: {e}")
                    break

                # 解析 API 响应
                list_items = parser.parse_api_response(api_resp.text, parser.API_URL)
                if not list_items:
                    break  # 无更多数据

                # 第一页时读取总页数
                if page_num == 1:
                    try:
                        import json as _json
                        meta = _json.loads(api_resp.text)
                        total_pages = meta.get("totalPages", 1)
                    except Exception:
                        total_pages = 1
                    print(f"    共 {total_pages} 页")

                print(f"    page {page_num}/{total_pages}: 获取 {len(list_items)} 条")

                # 对每个食物访问详情页补充营养素
                for list_item in list_items:
                    if len(all_items) >= max_items:
                        break

                    # 设置类别
                    list_item.category = our_category

                    # 限速后访问详情页
                    fetcher.rate_limiter.acquire()
                    detail_res = fetcher.fetch(list_item.source_url)
                    if detail_res.ok:
                        detail_item = parser.parse_detail(list_item.source_url, detail_res.text)
                        if detail_item:
                            # 合并：详情页营养素覆盖列表 API（详情页更完整）
                            merged_nutrients = dict(list_item.nutrients)
                            for k, v in detail_item.nutrients.items():
                                if v is not None:
                                    merged_nutrients[k] = v
                            list_item.nutrients = merged_nutrients
                            list_item.raw_payload = detail_res.text

                    if write_raw:
                        self.raw_store.save(source.key, list_item.source_url,
                                            list_item.raw_payload or api_resp.text,
                                            list_item.to_dict(), raw_format="html")
                    all_items.append(list_item.to_dict())

                page_num += 1

        return all_items[:max_items]

    def _crawl_off(self, parser, fetcher, source, max_items, write_raw):
        """采集 Open Food Facts（JSON API，开放数据）"""
        search_urls = parser.list_urls(max_items)
        all_items = []
        for url in search_urls:
            res = fetcher.fetch(url, expect_json=True)
            if not res.ok:
                logger.warning(f"OFF 搜索失败: {res.error}")
                continue
            # OFF 单次返回多产品，批量解析
            batch = parser.parse_batch(res.text, source_url=url)
            print(f"  搜索 {url.split('search_terms=')[1].split('&')[0]}: 获取 {len(batch)} 条")
            for item in batch:
                if write_raw:
                    self.raw_store.save(source.key, url, res.text,
                                        item.to_dict(), raw_format="json")
                all_items.append(item.to_dict())
            if len(all_items) >= max_items:
                break
        return all_items[:max_items]

    def _crawl_usda(self, parser, fetcher, source, max_items, write_raw):
        """采集 USDA FoodData Central"""
        search_urls = parser.list_urls(max_items)
        all_items = []
        for url in search_urls:
            res = fetcher.fetch(url, expect_json=True)
            if not res.ok:
                continue
            item = parser.parse_detail(url, res.text)
            if item:
                if write_raw:
                    self.raw_store.save(source.key, url, res.text,
                                        item.to_dict(), raw_format="json")
                all_items.append(item.to_dict())
        return all_items[:max_items]

    def run(self, max_items: int, ingest: bool = False,
            allow_update: bool = False) -> dict:
        """执行完整采集流程"""
        max_items = min(max_items, MAX_ITEMS_PER_RUN)
        print("=" * 70)
        print(f"网页爬虫启动 | 速度档: {self.profile.label} | 数据源: {self.source_keys}")
        print(f"单次上限: {max_items} | 入 SQLite: {ingest}")
        print("=" * 70)

        all_raw = []
        for key in self.source_keys:
            source = DATA_SOURCES[key]
            items = self.crawl_source(source, max_items, write_raw=True)
            all_raw.extend(items)

        print(f"\n采集汇总: 共 {len(all_raw)} 条原始数据")

        # SQLite 接入
        ingest_result = None
        if ingest and all_raw:
            print("\n" + "-" * 50)
            print("数据接入 SQLite food 表...")
            print("-" * 50)
            ingest_result = ingest_items(all_raw, allow_update=allow_update)
            print(ingest_result.summary())
            if ingest_result.failures:
                print(f"校验失败明细 (前 10 条):")
                for f in ingest_result.failures[:10]:
                    print(f"  - {f.food_name}: {f.reason}")
            if ingest_result.duplicate_names:
                print(f"重复条目 (前 10 条): {ingest_result.duplicate_names[:10]}")

        # 原始库统计
        raw_stats = self.raw_store.stats()
        print(f"\n原始库统计: {raw_stats}")

        return {
            "speed": self.profile.name,
            "sources": self.source_keys,
            "total_raw": len(all_raw),
            "ingest": ingest_result.summary() if ingest_result else "未接入",
            "raw_store_stats": raw_stats,
        }


# ============================================================
# CLI
# ============================================================

def cmd_benchmark(args):
    from crawler.benchmark import run_benchmark
    run_benchmark(num_urls=args.num_urls)


def cmd_crawl(args):
    orch = CrawlOrchestrator(speed_name=args.speed, source_keys=args.sources,
                             force_speed=args.force_speed)
    result = orch.run(max_items=args.max, ingest=args.ingest,
                      allow_update=args.update)
    print("\n" + "=" * 70)
    print("采集流程完成")
    print("=" * 70)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def cmd_verify(args):
    report = verify_all()
    print("\n" + "=" * 70)
    print("数据核验报告")
    print("=" * 70)
    summary = report.summary()
    print(f"总体: {summary['overall']}")
    print(f"SQLite 食物总数: {summary['total_foods_in_db']}")
    print(f"原始库记录数: {summary['total_raw_records']}")
    print(f"校验通过: {summary['checks_passed']} | 告警: {summary['warnings']} | 失败: {summary['failures']}")
    if report.issues:
        print("\n明细 (前 20 条):")
        for issue in report.issues[:20]:
            print(f"  [{issue.level}] {issue.category}: {issue.detail}")


def cmd_config(args):
    """打印当前配置"""
    print("=" * 60)
    print("爬虫系统配置")
    print("=" * 60)
    print("\n【三档速度配置】")
    for name, p in SPEED_PROFILES.items():
        print(f"  {p.label} ({name}): 间隔={p.interval_range}s 并发={p.concurrency} "
              f"超时={p.timeout}s 重试={p.max_retries}")
        print(f"    {p.description}")
    print("\n【数据源】")
    for key, s in DATA_SOURCES.items():
        status = "启用" if s.enabled_by_default else "停用(需配置)"
        gov = " [政府站·强制slow]" if s.is_government else ""
        print(f"  {s.name} ({key}){gov} - {status}")
        print(f"    许可: {s.license}")
    print("\n【food 表字段规则】")
    from crawler.config import VALID_CATEGORIES, CATEGORY_CONVENTION, FOOD_TABLE_NUTRIENTS
    print(f"  营养字段(9项): {FOOD_TABLE_NUTRIENTS}")
    print(f"  合法类别(8类): {VALID_CATEGORIES}")
    print(f"  类别约定 (priority, show_gi, show_folic_acid, show_dha):")
    for cat, conv in CATEGORY_CONVENTION.items():
        print(f"    {cat}: {conv}")


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    parser = argparse.ArgumentParser(
        description="食材数据网页爬虫系统（三档速度·合规·人道采集）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_bench = sub.add_parser("benchmark", help="三档速度系统化测试（本地仿真）")
    p_bench.add_argument("--num-urls", type=int, default=24, help="每档测试 URL 数")
    p_bench.set_defaults(func=cmd_benchmark)

    p_crawl = sub.add_parser("crawl", help="采集食材数据")
    p_crawl.add_argument("--speed", choices=list(SPEED_PROFILES.keys()),
                         default="medium", help="速度档")
    p_crawl.add_argument("--sources", nargs="+",
                         default=["off"],
                         help="数据源 (chinanutri/off/usda)")
    p_crawl.add_argument("--max", type=int, default=30, help="单次最大采集数")
    p_crawl.add_argument("--ingest", action="store_true",
                         help="采集后直接入 SQLite（默认不入，先整理再导入）")
    p_crawl.add_argument("--force-speed", action="store_true",
                         help="跳过政府站强制降级（按指定速度档采集）")
    p_crawl.add_argument("--update", action="store_true", help="允许更新已存在条目")
    p_crawl.set_defaults(func=cmd_crawl)

    p_verify = sub.add_parser("verify", help="核验 SQLite 与原始库一致性")
    p_verify.set_defaults(func=cmd_verify)

    p_config = sub.add_parser("config", help="打印当前配置")
    p_config.set_defaults(func=cmd_config)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
