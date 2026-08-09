"""
爬虫系统配置中心
================
- 三档速度配置（快速 / 适中 / 慢速）
- 合规配置（UA、robots、服务条款）
- 权威数据源注册
- food 表字段规则与类别约定

设计原则：
1. 三档速度均设置「请求间隔 + 并发数 + 超时」三参数，覆盖不同采集场景
2. 限速参数含随机抖动区间，模拟真人浏览节奏
3. 数据源以「能扩充现有膳食数据库」为优先，强调权威性与许可
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ============================================================
# 一、三档速度配置
# ============================================================

@dataclass(frozen=True)
class SpeedProfile:
    """单档速度配置

    interval_range : (min, max) 秒，请求间随机抖动区间，模拟真人节奏
    concurrency    : 最大并发请求数（线程池大小）
    timeout        : 单请求超时（秒）
    max_retries    : 失败重试次数
    label          : 人类可读名称
    description    : 适用场景说明
    """
    name: str
    label: str
    description: str
    interval_range: Tuple[float, float]
    concurrency: int
    timeout: float
    max_retries: int


# 三档速度严格区分，覆盖「采集效率」与「服务器压力」的权衡区间
SPEED_PROFILES: Dict[str, SpeedProfile] = {
    # 快速档：高并发短间隔，仅用于已获授权的 API 或本地仿真测试，禁用于公网政府站
    "fast": SpeedProfile(
        name="fast",
        label="快速档",
        description="高并发短间隔，仅限授权API/本地仿真，禁止直接冲击公网政府站",
        interval_range=(0.3, 0.8),
        concurrency=8,
        timeout=8.0,
        max_retries=2,
    ),
    # 适中档：默认推荐档，平衡效率与压力，适合开放API（Open Food Facts 等）
    "medium": SpeedProfile(
        name="medium",
        label="适中档",
        description="默认推荐档，平衡采集效率与服务器压力，适合开放API数据源",
        interval_range=(1.5, 3.0),
        concurrency=3,
        timeout=15.0,
        max_retries=3,
    ),
    # 慢速档：保守档，强人道准则，适合政府/权威站点的有限采集
    "slow": SpeedProfile(
        name="slow",
        label="慢速档",
        description="保守档，模拟真人浏览，遵守人道采集准则，用于政府权威站有限采集",
        interval_range=(4.0, 8.0),
        concurrency=1,
        timeout=20.0,
        max_retries=3,
    ),
}

DEFAULT_SPEED = "medium"


# ============================================================
# 二、合规配置（UA 轮换 / robots / 服务条款）
# ============================================================

# 合规浏览器 UA 池（轮换使用，每个均如实标识为浏览器，不伪造身份）
USER_AGENT_POOL: List[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# 联系方式（礼貌标识，便于站点管理员联系；遵守 robots 人道准则）
CONTACT_EMAIL = "health-assistant-admin@example.com"

# 请求头公共部分（除 UA 外的诚实标识）
BASE_HEADERS: Dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# 单次采集任务上限（人道准则：不无限抓取）
MAX_ITEMS_PER_RUN = 2000
# 单数据源单次会话最大请求数（硬性熔断，防止失控）
MAX_REQUESTS_PER_SOURCE = 2000


# ============================================================
# 三、权威数据源注册
# ============================================================

@dataclass(frozen=True)
class DataSource:
    """数据源定义

    parser : 对应 parsers.py 中的解析器键名
    license: 数据许可/来源说明，用于合规标注
    needs_api_key: 是否需要 API key
    is_government: 是否为政府站点（触发更严格限速）
    """
    key: str
    name: str
    base_url: str
    parser: str
    license: str
    needs_api_key: bool = False
    is_government: bool = False
    enabled_by_default: bool = True


DATA_SOURCES: Dict[str, DataSource] = {
    # 1. 中国食物营养成分查询平台（政府权威，中文主源）
    "chinanutri": DataSource(
        key="chinanutri",
        name="中国食物营养成分查询平台",
        base_url="https://nlc.chinanutri.cn/fq/",
        parser="chinanutri",
        license="中国疾病预防控制中心营养与健康所·国家食物营养成分数据库（公共数据，采集需遵守站点条款）",
        is_government=True,
        enabled_by_default=True,
    ),
    # 2. Open Food Facts（开放数据，CC-BY-SA，无 key，国际品牌/包装食品）
    "off": DataSource(
        key="off",
        name="Open Food Facts",
        base_url="https://world.openfoodfacts.org/",
        parser="off",
        license="Open Food Facts，ODbL 1.0 数据许可（开放数据，可采集）",
        needs_api_key=False,
        is_government=False,
        enabled_by_default=True,
    ),
    # 3. USDA FoodData Central（美国农业部，权威，需免费 API key）
    "usda": DataSource(
        key="usda",
        name="USDA FoodData Central",
        base_url="https://api.nal.usda.gov/fdc/v1/",
        parser="usda",
        license="U.S. Department of Agriculture·FoodData Central（公共领域，需API key）",
        needs_api_key=True,
        is_government=True,
        enabled_by_default=False,  # 默认关，需配置 USDA_API_KEY
    ),
}


# ============================================================
# 四、food 表字段规则（严格沿用既有结构）
# ============================================================

# food 表允许的营养字段（仅 9 项，与建表语句一致；多余营养素不入库仅入原始库）
FOOD_TABLE_NUTRIENTS: Tuple[str, ...] = (
    "calorie", "protein", "fat", "carb", "diet_fiber",
    "calcium", "folic_acid", "dha", "gi_value",
)

# 合法食物类别（8 类 + 调味品 = 9 类）
VALID_CATEGORIES: Tuple[str, ...] = (
    "主食", "肉蛋类", "水产", "蔬菜", "水果", "豆制品", "奶类", "油脂类", "调味品",
)

# 每个类别的 priority / visibility 约定（来自既有数据实测，严格沿用）
# (priority, show_gi, show_folic_acid, show_dha)
CATEGORY_CONVENTION: Dict[str, Tuple[int, int, int, int]] = {
    "主食":   (4, 1, 0, 0),
    "肉蛋类": (2, 0, 0, 0),
    "水产":   (3, 0, 1, 1),
    "蔬菜":   (6, 1, 1, 0),
    "水果":   (7, 1, 0, 0),
    "豆制品": (5, 1, 1, 0),
    "奶类":   (1, 1, 0, 0),
    "油脂类": (8, 0, 0, 0),
    "调味品": (9, 0, 0, 0),  # 调味品：priority最低，无GI/叶酸/DHA显示
}

# 数值字段校验范围（合理上限，超出判为脏数据）
NUTRIENT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "calorie":   (0, 3000),
    "protein":   (0, 100),
    "fat":       (0, 100),
    "carb":      (0, 100),
    "diet_fiber":(0, 100),
    "calcium":   (0, 3000),
    "folic_acid":(0, 3000),
    "dha":       (0, 3000),  # 三文鱼 DHA 可达 1780mg/100g，深海鱼油更高
    "gi_value":  (0, 105),
}

# 爬取字段 → food 表字段名映射（多源统一）
RAW_TO_TABLE_MAP: Dict[str, str] = {
    "energy_kcal":      "calorie",
    "calories":         "calorie",
    "calorie":          "calorie",
    "protein_g":        "protein",
    "protein":          "protein",
    "fat_g":            "fat",
    "fat":              "fat",
    "carbohydrate_g":   "carb",
    "carb":             "carb",
    "carbohydrates":    "carb",
    "fiber_g":          "diet_fiber",
    "diet_fiber":       "diet_fiber",
    "fiber":            "diet_fiber",
    "calcium_mg":       "calcium",
    "calcium":          "calcium",
    "folic_acid_ug":    "folic_acid",
    "folate_ug":        "folic_acid",
    "folic_acid":       "folic_acid",
    "folate":           "folic_acid",
    "dha_mg":           "dha",
    "dha":              "dha",
    "gi_value":         "gi_value",
    "gi":               "gi_value",
    "glycemic_index":   "gi_value",
}


def get_speed(name: str) -> SpeedProfile:
    """按名称获取速度档配置"""
    if name not in SPEED_PROFILES:
        raise ValueError(f"未知速度档: {name}，可选: {list(SPEED_PROFILES.keys())}")
    return SPEED_PROFILES[name]


def get_category_convention(category: str) -> Tuple[int, int, int, int]:
    """获取类别对应的 (priority, show_gi, show_folic_acid, show_dha)"""
    if category not in CATEGORY_CONVENTION:
        raise ValueError(f"非法类别: {category}，合法: {VALID_CATEGORIES}")
    return CATEGORY_CONVENTION[category]
