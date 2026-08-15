import sys
import os
import json
import sqlite3
import re

BASE_DIR = r"C:\Users\13425\Desktop\个人健康助手\health\china-food-data\china-food-composition-data-main"
JSON_DATA_DIR = os.path.join(BASE_DIR, "json_data")
GI_FILE = os.path.join(BASE_DIR, "json_gi_of_foods", "glycemic_index_of_foods.json")
DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

CATEGORY_MAPPING = {
    "谷类": "主食",
    "谷物": "主食",
    "米": "主食",
    "面": "主食",
    "粉": "主食",
    "粥": "主食",
    "饭": "主食",
    "馒头": "主食",
    "面包": "主食",
    "面条": "主食",
    "通心粉": "主食",
    "豆类": "豆制品",
    "豆腐": "豆制品",
    "豆干": "豆制品",
    "腐竹": "豆制品",
    "蛋类": "肉蛋类",
    "鸡蛋": "肉蛋类",
    "鸭蛋": "肉蛋类",
    "鹌鹑蛋": "肉蛋类",
    "畜肉": "肉蛋类",
    "猪肉": "肉蛋类",
    "牛肉": "肉蛋类",
    "羊肉": "肉蛋类",
    "禽肉": "肉蛋类",
    "鸡肉": "肉蛋类",
    "鸭肉": "肉蛋类",
    "鱼肉": "水产",
    "虾": "水产",
    "蟹": "水产",
    "贝": "水产",
    "蔬菜": "蔬菜",
    "水果": "水果",
    "坚果": "零食",
    "种子": "零食",
    "乳类": "奶类",
    "牛奶": "奶类",
    "酸奶": "奶类",
    "奶酪": "奶类",
    "油脂": "油脂类",
}

FILE_CATEGORY_MAP = {
    "谷类及其制品": "主食",
    "蔬菜类及其制品": "蔬菜",
    "水果类及其制品": "水果",
    "畜肉类及其制品": "肉蛋类",
    "禽肉类及其制品": "肉蛋类",
    "鱼虾蟹贝类": "水产",
    "蛋类及其制品": "肉蛋类",
    "乳类及其制品": "奶类",
    "干豆类及其制品": "豆制品",
    "坚果种子类": "零食",
    "薯类淀粉及其制品": "主食",
    "菌藻类": "蔬菜",
    "植物油": "油脂类",
    "动物油脂类": "油脂类",
    "婴幼儿食品": "主食",
    "其他类": "零食",
}


def parse_float(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s in ['-', '', 'Tr', 'tr', 'N/A', 'NA']:
        return None
    s = re.sub(r'[^\d.]', '', s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def load_gi_data():
    gi_data = {}
    if not os.path.exists(GI_FILE):
        print(f"GI文件不存在: {GI_FILE}")
        return gi_data
    
    with open(GI_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for group in data:
        for item in group.get('list', []):
            food_name = item.get('foodName', '').strip()
            food_name = food_name.replace('*', '').strip()
            gi = parse_float(item.get('GI'))
            if food_name and gi:
                gi_data[food_name] = gi
                name_parts = food_name.split('（')
                if len(name_parts) > 1:
                    base_name = name_parts[0].strip()
                    gi_data[base_name] = gi
    
    print(f"加载GI数据: {len(gi_data)} 条")
    return gi_data


def get_category_from_filename(filename):
    for key, value in FILE_CATEGORY_MAP.items():
        if key in filename:
            return value
    return "其他"


def get_category_from_name(food_name):
    for keyword, category in CATEGORY_MAPPING.items():
        if keyword in food_name:
            return category
    return "其他"


def clear_food_table():
    print("清空食物表...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food")
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM food")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"清空完成，剩余记录: {count}")


def import_to_sqlite():
    print("开始导入中国食物成分数据到SQLite...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    gi_data = load_gi_data()
    
    json_files = [f for f in os.listdir(JSON_DATA_DIR) if f.endswith('.json')]
    print(f"找到 {len(json_files)} 个JSON文件")
    
    imported_count = 0
    skipped_count = 0
    existing_names = set()
    
    cursor.execute("SELECT food_name FROM food WHERE status = 'approved'")
    for row in cursor.fetchall():
        existing_names.add(row[0])
    
    for json_file in json_files:
        filepath = os.path.join(JSON_DATA_DIR, json_file)
        print(f"处理文件: {json_file}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"  读取文件失败: {e}")
            continue
        
        file_category = get_category_from_filename(json_file)
        
        for item in data:
            food_name = item.get('foodName', '').strip()
            
            if not food_name or len(food_name) < 2:
                skipped_count += 1
                continue
            
            if food_name in existing_names:
                skipped_count += 1
                continue
            
            energy = parse_float(item.get('energyKCal'))
            protein = parse_float(item.get('protein'))
            fat = parse_float(item.get('fat'))
            carbs = parse_float(item.get('CHO'))
            
            if energy is None or protein is None or fat is None:
                skipped_count += 1
                continue
            
            if energy < 0 or energy > 5000:
                skipped_count += 1
                continue
            
            fiber = parse_float(item.get('dietaryFiber'))
            calcium = parse_float(item.get('Ca'))
            folic_acid = parse_float(item.get('folate'))
            dha = None
            
            gi = None
            for name in [food_name, food_name.split('（')[0].strip(), food_name.split('[')[0].strip()]:
                if name in gi_data:
                    gi = gi_data[name]
                    break
            
            category = file_category
            if category == "其他":
                category = get_category_from_name(food_name)
            
            try:
                cursor.execute("""
                    INSERT INTO food (food_name, food_category, calorie, protein, fat, carb,
                                     diet_fiber, gi_value, calcium, dha, folic_acid, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (food_name, category, energy, protein, fat, carbs,
                      fiber, gi, calcium, dha, folic_acid, 'approved'))
                
                imported_count += 1
                existing_names.add(food_name)
                
                if imported_count % 500 == 0:
                    conn.commit()
                    print(f"  已导入 {imported_count} 条")
            except Exception as e:
                skipped_count += 1
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM food")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category")
    category_counts = cursor.fetchall()
    
    conn.close()
    
    print(f"\n导入完成!")
    print(f"总记录数: {total_count}")
    print(f"本次导入: {imported_count}")
    print(f"跳过: {skipped_count}")
    print(f"\n分类分布:")
    for cat, cnt in category_counts:
        print(f"  {cat}: {cnt}")
    
    return imported_count


def main():
    print("=" * 60)
    print("中国食物成分数据导入工具 - SQLite")
    print("=" * 60)
    
    clear_food_table()
    
    import_to_sqlite()
    
    print("\n" + "=" * 60)
    print("SQLite导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()