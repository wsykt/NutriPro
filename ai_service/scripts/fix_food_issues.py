"""
修复食物数据问题：
1. 修复蛋白质异常值（如295、363明显是OCR错误，应为2.95、3.63）
2. 清理残留的品牌名称
3. 调整一些优先级
"""
import sqlite3
import re

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

def fix_protein_values():
    """修复蛋白质异常值"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 查找蛋白质异常高的记录（正常食物蛋白质一般不超过90g/100g，除了蛋白粉等）
    cursor.execute("""
        SELECT food_id, food_name, protein, calorie 
        FROM food WHERE protein > 90 AND food_name NOT LIKE '%粉%' 
        AND food_name NOT LIKE '%干%' AND food_name NOT LIKE '%奶粉%'
        AND food_name NOT LIKE '%蛋白%' AND food_name NOT LIKE '%奶酪%'
        AND food_name NOT LIKE '%疙瘩%' AND food_name NOT LIKE '%松%'
    """)
    abnormal = cursor.fetchall()
    print(f"发现 {len(abnormal)} 条蛋白质异常记录:")
    
    fixed = 0
    for food_id, name, protein, calorie in abnormal:
        # 如果蛋白质值大于100，可能是小数点错误，除以100
        if protein > 100:
            new_protein = round(protein / 100, 2)
        elif protein > 50:
            new_protein = round(protein / 10, 2)
        else:
            continue
        
        print(f"  {name}: {protein} -> {new_protein}")
        cursor.execute("UPDATE food SET protein = ? WHERE food_id = ?", (new_protein, food_id))
        fixed += 1
    
    conn.commit()
    conn.close()
    print(f"修复了 {fixed} 条蛋白质异常值")


def clean_residual_brand_names():
    """清理残留的品牌名称"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 查找名称以品牌开头或包含孤立品牌信息的记录
    cursor.execute("SELECT food_id, food_name FROM food WHERE status = 'approved'")
    records = cursor.fetchall()
    
    # 需要清理的前缀品牌（名称开头的）
    brand_prefixes = [
        "晨曦脱脂", "尔蒙特低脂", "澳田脱脂", "牧场脱脂", "佳轻欣脱脂",
        "核桃牛奶", "苏醇纤牛奶", "醇牛奶", "型零乳糖牛奶",
    ]
    
    # 映射到标准名称
    name_mapping = {
        "晨曦脱脂纯牛奶）": "纯牛奶(脱脂)",
        "尔蒙特低脂牛奶）": "纯牛奶(低脂)",
        "澳田脱脂牛奶)": "纯牛奶(脱脂)",
        "牧场脱脂牛奶)": "纯牛奶(脱脂)",
        "佳轻欣脱脂牛奶）": "纯牛奶(脱脂)",
        "核桃牛奶）": "核桃牛奶",
        "苏醇纤牛奶)": "牛奶(调制)",
        "醇牛奶)": "纯牛奶(全脂)",
        "型零乳糖牛奶）": "零乳糖牛奶",
    }
    
    updated = 0
    for food_id, food_name in records:
        new_name = name_mapping.get(food_name.strip())
        if new_name:
            print(f"  重命名: {food_name} -> {new_name}")
            cursor.execute("UPDATE food SET food_name = ? WHERE food_id = ?", (new_name, food_id))
            updated += 1
    
    conn.commit()
    conn.close()
    print(f"清理了 {updated} 条残留品牌名称")


def adjust_priorities():
    """调整优先级，确保代表值和普通食物排序最靠前"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # "代表值"类型的食物设为最高优先级
    cursor.execute("""
        UPDATE food SET priority = 11 
        WHERE food_name LIKE '%代表值%' AND priority < 11
    """)
    print(f"代表值食物提升优先级: {cursor.rowcount} 条")
    
    # "普通"类型的食物设为最高优先级
    cursor.execute("""
        UPDATE food SET priority = 11 
        WHERE (food_name LIKE '%（普通）%' OR food_name LIKE '%(普通)%') AND priority < 11
    """)
    print(f"普通食物提升优先级: {cursor.rowcount} 条")
    
    # 降低淀粉类优先级（不是常用主食）
    cursor.execute("""
        UPDATE food SET priority = 0 
        WHERE food_name LIKE '淀粉%' AND food_category = '主食'
    """)
    print(f"降低淀粉类优先级: {cursor.rowcount} 条")
    
    # 降低罐头类优先级
    cursor.execute("""
        UPDATE food SET priority = CASE WHEN priority > 5 THEN 5 ELSE priority END
        WHERE food_name LIKE '%罐头%'
    """)
    print(f"降低罐头类优先级: {cursor.rowcount} 条")
    
    conn.commit()
    conn.close()


def merge_duplicate_milk():
    """合并重复的牛奶记录（如纯牛奶(脱脂) 有多条）"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 查找重名记录
    cursor.execute("""
        SELECT food_name, COUNT(*) as cnt 
        FROM food WHERE status = 'approved' 
        GROUP BY food_name HAVING cnt > 1
    """)
    duplicates = cursor.fetchall()
    
    print(f"\n发现 {len(duplicates)} 组重名记录:")
    merged = 0
    for dup in duplicates:
        name = dup['food_name']
        cnt = dup['cnt']
        
        cursor.execute("""
            SELECT * FROM food WHERE food_name = ? AND status = 'approved'
            ORDER BY priority DESC, food_id ASC
        """, (name,))
        records = [dict(r) for r in cursor.fetchall()]
        
        if len(records) <= 1:
            continue
        
        # 保留第一条，删除其余
        keep = records[0]
        for r in records[1:]:
            cursor.execute("DELETE FROM food WHERE food_id = ?", (r['food_id'],))
        
        print(f"  {name}: 保留1条，删除{len(records)-1}条")
        merged += len(records) - 1
    
    conn.commit()
    conn.close()
    print(f"合并了 {merged} 条重名记录")


def main():
    print("=" * 50)
    print("食物数据修复工具")
    print("=" * 50)
    
    print("\n[1/4] 修复蛋白质异常值...")
    fix_protein_values()
    
    print("\n[2/4] 清理残留品牌名称...")
    clean_residual_brand_names()
    
    print("\n[3/4] 调整优先级...")
    adjust_priorities()
    
    print("\n[4/4] 合并重名记录...")
    merge_duplicate_milk()
    
    # 最终统计
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM food")
    total = cursor.fetchone()[0]
    print(f"\n最终记录数: {total}")
    conn.close()
    
    print("\n" + "=" * 50)
    print("修复完成！")


if __name__ == "__main__":
    main()
