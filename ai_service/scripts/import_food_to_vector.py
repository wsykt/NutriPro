import sys
import os
import sqlite3
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

FOOD_NAME_MAPPINGS = {
    "apple": "苹果", "apples": "苹果",
    "banana": "香蕉", "bananas": "香蕉",
    "orange": "橙子", "oranges": "橙子",
    "grape": "葡萄", "grapes": "葡萄",
    "pear": "梨", "pears": "梨",
    "peach": "桃子", "peaches": "桃子",
    "strawberry": "草莓", "strawberries": "草莓",
    "blueberry": "蓝莓", "blueberries": "蓝莓",
    "raspberry": "覆盆子", "raspberries": "覆盆子",
    "blackberry": "黑莓", "blackberries": "黑莓",
    "mango": "芒果", "mangoes": "芒果",
    "pineapple": "菠萝", "pineapples": "菠萝",
    "watermelon": "西瓜",
    "kiwi": "猕猴桃", "kiwifruit": "猕猴桃",
    "lemon": "柠檬", "lemons": "柠檬",
    "lime": "青柠", "limes": "青柠",
    "grapefruit": "葡萄柚",
    "pomegranate": "石榴",
    "cherry": "樱桃", "cherries": "樱桃",
    "plum": "李子", "plums": "李子",
    "apricot": "杏", "apricots": "杏",
    "peanut": "花生", "peanuts": "花生",
    "almond": "杏仁", "almonds": "杏仁",
    "walnut": "核桃", "walnuts": "核桃",
    "cashew": "腰果", "cashews": "腰果",
    "pistachio": "开心果", "pistachios": "开心果",
    "hazelnut": "榛子", "hazelnuts": "榛子",
    "macadamia": "夏威夷果", "macadamias": "夏威夷果",
    "rice": "米饭", "white rice": "白米饭", "brown rice": "糙米",
    "bread": "面包", "white bread": "白面包", "whole wheat bread": "全麦面包",
    "pasta": "面条", "spaghetti": "意大利面",
    "wheat": "小麦", "oat": "燕麦", "oats": "燕麦",
    "corn": "玉米", "maize": "玉米",
    "potato": "土豆", "potatoes": "土豆", "sweet potato": "红薯",
    "carrot": "胡萝卜", "carrots": "胡萝卜",
    "tomato": "西红柿", "tomatoes": "西红柿",
    "spinach": "菠菜",
    "broccoli": "西兰花",
    "cauliflower": "菜花",
    "cabbage": "卷心菜",
    "lettuce": "生菜",
    "onion": "洋葱", "onions": "洋葱",
    "garlic": "大蒜",
    "egg": "鸡蛋", "eggs": "鸡蛋",
    "chicken": "鸡肉",
    "beef": "牛肉",
    "pork": "猪肉",
    "fish": "鱼",
    "salmon": "三文鱼",
    "shrimp": "虾", "prawn": "虾", "prawns": "虾",
    "milk": "牛奶",
    "cheese": "奶酪",
    "yogurt": "酸奶",
    "tofu": "豆腐",
    "soy": "大豆", "soybean": "大豆",
    "bean": "豆类", "beans": "豆类",
    "lentil": "扁豆", "lentils": "扁豆",
    "chickpea": "鹰嘴豆", "chickpeas": "鹰嘴豆",
    "coffee": "咖啡",
    "tea": "茶",
    "chocolate": "巧克力",
    "butter": "黄油",
    "oil": "油", "olive oil": "橄榄油", "vegetable oil": "植物油",
    "sugar": "糖",
    "salt": "盐",
    "honey": "蜂蜜",
    "oatmeal": "燕麦片",
    "cereal": "麦片",
    "ice cream": "冰淇淋",
    "cake": "蛋糕",
    "cookie": "饼干", "biscuit": "饼干",
    "pizza": "披萨",
    "soup": "汤",
    "juice": "果汁",
    "water": "水",
    "cucumber": "黄瓜", "cucumbers": "黄瓜",
    "eggplant": "茄子",
    "pepper": "辣椒", "bell pepper": "甜椒",
    "mushroom": "蘑菇", "mushrooms": "蘑菇",
    "avocado": "牛油果",
    "coconut": "椰子",
    "date": "枣", "dates": "枣",
    "fig": "无花果", "figs": "无花果",
    "guava": "番石榴",
    "lychee": "荔枝", "litchi": "荔枝",
    "papaya": "木瓜",
    "persimmon": "柿子",
    "tangerine": "橘子",
    "clementine": "柑橘",
    "satsuma": "蜜橘",
    "mandarin": "橘子",
    "turkey": "火鸡",
    "duck": "鸭肉",
    "goose": "鹅肉",
    "lamb": "羊肉",
    "veal": "小牛肉",
    "cod": "鳕鱼",
    "tuna": "金枪鱼",
    "mackerel": "鲭鱼",
    "herring": "鲱鱼",
    "sardine": "沙丁鱼",
    "trout": "鳟鱼",
    "tilapia": "罗非鱼",
    "catfish": "鲶鱼",
    "clam": "蛤蜊",
    "oyster": "牡蛎",
    "scallop": "扇贝",
    "crab": "螃蟹",
    "lobster": "龙虾",
    "milk chocolate": "牛奶巧克力",
    "dark chocolate": "黑巧克力",
    "white chocolate": "白巧克力",
}

PROCESSED_KEYWORDS = [
    "protein", "whey", "supplement", "vitamin",
    "alcohol", "beer", "wine", "whiskey",
    "instant", "prepackaged", "ready", "microwave",
]

def has_chinese(text):
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def get_clean_name(name):
    if not name:
        return ""
    
    if has_chinese(name):
        cleaned = re.sub(r'[^\u4e00-\u9fff]', '', name)
        return cleaned.strip()
    
    lower_name = name.lower()
    
    for en_name, zh_name in FOOD_NAME_MAPPINGS.items():
        if en_name.lower() == lower_name:
            return zh_name
        if en_name in lower_name:
            return zh_name
    
    return name.strip()

def is_valid_food_record(food_name, calorie, protein, fat, carb, category):
    if calorie is None or calorie <= 0:
        return False
    
    if category == "其他":
        return False
    
    calorie_ranges = {
        "主食": (10, 1000),
        "蔬菜": (5, 500),
        "水果": (10, 500),
        "肉蛋类": (80, 800),
        "奶类": (30, 500),
        "豆制品": (30, 500),
        "水产": (50, 500),
        "油脂类": (50, 1000),
    }
    
    if category in calorie_ranges:
        min_cal, max_cal = calorie_ranges[category]
        if calorie < min_cal or calorie > max_cal:
            return False
    
    if protein is not None and protein > 200:
        return False
    if fat is not None and fat > 200:
        return False
    if carb is not None and carb > 200:
        return False
    
    return True

def is_processed_food(name):
    return any(kw in name.lower() for kw in PROCESSED_KEYWORDS)

def add_to_vector_db():
    print("开始将食物数据加入向量知识库...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT food_name, food_category, calorie, protein, fat, carb, diet_fiber, gi_value
        FROM food WHERE status = 'approved'
    """)
    
    food_records = cursor.fetchall()
    conn.close()
    
    print(f"从数据库读取到 {len(food_records)} 条食物记录")
    
    documents = []
    metadatas = []
    ids = []
    added_names = set()
    
    for idx, record in enumerate(food_records):
        food_name, category, calorie, protein, fat, carb, fiber, gi = record
        
        if not is_valid_food_record(food_name, calorie, protein, fat, carb, category):
            continue
        
        clean_name = get_clean_name(food_name)
        
        if not clean_name or len(clean_name) < 2:
            continue
        
        if clean_name in added_names:
            continue
        
        content = f"{clean_name}（{category}）：热量{calorie}kcal/100g，蛋白质{protein}g，脂肪{fat}g，碳水{carb}g"
        if fiber:
            content += f"，膳食纤维{fiber}g"
        if gi:
            content += f"，GI值{gi}"
        
        documents.append(content)
        metadatas.append({
            "category": "food_knowledge",
            "food_name": clean_name,
            "food_category": category,
        })
        ids.append(f"food_{idx}")
        added_names.add(clean_name)
    
    print(f"筛选后准备添加 {len(documents)} 条到向量库")
    
    batch_size = 500
    total_batches = (len(documents) + batch_size - 1) // batch_size
    success_count = 0
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        try:
            retriever.add(batch_docs, batch_metas, batch_ids)
            success_count += len(batch_docs)
            print(f"已添加批次 {i//batch_size + 1}/{total_batches}, 累计 {success_count} 条")
        except Exception as e:
            print(f"添加批次 {i//batch_size + 1} 失败: {e}")
            return
    
    print(f"向量知识库更新完成，总记录数: {retriever.count()}")


def main():
    print("=" * 60)
    print("食物成分数据导入工具 - 向量知识库")
    print("=" * 60)
    
    add_to_vector_db()
    
    print("\n" + "=" * 60)
    print("向量知识库导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()