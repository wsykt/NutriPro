"""
食物数据整合脚本
================
从原始库读取爬取数据 → 黑名单剔除 → 激进合并取均值 → 输出干净数据

整合规则（用户确认）：
1. 黑名单剔除：
   - 中国人不常吃：火鸡、奶酪、奶油（黄油保留，归油脂类）
   - 婴幼儿食品、速食方便食品、含酒、饮料（已在采集时按大类剔除，此处按名称二次过滤）
2. 激进合并：
   - 去掉括号/方括号内的品种标注（如"小麦粉(标准粉)"→"小麦粉"）
   - 同基础名 + 同类别的所有条目 → 营养素取均值
   - 合并后名称：基础名 + "(均值)"
3. 输出：merged_foods.json，供后续导入 SQLite 和向量知识库

用法:
    python -m crawler.merge_foods                    # 仅整合，输出 JSON
    python -m crawler.merge_foods --ingest           # 整合后直接入 SQLite
    python -m crawler.merge_foods --report           # 打印详细合并报告
"""
from __future__ import annotations
import os
import sys
import re
import json
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

from crawler.raw_store import get_raw_store
from crawler.config import FOOD_TABLE_NUTRIENTS, RAW_TO_TABLE_MAP, VALID_CATEGORIES

logger = logging.getLogger(__name__)

OUTPUT_PATH = os.path.join(AI_SERVICE_DIR, "crawler", "merged_foods.json")


# ============================================================
# 一、黑名单关键词（名称包含即剔除）
# ============================================================

# 中国人不常吃 / 不需要的食品
BLACKLIST_KEYWORDS = [
    # 奶制品中剔除（黄油保留）
    "奶酪", "奶油", "芝士", "起司", "奶昔", "炼乳",
    # 禽类中剔除
    "火鸡", "火鸡面",
    # 婴幼儿
    "婴儿", "幼儿", "配方奶", "辅食", "米粉(婴幼儿)",
    # 速食方便
    "方便面", "速食", "快餐", "肯德基", "麦当劳", "汉堡", "热狗",
    "披萨", "比萨", "薯条", "炸鸡",
    # 含酒（料酒、黄酒、米酒等全部剔除）
    "酒", "醪糟", "酒酿",
    # 饮料
    "可乐", "雪碧", "芬达", "奶茶", "咖啡", "汽水", "果汁饮料",
    # 糖蜜饯零食
    "蜜饯", "果脯", "棉花糖", "巧克力", "饼干", "蛋糕", "甜甜圈",
]

# 需要保留的例外（即使含黑名单关键词也保留）
# 例如"酒酿"含"酒"但用户可能想要？不，用户明确说含酒就不要。无例外。


def is_blacklisted(name: str) -> bool:
    """名称是否命中黑名单"""
    for kw in BLACKLIST_KEYWORDS:
        if kw in name:
            return True
    return False


# ============================================================
# 二、基础名提取（激进合并核心）
# ============================================================

# 同义词映射：不同叫法 → 统一基础名
SYNONYM_MAP = {
    # 鸡蛋类
    "土鸡蛋": "鸡蛋", "草鸡蛋": "鸡蛋", "乌鸡蛋": "鸡蛋", "柴鸡蛋": "鸡蛋",
    "山鸡蛋": "鸡蛋", "笨鸡蛋": "鸡蛋",
    # 萝卜
    "白萝卜": "萝卜", "红萝卜": "萝卜", "胡萝卜": "胡萝卜",  # 胡萝卜独立保留
    "变萝卜": "萝卜", "水萝卜": "萝卜", "心里美": "萝卜",
    # 大米
    "稻米": "大米", "粳米": "大米", "籼米": "大米",
    # 猪肉部位合并到"猪肉"
    "猪肉(肥)": "猪肉", "猪肉(瘦)": "猪肉", "猪肉(肥瘦)": "猪肉",
    # 牛肉/羊肉同理
    "牛肉(肥)": "牛肉", "牛肉(瘦)": "牛肉", "牛肉(肥瘦)": "牛肉",
    "羊肉(肥)": "羊肉", "羊肉(瘦)": "羊肉", "羊肉(肥瘦)": "羊肉",
}

# 基础名提取规则
def extract_base_name(name: str) -> str:
    """提取基础名：去掉括号/方括号内的品种标注

    例:
        "小麦粉(标准粉)" → "小麦粉"
        "鸡蛋(均值)" → "鸡蛋"
        "白萝卜[莱菔](鲜)" → "白萝卜" → 同义词 → "萝卜"
        "猪肉(肥瘦)(均值)" → "猪肉"
    """
    if not name:
        return name

    # 先查同义词表（在去括号前后都查）
    if name in SYNONYM_MAP:
        return SYNONYM_MAP[name]

    # 去掉所有 (...) （...） [...] 【...】 及其内容
    base = re.sub(r'[\(（\[【][^\)）\]】]*[\)）\]】]', '', name).strip()

    # 再次查同义词表
    if base in SYNONYM_MAP:
        return SYNONYM_MAP[base]

    return base


# ============================================================
# 三、营养素标准化与均值计算
# ============================================================

def normalize_nutrients(raw_nutrients: Dict) -> Dict[str, Optional[float]]:
    """将原始营养素字段映射到 food 表 9 项字段"""
    table: Dict[str, Optional[float]] = {k: None for k in FOOD_TABLE_NUTRIENTS}
    for raw_key, val in raw_nutrients.items():
        table_key = RAW_TO_TABLE_MAP.get(raw_key)
        if table_key and table_key in table:
            num = _to_float(val)
            if num is not None and table[table_key] is None:
                table[table_key] = num
    return table


def _to_float(val) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if val != val:  # NaN
            return None
        return float(val)
    s = str(val).strip()
    if s in ("", "-", "—", "微量", "Tr", "tr", "ND", "未检出", "N/A"):
        return None
    m = re.search(r'[-+]?\d*\.?\d+', s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def average_nutrients(items: List[dict]) -> Dict[str, Optional[float]]:
    """对多条数据的营养素取均值（仅对非空值取平均）

    若某营养素在所有条目中都为空，则结果为 None
    若部分条目有值部分为空，则仅对有值的取平均
    """
    sums: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)

    for item in items:
        nutrients = item.get("nutrients", {}) or {}
        table = normalize_nutrients(nutrients)
        for k, v in table.items():
            if v is not None:
                sums[k] += v
                counts[k] += 1

    result: Dict[str, Optional[float]] = {}
    for k in FOOD_TABLE_NUTRIENTS:
        if counts[k] > 0:
            # 保留 1 位小数
            result[k] = round(sums[k] / counts[k], 1)
        else:
            result[k] = None
    return result


# ============================================================
# 四、主整合流程
# ============================================================

def merge_foods(raw_items: List[dict]) -> Tuple[List[dict], dict]:
    """整合食物数据：剔除 → 合并 → 输出

    返回 (合并后数据列表, 统计报告)
    """
    stats = {
        "total_raw": len(raw_items),
        "blacklisted": 0,
        "blacklist_examples": [],
        "groups": 0,           # 合并后的组数
        "merged_items": 0,     # 合并掉的条目数（被并入均值的）
        "singletons": 0,       # 未合并的单条目数
        "by_category": {},
    }

    # 1. 黑名单剔除
    kept_items = []
    for item in raw_items:
        name = item.get("name", "")
        if is_blacklisted(name):
            stats["blacklisted"] += 1
            if len(stats["blacklist_examples"]) < 20:
                stats["blacklist_examples"].append(name)
        else:
            kept_items.append(item)

    # 2. 按基础名 + 类别分组
    groups: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
    for item in kept_items:
        name = item.get("name", "")
        category = item.get("category") or "未分类"
        base_name = extract_base_name(name)
        groups[(base_name, category)].append(item)

    stats["groups"] = len(groups)

    # 3. 每组取均值
    merged_list = []
    for (base_name, category), items in groups.items():
        if len(items) == 1:
            # 单条目：直接用，名称去括号
            single = items[0]
            nutrients = normalize_nutrients(single.get("nutrients", {}))
            merged_name = base_name if base_name != single.get("name") else single["name"]
            stats["singletons"] += 1
        else:
            # 多条目：取均值
            nutrients = average_nutrients(items)
            merged_name = f"{base_name}(均值)"
            stats["merged_items"] += len(items) - 1  # 被合并掉的条目数

        # 统计类别分布
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        # 收集来源信息
        source_urls = [it.get("source_url", "") for it in items if it.get("source_url")]
        source_url = source_urls[0] if source_urls else ""

        merged_list.append({
            "name": merged_name,
            "base_name": base_name,
            "category": category,
            "nutrients": nutrients,
            "merged_from": [it.get("name", "") for it in items],
            "merged_count": len(items),
            "source_url": source_url,
            "source_key": items[0].get("source_key", "chinanutri") if items else "",
            "origin": "中国",
        })

    # 按类别+名称排序
    merged_list.sort(key=lambda x: (x["category"], x["base_name"]))

    return merged_list, stats


# ============================================================
# 五、CLI
# ============================================================

def main():
    import argparse
    logging.basicConfig(level=logging.WARNING,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    parser = argparse.ArgumentParser(description="食物数据整合：剔除+合并取均值")
    parser.add_argument("--ingest", action="store_true",
                        help="整合后直接入 SQLite food 表")
    parser.add_argument("--report", action="store_true",
                        help="打印详细合并报告")
    parser.add_argument("--output", default=OUTPUT_PATH,
                        help=f"输出 JSON 路径（默认: {OUTPUT_PATH}）")
    args = parser.parse_args()

    print("=" * 70)
    print("食物数据整合：黑名单剔除 + 激进合并取均值")
    print("=" * 70)

    # 1. 从原始库读取
    raw_store = get_raw_store()
    raw_records = raw_store.list_all()
    print(f"\n【1】读取原始库: {len(raw_records)} 条记录")

    # 提取 parsed_item 中的数据
    raw_items = []
    for rec in raw_records:
        parsed = rec.get("parsed_item", {}) or {}
        if parsed.get("name"):
            raw_items.append(parsed)

    print(f"    有效条目: {len(raw_items)} 条")

    if not raw_items:
        print("⚠️ 原始库无数据，请先运行爬虫采集")
        return

    # 2. 整合
    print(f"\n【2】整合中...")
    merged_list, stats = merge_foods(raw_items)

    print(f"\n【3】整合结果:")
    print(f"  原始条目: {stats['total_raw']}")
    print(f"  黑名单剔除: {stats['blacklisted']}")
    if args.report and stats["blacklist_examples"]:
        print(f"    剔除示例: {stats['blacklist_examples'][:10]}")
    print(f"  合并后组数: {stats['groups']}")
    print(f"  未合并单条目: {stats['singletons']}")
    print(f"  被合并条目: {stats['merged_items']}")
    print(f"  最终条目数: {len(merged_list)}")
    print(f"\n  按类别分布:")
    for cat, cnt in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        print(f"    {cat}: {cnt}")

    # 4. 详细合并报告
    if args.report:
        print(f"\n【4】合并详情（被合并的组，即 merged_count > 1）:")
        merged_groups = [m for m in merged_list if m["merged_count"] > 1]
        merged_groups.sort(key=lambda x: -x["merged_count"])
        for m in merged_groups[:30]:
            print(f"  {m['name']} ({m['category']}) ← 合并 {m['merged_count']} 条:")
            for origin in m["merged_from"]:
                print(f"    - {origin}")

    # 5. 保存 JSON
    print(f"\n【5】保存到: {args.output}")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(merged_list, f, ensure_ascii=False, indent=2)
    print(f"    已保存 {len(merged_list)} 条")

    # 6. 可选：接入 SQLite
    if args.ingest:
        print(f"\n【6】接入 SQLite food 表...")
        from crawler.ingest_to_sqlite import ingest_items
        # 转换为 ingest_items 需要的格式
        ingest_data = []
        for m in merged_list:
            # 把 table 字段名转回 raw 字段名（ingest_items 内部会再转一次）
            raw_nutrients = {}
            reverse_map = {v: k for k, v in RAW_TO_TABLE_MAP.items()}
            for k, v in m["nutrients"].items():
                if v is not None and k in reverse_map:
                    raw_nutrients[reverse_map[k]] = v
            ingest_data.append({
                "name": m["name"],
                "category": m["category"],
                "nutrients": raw_nutrients,
                "source_url": m["source_url"],
                "source_key": m["source_key"],
                "origin": m["origin"],
                "raw_payload": "",
                "fetched_at": "",
            })
        result = ingest_items(ingest_data, allow_update=False)
        print(f"  {result.summary()}")
        if result.failures:
            print(f"  失败明细 (前 10 条):")
            for fail in result.failures[:10]:
                print(f"    - {fail.food_name}: {fail.reason}")
        if result.duplicate_names:
            print(f"  重复条目 (前 10 条): {result.duplicate_names[:10]}")

    print("\n" + "=" * 70)
    print("整合流程完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
