import sys
import os
import csv
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from food_name_translation import translate_food_name, translate_category

TSV_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\food_data\data\en.openfoodfacts.org.products.tsv"
DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"


def parse_float(value):
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


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
    print("开始导入食物数据到SQLite...")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM food")
    existing_count = cursor.fetchone()[0]
    print(f"数据库中已有食物记录: {existing_count}")
    
    cursor.execute("SELECT food_name FROM food WHERE status = 'approved'")
    existing_names = set(row[0] for row in cursor.fetchall())
    print(f"已存在的食物名称数量: {len(existing_names)}")
    
    imported_count = 0
    skipped_count = 0
    translated_count = 0
    not_translated_count = 0
    
    with open(TSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for i, row in enumerate(reader):
            if i % 50000 == 0 and i > 0:
                print(f"已处理 {i} 行, 导入 {imported_count} 条")
            
            product_name = row.get('product_name', '').strip()
            generic_name = row.get('generic_name', '').strip()
            food_name = product_name or generic_name
            
            if not food_name or len(food_name) < 2:
                skipped_count += 1
                continue
            
            translated_name = translate_food_name(food_name)
            if translated_name != food_name:
                translated_count += 1
            else:
                not_translated_count += 1
            
            if translated_name in existing_names:
                skipped_count += 1
                continue
            
            energy = parse_float(row.get('energy_100g'))
            proteins = parse_float(row.get('proteins_100g'))
            fat = parse_float(row.get('fat_100g'))
            carbs = parse_float(row.get('carbohydrates_100g'))
            
            if energy is None or proteins is None or fat is None or carbs is None:
                skipped_count += 1
                continue
            
            if energy < 0 or energy > 5000:
                skipped_count += 1
                continue
            
            category = translate_category(row.get('categories', ''))
            fiber = parse_float(row.get('fiber_100g'))
            gi = parse_float(row.get('glycemic-index_100g'))
            calcium = parse_float(row.get('calcium_100g'))
            folic_acid = parse_float(row.get('vitamin-b9_100g'))
            omega3 = parse_float(row.get('omega-3-fat_100g'))
            dha = parse_float(row.get('-docosahexaenoic-acid_100g'))
            
            if dha is None and omega3 is not None:
                dha = omega3 * 0.3
            
            try:
                cursor.execute("""
                    INSERT INTO food (food_name, food_category, calorie, protein, fat, carb,
                                     diet_fiber, gi_value, calcium, dha, folic_acid, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (translated_name, category, energy, proteins, fat, carbs,
                      fiber, gi, calcium, dha, folic_acid, 'approved'))
                
                imported_count += 1
                existing_names.add(translated_name)
                
                if imported_count % 500 == 0:
                    conn.commit()
            except Exception as e:
                skipped_count += 1
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM food")
    total_count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"\n导入完成!")
    print(f"总记录数: {total_count}")
    print(f"本次导入: {imported_count}")
    print(f"跳过: {skipped_count}")
    print(f"已翻译: {translated_count}")
    print(f"未翻译: {not_translated_count}")
    
    return imported_count


def main():
    print("=" * 60)
    print("食物成分数据导入工具 - SQLite")
    print("=" * 60)
    
    clear_food_table()
    
    import_to_sqlite()
    
    print("\n" + "=" * 60)
    print("SQLite导入完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()