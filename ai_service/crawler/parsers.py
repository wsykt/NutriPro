"""
多源数据解析器
==============
每个数据源一个解析器，统一输出 RawFoodItem 结构。
解析器只负责「把网页/JSON 转成结构化字段」，不触碰数据库。

统一输出字段（RawFoodItem）:
    name            : 食材名称（生/熟标注在名称中）
    category        : 膳食分类（8 类之一，未知则 None 待清洗时判定）
    nutrients       : 全量营养素字典（多源原始字段名）
    cooking_methods : 烹饪方式列表（food 表不存，入原始库）
    origin          : 食材产地（food 表不存，入原始库）
    source_url      : 来源 URL
    source_key      : 数据源标识
    raw_payload     : 原始响应（用于原始库留存）
    fetched_at      : 抓取时间戳
"""

from __future__ import annotations
import json
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ============================================================
# 统一输出结构
# ============================================================

@dataclass
class RawFoodItem:
    name: str
    category: Optional[str] = None
    nutrients: Dict[str, float] = field(default_factory=dict)  # 全量原始营养素
    cooking_methods: List[str] = field(default_factory=list)
    origin: str = ""
    source_url: str = ""
    source_key: str = ""
    raw_payload: str = ""   # 原始响应文本（HTML/JSON）
    fetched_at: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name, "category": self.category,
            "nutrients": self.nutrients,
            "cooking_methods": self.cooking_methods, "origin": self.origin,
            "source_url": self.source_url, "source_key": self.source_key,
            "raw_payload": self.raw_payload, "fetched_at": self.fetched_at,
        }


# ============================================================
# 解析器基类
# ============================================================

class BaseParser:
    """解析器基类：提供列表页 URL 生成 + 详情页解析接口"""

    def list_urls(self, max_items: int) -> List[str]:
        """返回待抓取的详情页 URL 列表"""
        raise NotImplementedError

    def parse_detail(self, url: str, html_or_json: str) -> Optional[RawFoodItem]:
        """解析详情页，返回 RawFoodItem 或 None"""
        raise NotImplementedError


# ============================================================
# 1. 中国食物营养成分查询平台解析器
# ============================================================

# 营养素名称标准化映射（中文 → 统一字段）
NUTRIENT_NAME_MAP = {
    "能量": "energy_kcal", "热量": "energy_kcal",
    "蛋白质": "protein_g",
    "脂肪": "fat_g",
    "碳水化合物": "carbohydrate_g", "碳水": "carbohydrate_g",
    "膳食纤维": "fiber_g",
    "钠": "sodium_mg",
    "维生素A": "vitamin_a_ug", "视黄醇当量": "vitamin_a_ug",
    "维生素C": "vitamin_c_mg",
    "维生素D": "vitamin_d_ug",
    "维生素E": "vitamin_e_mg",
    "钙": "calcium_mg",
    "铁": "iron_mg",
    "锌": "zinc_mg",
    "钾": "potassium_mg",
    "磷": "phosphorus_mg",
    "镁": "magnesium_mg",
    "硒": "selenium_ug",
    "铜": "copper_mg",
    "锰": "manganese_mg",
    "烟酸": "niacin_mg",
    "硫胺素": "thiamine_mg",
    "核黄素": "riboflavin_mg",
    "叶酸": "folic_acid_ug",
    "胆固醇": "cholesterol_mg",
    "饱和脂肪酸": "sfa_g",
    "单不饱和脂肪酸": "mufa_g",
    "多不饱和脂肪酸": "pufa_g",
    "DHA": "dha_mg",
    "EPA": "epa_mg",
    "GI": "gi_value", "血糖生成指数": "gi_value",
}

# 关键词 → 食物类别（用于自动分类）
CATEGORY_KEYWORDS = [
    (["大米", "面粉", "面条", "馒头", "米饭", "玉米", "燕麦", "小米", "糙米", "糯米", "面包", "饼", "粥", "粉条", "红薯", "土豆", "紫薯", "芋头", "山药"], "主食"),
    (["猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鹅肉", "鸡蛋", "鸭蛋", "鹌鹑蛋", "皮蛋", "咸蛋", "猪肝", "排骨", "火腿", "培根", "香肠"], "肉蛋类"),
    (["鱼", "虾", "蟹", "贝", "海带", "紫菜", "鱿鱼", "章鱼", "海参", "扇贝", "蛤蜊", "牡蛎", "带鱼", "鲫鱼", "鲤鱼", "草鱼"], "水产"),
    (["白菜", "菠菜", "芹菜", "西红柿", "黄瓜", "茄子", "萝卜", "胡萝卜", "青椒", "辣椒", "蘑菇", "木耳", "韭菜", "生菜", "油菜", "西兰花", "豆角", "南瓜"], "蔬菜"),
    (["苹果", "香蕉", "橙子", "葡萄", "梨", "桃", "西瓜", "芒果", "草莓", "蓝莓", "柚子", "柠檬", "荔枝", "龙眼", "菠萝", "猕猴桃", "樱桃"], "水果"),
    (["豆腐", "豆浆", "豆干", "腐竹", "豆皮", "黄豆", "绿豆", "红豆", "黑豆", "毛豆", "豆芽", "纳豆"], "豆制品"),
    (["牛奶", "酸奶", "奶酪", "奶油", "黄油", "奶粉", "脱脂奶", "低脂奶", "炼乳"], "奶类"),
    (["油", "脂", "猪油", "牛油", "花生油", "大豆油", "菜籽油", "玉米油", "橄榄油", "葵花籽油", "芝麻油", "香油"], "油脂类"),
]


def guess_category(name: str) -> Optional[str]:
    """根据名称关键词推断食物类别"""
    for keywords, cat in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in name:
                return cat
    return None


def _parse_numeric(value_str: str) -> Optional[float]:
    """从带单位的字符串中提取数值"""
    if not value_str:
        return None
    s = str(value_str).strip()
    if s in ("-", "—", "微量", "Tr", "tr", "ND", "未检出", "N/A", "NA", ""):
        return None
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _match_nutrient_strict(key: str, nutrient_map: dict) -> Optional[str]:
    """严格匹配营养素中文名 → 字段名

    避免子串误匹配：如 "脂肪" 不应匹配 "饱和脂肪酸(SFA)"
    规则：中文名后必须紧跟 ( 或 （ 或 空格 或字符串结束
    """
    for cn, field in nutrient_map.items():
        # 构建正则：中文名 + 边界（括号/空格/结束）
        pattern = re.escape(cn) + r"(?=[\s(（]|$)"
        if re.search(pattern, key):
            return field
    return None


# chinanutri 大类编码 → 我们 9 类的映射（含调味品）
# 站点分类：1=谷类, 10=薯类淀粉, 11=干豆类, 12=蔬菜, 13=菌藻, 14=水果,
#           15=坚果种子, 16=畜肉, 17=禽肉, 18=乳类, 19=蛋类, 20=鱼虾蟹贝,
#           21=婴幼儿食品(剔除), 22=小吃(剔除), 23=速食(剔除), 24=饮料(剔除),
#           25=含酒(剔除), 26=糖蜜饯(剔除), 27=油脂类, 28=调味品, 29=其它/花茶(剔除)
CHINANUTRI_CATEGORY_MAP = {
    1:  "主食",    # 谷类及制品
    10: "主食",    # 薯类、淀粉及制品
    11: "豆制品",  # 干豆类及制品
    12: "蔬菜",    # 蔬菜类及制品
    13: "蔬菜",    # 菌藻类（归入蔬菜）
    14: "水果",    # 水果类及制品
    15: "油脂类",  # 坚果、种子类（脂肪高，归油脂类）
    16: "肉蛋类",  # 畜肉类及制品
    17: "肉蛋类",  # 禽肉类及制品
    18: "奶类",    # 乳类及制品
    19: "肉蛋类",  # 蛋类及制品
    20: "水产",    # 鱼虾蟹贝类
    27: "油脂类",  # 油脂类
    28: "调味品",  # 调味品类（新增第9类）
}

# chinanutri 列表 API 返回数组字段索引（共 36 字段）
# 基于实测：[id, img, name, ?, ?, 食部%, 水分, 能量(kJ), 蛋白, 脂肪, 胆固醇, 灰分, 碳水, 膳食纤维, 胡萝卜素, 维A, α-TE, 硫胺素, 核黄素, 烟酸, 维C, 钙, 磷, 钾, 钠, 镁, 铁, 锌, 硒, 铜, 锰, 碘, SFA, MUFA, PUFA, 合计]
CHINANUTRI_LIST_FIELDS = {
    "id":              0,
    "name":            2,
    "edible":          5,   # 食部 %
    "water":           6,   # 水分 g
    "energy_kj":       7,   # 能量 kJ（需转 kcal）
    "protein_g":       8,
    "fat_g":           9,
    "cholesterol":     10,
    "ash":             11,
    "carbohydrate_g":  12,
    "fiber_g":         13,  # 总膳食纤维
    "calcium_mg":      21,
    "phosphorus":      22,
    "potassium":       23,
    "sodium":          24,
    "magnesium":       25,
    "iron":            26,
    "zinc":            27,
    "selenium":        28,
}

KJ_TO_KCAL = 4.184  # 1 kcal = 4.184 kJ


class ChinaNutriParser(BaseParser):
    """中国食物营养成分查询平台解析器

    站点结构（实测）:
    - 列表页: foodlist_{kw}_{cat1}_{cat2}_{field}_{sort}_{page}.htm （HTML，但食物列表 AJAX 加载）
    - AJAX 接口: POST FoodInfoQueryAction!queryFoodInfoList.do
      参数: categoryOne, categoryTwo, foodName, pageNum, field, flag
      返回: {list: [[id, img, name, ...], ...], totalPages, currentPage}
    - 详情页: /foodinfo/{id}.html （含叶酸/DHA/GI 等完整营养素表格）

    采集策略:
    1. 通过 AJAX API 获取分类下食物列表（含基础营养素，每页 8 条）
    2. 通过详情页补充叶酸/DHA/GI 等列表 API 不返回的字段
    3. 能量单位 kJ → kcal 转换（÷4.184）
    """

    BASE_URL = "https://nlc.chinanutri.cn/fq/"
    API_URL = "https://nlc.chinanutri.cn/fq/FoodInfoQueryAction!queryFoodInfoList.do"

    # 我们 9 类对应的 chinanutri 大类编码（14个大类）
    # 剔除：21婴幼儿/22小吃/23速食/24饮料/25含酒/26糖蜜饯/29其它花茶
    CATEGORIES_TO_CRAWL = [1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 27, 28]

    def __init__(self):
        self.base = self.BASE_URL

    def list_urls(self, max_items: int) -> List[str]:
        """生成 AJAX API 请求 URL 列表（按分类第1页）

        实际 POST 请求由 Fetcher 之后的 crawler 层发起（fetcher 仅做 GET），
        所以这里返回的是分类页 HTML URL，crawler 调用 parse_list 时从 HTML
        提取分类信息，再由 _crawl_chinanutri 直接调用 POST API。
        """
        max_items = min(max_items, 50)
        # 返回每个大类第 1 页（HTML，用于读取分类信息）
        urls = []
        for cat in self.CATEGORIES_TO_CRAWL:
            urls.append(urljoin(self.base, f"foodlist_0_{cat}_0_0_0_1.htm"))
        # 控制总 URL 数与 max_items 相当（每个分类页可拿到约 8 条详情）
        needed_pages = max(1, (max_items + 7) // 8)
        return urls[:needed_pages]

    def api_request_payload(self, category_one: int, page_num: int = 1,
                             food_name: str = "0") -> str:
        """构建 POST API 请求体"""
        return (f"categoryOne={category_one}&categoryTwo=0"
                f"&foodName={food_name}&pageNum={page_num}"
                f"&field=0&flag=0")

    def parse_list(self, html: str) -> List[dict]:
        """从列表页 HTML 提取分类信息（兼容旧接口，实际数据走 parse_api_response）"""
        soup = BeautifulSoup(html, "html.parser")
        items = []
        # 列表页的食物链接是 AJAX 渲染的，HTML 中不存在
        # 这里仅提取分类信息，实际数据通过 parse_api_response 解析
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if text and "foodinfo" in href:
                items.append({"name": text, "url": urljoin(self.base, href)})
        return items

    def parse_api_response(self, json_text: str, source_url: str = "") -> List[RawFoodItem]:
        """解析 AJAX API 返回的 JSON 列表

        返回多条 RawFoodItem（每页 8 条），仅含基础营养素。
        叶酸/DHA/GI 需后续访问详情页补充。
        """
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return []

        items = []
        for row in data.get("list", []):
            if not isinstance(row, list) or len(row) < 14:
                continue
            food_id = row[CHINANUTRI_LIST_FIELDS["id"]]
            name = row[CHINANUTRI_LIST_FIELDS["name"]]
            if not name:
                continue

            nutrients: Dict[str, float] = {}
            for field, idx in CHINANUTRI_LIST_FIELDS.items():
                if field in ("id", "name"):
                    continue
                val = _parse_numeric(row[idx]) if idx < len(row) else None
                if val is not None:
                    if field == "energy_kj":
                        # kJ → kcal 转换
                        nutrients["energy_kcal"] = round(val / KJ_TO_KCAL, 1)
                    elif field == "fiber_g":
                        nutrients["fiber_g"] = val
                    elif field == "calcium_mg":
                        nutrients["calcium_mg"] = val
                    elif field == "protein_g":
                        nutrients["protein_g"] = val
                    elif field == "fat_g":
                        nutrients["fat_g"] = val
                    elif field == "carbohydrate_g":
                        nutrients["carbohydrate_g"] = val

            # 详情页 URL（用于补充叶酸/DHA/GI）
            detail_url = urljoin(self.base, f"foodinfo/{food_id}.html")

            items.append(RawFoodItem(
                name=name,
                category=None,  # 由 crawler 根据分类上下文填入
                nutrients=nutrients,
                cooking_methods=[],
                origin="中国",
                source_url=detail_url,
                source_key="chinanutri",
                raw_payload=json_text,
                fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            ))
        return items

    def parse_detail(self, url: str, html: str) -> Optional[RawFoodItem]:
        """解析详情页 HTML，补充叶酸/DHA/GI 等列表 API 不返回的字段

        详情页结构:
        - h1 为空，食物名在 <title> 或面包屑最后
        - 1 个 table，6 列 [类型, 项目, 含量, 同类排名, 同类均值, 含量水平]
        - 第 2 列是营养素中文名（带英文括号），第 3 列是含量（带单位）
        - "—" 表示未检测，"Tr" 表示未检出
        """
        soup = BeautifulSoup(html, "html.parser")

        # 名称：优先 title，其次面包屑最后项
        name = ""
        title = soup.find("title")
        if title:
            title_text = title.get_text(strip=True)
            # title 格式：白萝卜[莱菔](鲜)-食物营养成分查询平台
            if "-" in title_text:
                name = title_text.split("-")[0].strip()
            else:
                name = title_text

        if not name:
            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                name = h1.get_text(strip=True)

        if not name:
            return None

        # 营养素表格解析（详情页含完整字段，包括叶酸/DHA）
        nutrients: Dict[str, float] = {}
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 3:
                    # 第 2 列是项目名（带英文括号），第 3 列是含量
                    key = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    val = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    # 严格匹配：避免 "脂肪" 误匹配 "饱和脂肪酸"
                    std = _match_nutrient_strict(key, NUTRIENT_NAME_MAP)
                    if std:
                        num = _parse_numeric(val)
                        if num is not None:
                            if std == "energy_kcal":
                                # 详情页能量可能也是 kJ（需检查单位）
                                if "kJ" in val or "kj" in val.lower():
                                    num = round(num / KJ_TO_KCAL, 1)
                            nutrients[std] = num

        if not nutrients:
            return None

        category = guess_category(name)

        return RawFoodItem(
            name=name,
            category=category,
            nutrients=nutrients,
            cooking_methods=[],
            origin="中国",
            source_url=url,
            source_key="chinanutri",
            raw_payload=html,
            fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )


# ============================================================
# 2. Open Food Facts 解析器（JSON API，开放数据）
# ============================================================

class OpenFoodFactsParser(BaseParser):
    """Open Food Facts JSON API 解析器（ODbL 开放许可）"""

    BASE_URL = "https://world.openfoodfacts.org/api/v2"
    # 中文常见食物关键词检索（API 支持 search）
    SEARCH_TERMS = ["rice", "chicken", "tofu", "milk", "apple", "spinach", "salmon"]

    def __init__(self):
        self.base = self.BASE_URL

    def search_url(self, term: str, page: int = 1, page_size: int = 20) -> str:
        return (f"{self.base}/search?search_terms={quote(term)}"
                f"&page={page}&page_size={page_size}&json=1&fields=product_name,"
                f"product_name_zh,nutriments,categories_tags,origins,countries")

    def list_urls(self, max_items: int) -> List[str]:
        return [self.search_url(term) for term in self.SEARCH_TERMS]

    def parse_detail(self, url: str, json_text: str) -> Optional[RawFoodItem]:
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return None

        products = data.get("products", [])
        items = []
        for prod in products:
            name = prod.get("product_name_zh") or prod.get("product_name") or ""
            if not name:
                continue
            nutriments = prod.get("nutriments", {}) or {}
            # 统一字段名
            nutrients = {}
            for k, v in nutriments.items():
                if isinstance(v, (int, float)) and v == v:  # 排除 NaN
                    if "energy-kcal_100g" in k:
                        nutrients["energy_kcal"] = float(v)
                    elif "proteins_100g" in k:
                        nutrients["protein_g"] = float(v)
                    elif "fat_100g" in k:
                        nutrients["fat_g"] = float(v)
                    elif "carbohydrates_100g" in k:
                        nutrients["carbohydrate_g"] = float(v)
                    elif "fiber_100g" in k:
                        nutrients["fiber_g"] = float(v)
                    elif "calcium_100g" in k:
                        nutrients["calcium_mg"] = float(v)

            origin = prod.get("origins") or ""
            cat_tags = prod.get("categories_tags", []) or []
            category = guess_category(name)

            items.append(RawFoodItem(
                name=name,
                category=category,
                nutrients=nutrients,
                cooking_methods=[],
                origin=origin,
                source_url=url,
                source_key="off",
                raw_payload=json.dumps(prod, ensure_ascii=False),
                fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            ))
        # 返回第一个有效项（fetcher 单 URL 单 item 约定）
        # 注意：OFF 单次搜索返回多产品，由 crawler 批量处理
        self._last_batch = items
        return items[0] if items else None

    def parse_batch(self, json_text: str, source_url: str = "") -> List[RawFoodItem]:
        """OFF 搜索接口一次返回多产品，提供批量解析"""
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return []
        products = data.get("products", [])
        items = []
        for prod in products:
            name = prod.get("product_name_zh") or prod.get("product_name") or ""
            if not name:
                continue
            nutriments = prod.get("nutriments", {}) or {}
            nutrients = {}
            for k, v in nutriments.items():
                if isinstance(v, (int, float)) and v == v:
                    if "energy-kcal_100g" in k: nutrients["energy_kcal"] = float(v)
                    elif "proteins_100g" in k: nutrients["protein_g"] = float(v)
                    elif "fat_100g" in k: nutrients["fat_g"] = float(v)
                    elif "carbohydrates_100g" in k: nutrients["carbohydrate_g"] = float(v)
                    elif "fiber_100g" in k: nutrients["fiber_g"] = float(v)
                    elif "calcium_100g" in k: nutrients["calcium_mg"] = float(v)
            items.append(RawFoodItem(
                name=name, category=guess_category(name),
                nutrients=nutrients, cooking_methods=[],
                origin=prod.get("origins") or "",
                source_url=source_url, source_key="off",
                raw_payload=json.dumps(prod, ensure_ascii=False),
                fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            ))
        return items


# ============================================================
# 3. USDA FoodData Central 解析器（JSON API，需 key）
# ============================================================

class USDAParser(BaseParser):
    """USDA FoodData Central API 解析器"""

    BASE_URL = "https://api.nal.usda.gov/fdc/v1/"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base = self.BASE_URL

    def search_url(self, query: str, page_size: int = 20) -> str:
        return (f"{self.base}foods/search?api_key={self.api_key}"
                f"&query={quote(query)}&pageSize={page_size}&dataType=SR%20Legacy")

    def list_urls(self, max_items: int) -> List[str]:
        terms = ["rice", "chicken breast", "salmon", "broccoli", "tofu", "milk", "apple"]
        return [self.search_url(t) for t in terms]

    def parse_detail(self, url: str, json_text: str) -> Optional[RawFoodItem]:
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError:
            return None
        foods = data.get("foods", [])
        items = []
        for f in foods:
            name = f.get("description") or f.get("lowercaseDescription") or ""
            if not name:
                continue
            nutrients = {}
            for fn in f.get("foodNutrients", []):
                nname = (fn.get("nutrientName") or "").lower()
                val = fn.get("value")
                if val is None:
                    continue
                if "energy" in nname and "kcal" in nname:
                    nutrients["energy_kcal"] = float(val)
                elif "protein" in nname:
                    nutrients["protein_g"] = float(val)
                elif "total lipid (fat)" in nname:
                    nutrients["fat_g"] = float(val)
                elif "carbohydrate" in nname:
                    nutrients["carbohydrate_g"] = float(val)
                elif "fiber" in nname:
                    nutrients["fiber_g"] = float(val)
                elif "calcium" in nname:
                    nutrients["calcium_mg"] = float(val)
                elif "folate" in nname:
                    nutrients["folic_acid_ug"] = float(val)
            items.append(RawFoodItem(
                name=name, category=guess_category(name),
                nutrients=nutrients, cooking_methods=[],
                origin="美国 USDA",
                source_url=url, source_key="usda",
                raw_payload=json.dumps(f, ensure_ascii=False),
                fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            ))
        return items[0] if items else None


# ============================================================
# 解析器注册表
# ============================================================

PARSERS = {
    "chinanutri": ChinaNutriParser,
    "off": OpenFoodFactsParser,
    "usda": USDAParser,
}


def get_parser(source_key: str, **kwargs) -> BaseParser:
    cls = PARSERS.get(source_key)
    if cls is None:
        raise ValueError(f"未知数据源: {source_key}")
    return cls(**kwargs)
