"""
NLU 自然语言饮食解析引擎

核心功能：
1. 将自然语言饮食描述 → 结构化 JSON（食物名称+重量+营养数据）
2. 通过 LLM 提取食物项，再交叉校验食物数据库获取精确营养值
3. 支持多餐（早餐/午餐/晚餐/加餐）一次性解析
4. 支持自然语言单位（碗/个/杯/根/勺→克）自动换算

使用场景：
- 语音录入：STT 文本 → 此引擎 → 结构化营养数据
- 拍照识别：OCR 文本 → 此引擎 → 结构化营养数据
- 对话解析：用户文字描述 → 此引擎 → 营养分析输入
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple

# 从共享常量模块导入单位换算表
from constants.food_units import UNIT_TO_GRAMS, ITEM_GRAM_PER_UNIT

# 统一 SQLite 连接（WAL + busy_timeout）
from utils.sqlite_utils import get_conn

# ==============================================================
# 数据库路径
# ==============================================================
_DB_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "food.db"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "backend-health", "data", "health.db"),
]

# 缓存
_food_cache: List[dict] = None
_food_index: Dict[str, List[dict]] = None


def _load_food_db():
    """加载食物数据库到缓存"""
    global _food_cache, _food_index
    if _food_cache is not None:
        return

    db_path = None
    for p in _DB_PATHS:
        if os.path.exists(p) and os.path.getsize(p) > 100:
            db_path = p
            break

    if not db_path:
        _food_cache = []
        _food_index = {}
        return

    conn = get_conn(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT food_name, food_category, calorie, protein, carb, fat,
               diet_fiber, gi_value, calcium, folic_acid, dha, priority
        FROM food WHERE status = 'approved'
    """)
    _food_cache = []
    _food_index = {}
    for row in cursor.fetchall():
        item = {
            "food_name": row[0],
            "category": row[1] or "",
            "calorie": float(row[2] or 0),
            "protein": float(row[3] or 0),
            "carb": float(row[4] or 0),
            "fat": float(row[5] or 0),
            "diet_fiber": float(row[6] or 0),
            "gi_value": float(row[7] or 0),
            "calcium": float(row[8] or 0),
            "folic_acid": float(row[9] or 0),
            "dha": float(row[10] or 0),
            "priority": int(row[11] or 0),
        }
        _food_cache.append(item)

        # 建立索引：食物的每个关键子串
        name = row[0]
        _food_index.setdefault(name, []).append(item)
        # 去掉括号内容建立索引
        clean_name = re.sub(r'[（(][^)）]*[)）]', '', name).strip()
        if clean_name != name:
            _food_index.setdefault(clean_name, []).append(item)
        # 简名索引（取前4-6字）
        short = clean_name[:6] if len(clean_name) >= 4 else ""
        if short:
            # 不覆盖精确匹配
            if short not in _food_index:
                _food_index.setdefault(short, []).append(item)

    conn.close()


def _fuzzy_match_food(query: str) -> Optional[dict]:
    """模糊匹配食物名称，返回最佳匹配项（按优先级降序）"""
    _load_food_db()
    if not _food_cache:
        return None

    query = query.strip()
    
    # 常见别名映射（用于查不到时的二次匹配）
    ALIAS_MAP = {
        "白米饭": "米饭",
        "大米饭": "米饭",
        "番茄": "西红柿",
        "马铃薯": "土豆",
        "红萝卜": "胡萝卜",
        "土豆丝": "土豆",
        "清蒸鲈鱼": "海鲈鱼(鲜)",
        "红烧肉": "猪肉(肥瘦)",
        "炒青菜": "油菜",
        "纯牛奶": "牛奶",
        "鲜牛奶": "牛奶",
        "可乐": "雪碧饮料",
        "小西红柿": "樱桃番茄",
        "大白菜": "白菜",
        "鲈鱼": "海鲈鱼(鲜)",
        "河鲈鱼": "海鲈鱼(鲜)",
        "鸡大胸": "鸡胸脯肉",
        "全麦面包": "面包(均值)",
        "水煮蛋": "鸡蛋(煮)",
        "薯条": "油炸土豆条",
    }
    
    candidates = []

    # 0. 别名映射
    if query in ALIAS_MAP:
        query = ALIAS_MAP[query]

    # 1. 精确匹配
    for item in _food_cache:
        if item["food_name"] == query:
            candidates.append(item)

    # 2. 去掉括号后的精确匹配
    if not candidates:
        clean_query = re.sub(r'[（(][^)）]*[)）]', '', query).strip()
        for item in _food_cache:
            clean_name = re.sub(r'[（(][^)）]*[)）]', '', item["food_name"]).strip()
            if clean_name == clean_query:
                candidates.append(item)

    # 2. 包含匹配（query 在食物名中）
    if not candidates:
        for item in _food_cache:
            if query in item["food_name"]:
                candidates.append(item)

    # 3. 食物名在 query 中
    if not candidates:
        for item in _food_cache:
            if item["food_name"] in query:
                candidates.append(item)

    # 4. 部分字匹配（拆字匹配）
    if not candidates and len(query) >= 2:
        query_chars = set(query)
        for item in _food_cache:
            item_chars = set(item["food_name"])
            match_ratio = len(query_chars & item_chars) / len(query_chars)
            if match_ratio >= 0.7:
                candidates.append(item)

    if not candidates:
        return None

    # 按优先级降序排序
    candidates.sort(key=lambda x: (x["priority"], x["calorie"]), reverse=True)
    return candidates[0]


def _convert_amount(raw_amount: str, food_name: str = "") -> Tuple[float, str]:
    """将自然语言数量转换为克数，返回 (克数, 描述)"""
    raw = raw_amount.strip()

    # 直接数字+g/克
    m = re.match(r'^(\d+[\.\d]*)\s*(g|克|ml|毫升)$', raw)
    if m:
        return float(m.group(1)), raw

    # 数字 + 单位
    m = re.match(r'^(\d+[\.\d]*)\s*(.+)$', raw)
    if m:
        num = float(m.group(1))
        unit = m.group(2).strip()
        # 食物特定单位覆盖
        if unit == "个" and food_name:
            for key, gram in ITEM_GRAM_PER_UNIT.items():
                if key in food_name:
                    return num * gram, f"{num}{unit}(约{num*gram}g)"
        # 通用单位
        if unit in UNIT_TO_GRAMS:
            return num * UNIT_TO_GRAMS[unit], f"{num}{unit}(约{num * UNIT_TO_GRAMS[unit]}g)"
        # 直接数字（没有单位）= 就是克
        return num, f"{num}g"

    # 纯数字 = 克
    m = re.match(r'^(\d+[\.\d]*)$', raw)
    if m:
        return float(m.group(1)), f"{raw}g"

    return 100, f"{raw}(按100g估算)"


# ==============================================================
# 菜品智能还原：将菜品拆解为实际食材
# ==============================================================

DISH_INGREDIENTS_MAP = {
    "宫保鸡丁": [
        {"ingredient": "鸡腿肉", "ratio": 0.45},
        {"ingredient": "花生米", "ratio": 0.15},
        {"ingredient": "黄瓜", "ratio": 0.20},
        {"ingredient": "干辣椒", "ratio": 0.05},
        {"ingredient": "食用油", "ratio": 0.05},
        {"ingredient": "白砂糖", "ratio": 0.05},
        {"ingredient": "酱油", "ratio": 0.05},
    ],
    "鱼香肉丝": [
        {"ingredient": "猪里脊", "ratio": 0.50},
        {"ingredient": "胡萝卜", "ratio": 0.15},
        {"ingredient": "木耳", "ratio": 0.10},
        {"ingredient": "冬笋", "ratio": 0.10},
        {"ingredient": "豆瓣酱", "ratio": 0.05},
        {"ingredient": "食用油", "ratio": 0.05},
        {"ingredient": "白砂糖", "ratio": 0.05},
    ],
    "红烧肉": [
        {"ingredient": "五花肉", "ratio": 0.70},
        {"ingredient": "冰糖", "ratio": 0.08},
        {"ingredient": "酱油", "ratio": 0.05},
        {"ingredient": "料酒", "ratio": 0.05},
        {"ingredient": "八角", "ratio": 0.02},
        {"ingredient": "姜", "ratio": 0.05},
        {"ingredient": "葱", "ratio": 0.05},
    ],
    "麻婆豆腐": [
        {"ingredient": "豆腐", "ratio": 0.55},
        {"ingredient": "牛肉末", "ratio": 0.15},
        {"ingredient": "豆瓣酱", "ratio": 0.08},
        {"ingredient": "花椒", "ratio": 0.02},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "葱", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.02},
        {"ingredient": "水淀粉", "ratio": 0.05},
    ],
    "糖醋里脊": [
        {"ingredient": "猪里脊", "ratio": 0.55},
        {"ingredient": "番茄酱", "ratio": 0.15},
        {"ingredient": "白醋", "ratio": 0.08},
        {"ingredient": "白砂糖", "ratio": 0.10},
        {"ingredient": "鸡蛋", "ratio": 0.05},
        {"ingredient": "淀粉", "ratio": 0.05},
        {"ingredient": "食用油", "ratio": 0.02},
    ],
    "清蒸鲈鱼": [
        {"ingredient": "鲈鱼", "ratio": 0.85},
        {"ingredient": "姜", "ratio": 0.05},
        {"ingredient": "葱", "ratio": 0.05},
        {"ingredient": "蒸鱼豉油", "ratio": 0.03},
        {"ingredient": "食用油", "ratio": 0.02},
    ],
    "西红柿炒鸡蛋": [
        {"ingredient": "西红柿", "ratio": 0.45},
        {"ingredient": "鸡蛋", "ratio": 0.35},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "白砂糖", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.02},
        {"ingredient": "葱", "ratio": 0.05},
    ],
    "青椒土豆丝": [
        {"ingredient": "土豆", "ratio": 0.65},
        {"ingredient": "青椒", "ratio": 0.20},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "盐", "ratio": 0.03},
        {"ingredient": "醋", "ratio": 0.02},
        {"ingredient": "葱", "ratio": 0.02},
    ],
    "地三鲜": [
        {"ingredient": "茄子", "ratio": 0.40},
        {"ingredient": "土豆", "ratio": 0.30},
        {"ingredient": "青椒", "ratio": 0.15},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "酱油", "ratio": 0.03},
        {"ingredient": "盐", "ratio": 0.02},
        {"ingredient": "蒜", "ratio": 0.02},
    ],
    "水煮鱼": [
        {"ingredient": "草鱼", "ratio": 0.50},
        {"ingredient": "豆芽", "ratio": 0.20},
        {"ingredient": "干辣椒", "ratio": 0.08},
        {"ingredient": "花椒", "ratio": 0.03},
        {"ingredient": "豆瓣酱", "ratio": 0.08},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "姜", "ratio": 0.03},
    ],
    "回锅肉": [
        {"ingredient": "五花肉", "ratio": 0.55},
        {"ingredient": "青蒜", "ratio": 0.15},
        {"ingredient": "豆瓣酱", "ratio": 0.08},
        {"ingredient": "豆豉", "ratio": 0.05},
        {"ingredient": "甜面酱", "ratio": 0.05},
        {"ingredient": "食用油", "ratio": 0.05},
        {"ingredient": "白砂糖", "ratio": 0.04},
        {"ingredient": "姜", "ratio": 0.03},
    ],
    "蚂蚁上树": [
        {"ingredient": "粉丝", "ratio": 0.40},
        {"ingredient": "牛肉末", "ratio": 0.25},
        {"ingredient": "豆瓣酱", "ratio": 0.08},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "酱油", "ratio": 0.05},
        {"ingredient": "白砂糖", "ratio": 0.04},
        {"ingredient": "葱", "ratio": 0.05},
        {"ingredient": "姜", "ratio": 0.05},
    ],
    "青椒肉丝": [
        {"ingredient": "猪里脊", "ratio": 0.50},
        {"ingredient": "青椒", "ratio": 0.30},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "酱油", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.02},
        {"ingredient": "水淀粉", "ratio": 0.03},
        {"ingredient": "蒜", "ratio": 0.02},
    ],
    "蒜蓉西兰花": [
        {"ingredient": "西兰花", "ratio": 0.75},
        {"ingredient": "蒜", "ratio": 0.10},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "盐", "ratio": 0.03},
        {"ingredient": "蚝油", "ratio": 0.04},
    ],
    "醋溜白菜": [
        {"ingredient": "白菜", "ratio": 0.70},
        {"ingredient": "白醋", "ratio": 0.10},
        {"ingredient": "白砂糖", "ratio": 0.08},
        {"ingredient": "食用油", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.03},
        {"ingredient": "淀粉", "ratio": 0.04},
    ],
    "紫菜蛋花汤": [
        {"ingredient": "紫菜", "ratio": 0.15},
        {"ingredient": "鸡蛋", "ratio": 0.25},
        {"ingredient": "虾皮", "ratio": 0.05},
        {"ingredient": "香油", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.02},
        {"ingredient": "葱", "ratio": 0.03},
        {"ingredient": "水", "ratio": 0.45},
    ],
    "西红柿鸡蛋汤": [
        {"ingredient": "西红柿", "ratio": 0.30},
        {"ingredient": "鸡蛋", "ratio": 0.25},
        {"ingredient": "食用油", "ratio": 0.05},
        {"ingredient": "盐", "ratio": 0.03},
        {"ingredient": "葱", "ratio": 0.03},
        {"ingredient": "水", "ratio": 0.34},
    ],
    "酸辣土豆丝": [
        {"ingredient": "土豆", "ratio": 0.65},
        {"ingredient": "干辣椒", "ratio": 0.05},
        {"ingredient": "花椒", "ratio": 0.02},
        {"ingredient": "白醋", "ratio": 0.08},
        {"ingredient": "食用油", "ratio": 0.08},
        {"ingredient": "盐", "ratio": 0.03},
        {"ingredient": "葱", "ratio": 0.05},
        {"ingredient": "蒜", "ratio": 0.04},
    ],
    "鱼香茄子": [
        {"ingredient": "茄子", "ratio": 0.50},
        {"ingredient": "胡萝卜", "ratio": 0.10},
        {"ingredient": "木耳", "ratio": 0.08},
        {"ingredient": "豆瓣酱", "ratio": 0.08},
        {"ingredient": "食用油", "ratio": 0.10},
        {"ingredient": "白砂糖", "ratio": 0.05},
        {"ingredient": "白醋", "ratio": 0.05},
        {"ingredient": "蒜", "ratio": 0.04},
    ],
    "三杯鸡": [
        {"ingredient": "鸡腿", "ratio": 0.60},
        {"ingredient": "麻油", "ratio": 0.10},
        {"ingredient": "酱油", "ratio": 0.08},
        {"ingredient": "白酒", "ratio": 0.08},
        {"ingredient": "姜", "ratio": 0.05},
        {"ingredient": "九层塔", "ratio": 0.05},
        {"ingredient": "糖", "ratio": 0.04},
    ],
}


def _try_dish_reduction(dish_name: str, total_grams: float) -> Optional[List[dict]]:
    """
    尝试将菜品还原为食材组成
    
    输入: "宫保鸡丁", 150g
    输出: [
        {"ingredient": "鸡腿肉", "grams": 67.5},
        {"ingredient": "花生米", "grams": 22.5},
        ...
    ]
    """
    if dish_name not in DISH_INGREDIENTS_MAP:
        return None
    
    recipe = DISH_INGREDIENTS_MAP[dish_name]
    ingredients = []
    
    for item in recipe:
        ingredient_name = item["ingredient"]
        ratio = item["ratio"]
        grams = round(total_grams * ratio, 1)
        
        ingredients.append({
            "ingredient": ingredient_name,
            "grams": grams,
            "ratio": ratio,
        })
    
    return ingredients


# ==============================================================
# LLM 提取 Prompt
# ==============================================================

EXTRACT_PROMPT = """你是一个专业的饮食解析助手。请从用户描述中提取所有食物信息，以JSON格式返回。

规则：
1. 识别每种食物的**名称**和**数量**（包括自然语言单位如碗/个/杯/根）
2. 将食物按餐次分组：早餐、午餐、晚餐、加餐/零食
3. 如果未指定餐次，统一归为"未分类"
4. 如果未指定数量，标记为"适量"(100g)
5. 只解析食物相关描述，忽略闲聊内容

输出格式（严格JSON，不要其他文字）：
{
  "meals": [
    {
      "meal_type": "早餐|午餐|晚餐|加餐|未分类",
      "foods": [
        {"name": "食物名称", "amount": "数量描述", "confidence": 0.95}
      ]
    }
  ]
}

注意：
- amount 要保留原始单位的描述，如"2个"、"1碗"、"150g"
- confidence 0-1，对食物名称的确认程度
- 如果某个食物名称不确定，用较低的confidence
"""


def _llm_extract(text: str) -> dict:
    """使用 LLM 从文本中提取结构化食物信息"""
    from llm.router import llm

    messages = [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": f"解析以下饮食描述：\n{text}"},
    ]

    try:
        result = llm.chat_json(messages, max_retries=2)
        if result and "meals" in result:
            return result
    except Exception:
        pass

    # LLM 失败时使用规则兜底
    return _rule_based_extract(text)


def _rule_based_extract(text: str) -> dict:
    """纯规则兜底的食物提取"""
    meals = {"早餐": [], "午餐": [], "晚餐": [], "加餐": [], "未分类": []}
    current_meal = "未分类"

    lines = text.replace("，", "\n").replace("。", "\n").split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 识别餐次标记
        for meal_type in ["早餐", "午餐", "晚餐", "加餐", "零食", "夜宵"]:
            if meal_type in line:
                current_meal = "加餐" if meal_type in ("加餐", "零食", "夜宵") else meal_type
                break

        # 提取食物名+数量
        # 模式: XXXYYYg/克/个/碗...
        pattern = r'([\u4e00-\u9fff]+)\s*(\d+[\.\d]*)\s*(g|克|ml|毫升|个|碗|杯|根|条|块|片|袋|包)'
        matches = re.findall(pattern, line)
        for name, num, unit in matches:
            meals[current_meal].append({
                "name": name.strip(),
                "amount": f"{num}{unit}",
                "confidence": 0.7,
            })

    # 过滤空餐次
    result = {"meals": []}
    for meal_type, foods in meals.items():
        if foods:
            result["meals"].append({"meal_type": meal_type, "foods": foods})

    return result


# ==============================================================
# 主解析引擎
# ==============================================================

class NLUParser:
    """自然语言饮食解析引擎"""

    @staticmethod
    def parse(text: str) -> dict:
        """
        主入口：解析自然语言饮食描述，返回结构化营养数据

        输入: "早餐吃了2个鸡蛋和1碗燕麦，午餐200g鸡胸肉配西兰花"
        输出: {
            "raw_text": "...",
            "meals": {
                "早餐": { "foods": [...], "totals": {...} },
                "午餐": { "foods": [...], "totals": {...} }
            },
            "daily_totals": {...},
            "warnings": [...],
            "provider": "llm|rule",
        }
        """
        _load_food_db()

        # 第一步：LLM提取食物项
        extracted = _llm_extract(text)
        provider = "llm" if extracted.get("meals") else "rule"

        meals_output = {}
        all_warnings = []
        daily_totals = {
            "calorie": 0, "protein": 0, "fat": 0, "carb": 0,
            "diet_fiber": 0, "calcium": 0, "folic_acid": 0, "dha": 0,
        }

        for meal_group in extracted.get("meals", []):
            meal_type = meal_group.get("meal_type", "未分类")
            raw_foods = meal_group.get("foods", [])

            parsed_foods = []
            meal_totals = {
                "calorie": 0, "protein": 0, "fat": 0, "carb": 0,
                "diet_fiber": 0, "calcium": 0, "folic_acid": 0, "dha": 0,
            }

            for food in raw_foods:
                food_name = food.get("name", "").strip()
                raw_amount = food.get("amount", "100g")
                confidence = food.get("confidence", 0.5)

                # 数据库匹配
                db_match = _fuzzy_match_food(food_name)
                actual_name = db_match["food_name"] if db_match else food_name
                category = db_match["category"] if db_match else ""

                # 单位换算
                grams, amount_desc = _convert_amount(raw_amount, actual_name)

                # 计算营养
                factor = grams / 100
                ingredient_decomposition = None
                
                if db_match:
                    nutrition = {
                        "calorie": round(db_match["calorie"] * factor, 1),
                        "protein": round(db_match["protein"] * factor, 1),
                        "fat": round(db_match["fat"] * factor, 1),
                        "carb": round(db_match["carb"] * factor, 1),
                        "diet_fiber": round(db_match["diet_fiber"] * factor, 2),
                        "calcium": round(db_match["calcium"] * factor, 1),
                        "folic_acid": round(db_match["folic_acid"] * factor, 2),
                        "dha": round(db_match["dha"] * factor, 3),
                        "gi_value": round(db_match["gi_value"], 0) if db_match["gi_value"] else None,
                    }
                else:
                    # 尝试菜品智能还原
                    dish_ingredients = _try_dish_reduction(food_name, grams)
                    
                    if dish_ingredients:
                        ingredient_decomposition = dish_ingredients
                        # 基于食材计算营养总和
                        total_cal = 0
                        total_prot = 0
                        total_fat = 0
                        total_carb = 0
                        total_fiber = 0
                        total_calcium = 0
                        total_folic = 0
                        total_dha = 0
                        
                        for ing in dish_ingredients:
                            ing_name = ing["ingredient"]
                            ing_grams = ing["grams"]
                            ing_match = _fuzzy_match_food(ing_name)
                            
                            if ing_match:
                                ing_factor = ing_grams / 100
                                total_cal += ing_match["calorie"] * ing_factor
                                total_prot += ing_match["protein"] * ing_factor
                                total_fat += ing_match["fat"] * ing_factor
                                total_carb += ing_match["carb"] * ing_factor
                                total_fiber += ing_match["diet_fiber"] * ing_factor
                                total_calcium += ing_match["calcium"] * ing_factor
                                total_folic += ing_match["folic_acid"] * ing_factor
                                total_dha += ing_match["dha"] * ing_factor
                        
                        nutrition = {
                            "calorie": round(total_cal, 1),
                            "protein": round(total_prot, 1),
                            "fat": round(total_fat, 1),
                            "carb": round(total_carb, 1),
                            "diet_fiber": round(total_fiber, 2),
                            "calcium": round(total_calcium, 1),
                            "folic_acid": round(total_folic, 2),
                            "dha": round(total_dha, 3),
                            "gi_value": None,
                        }
                        
                        all_warnings.append({
                            "type": "food_decomposed",
                            "food": food_name,
                            "detail": f"「{food_name}」已拆解为{len(dish_ingredients)}种食材进行营养估算",
                            "severity": "info",
                            "decomposition": dish_ingredients,
                        })
                    else:
                        nutrition = {
                            "calorie": 0, "protein": 0, "fat": 0, "carb": 0,
                            "diet_fiber": 0, "calcium": 0, "folic_acid": 0, "dha": 0,
                            "gi_value": None,
                        }
                        all_warnings.append({
                            "type": "food_not_found",
                            "food": food_name,
                            "detail": f"「{food_name}」未在食物数据库中找到，营养值设为0",
                            "severity": "warning",
                        })

                # 如果 LLM 置信度低，记录警告
                if confidence < 0.5:
                    all_warnings.append({
                        "type": "low_confidence",
                        "food": food_name,
                        "detail": f"「{food_name}」识别置信度较低({confidence})，已匹配到「{actual_name}」",
                        "severity": "info",
                    })

                food_item = {
                    "food_name_original": food_name,
                    "food_name_matched": actual_name,
                    "category": category,
                    "amount_raw": raw_amount,
                    "amount_grams": round(grams, 1),
                    "amount_description": amount_desc,
                    "confidence": confidence,
                    "is_dish_decomposed": ingredient_decomposition is not None,
                    "ingredient_decomposition": ingredient_decomposition,
                    **nutrition,
                }
                parsed_foods.append(food_item)

                # 累加餐次总计
                for key in meal_totals:
                    meal_totals[key] += nutrition.get(key, 0)

            # 四舍五入餐次总计
            for key in meal_totals:
                meal_totals[key] = round(meal_totals[key], 1)

            # 餐次包含该餐的营养评估
            for key in daily_totals:
                daily_totals[key] += meal_totals[key]

            meals_output[meal_type] = {
                "foods": parsed_foods,
                "totals": meal_totals,
            }

        # 四舍五入每日总计
        for key in daily_totals:
            daily_totals[key] = round(daily_totals[key], 1)

        return {
            "raw_text": text,
            "meals": meals_output,
            "daily_totals": daily_totals,
            "warnings": all_warnings,
            "provider": provider,
            "food_count": len(_food_cache) if _food_cache else 0,
        }

    @staticmethod
    def parse_meal(text: str, meal_type: str = "未分类") -> dict:
        """
        快捷方法：指定餐次类型解析

        输入: parse_meal("吃了2个鸡蛋", "早餐")
        等价于: 构建 "早餐吃了2个鸡蛋" 然后 parse
        """
        if meal_type != "未分类":
            text = f"{meal_type}：{text}"
        return NLUParser.parse(text)

    @staticmethod
    def get_stats() -> dict:
        """获取解析引擎统计"""
        _load_food_db()
        return {
            "food_db_size": len(_food_cache) if _food_cache else 0,
            "supported_units": list(UNIT_TO_GRAMS.keys()),
            "special_item_units": list(ITEM_GRAM_PER_UNIT.keys()),
        }


agent = NLUParser()
