"""
食物数据优化脚本
功能：
1. 添加 priority 字段，常用食物优先级高，排序时靠前
2. 合并品牌差异小的同类食物（如不同牌子的全脂酸奶→酸奶(全脂)）
3. 合并品种差异小的同类食物（如不同品种苹果→苹果(普通)）
4. 清理冗余数据，保留高质量常用食物
"""
import sqlite3
import re
import statistics

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

# 常用食物列表（高优先级，排序靠前）
COMMON_FOODS = [
    # 主食
    "米饭", "馒头", "面条", "面包", "粥", "大米", "小米", "玉米", "燕麦", "红薯", "土豆",
    "包子", "饺子", "花卷", "烙饼", "油条", "年糕",
    # 肉蛋类
    "猪肉", "牛肉", "羊肉", "鸡肉", "鸭肉", "鸡蛋", "鸭蛋", "排骨", "里脊", "鸡胸",
    # 水产
    "鱼", "虾", "蟹", "带鱼", "鲫鱼", "草鱼", "鲤鱼", "三文鱼", "鲈鱼", "海带",
    # 蔬菜
    "白菜", "菠菜", "芹菜", "黄瓜", "番茄", "西红柿", "茄子", "豆角", "西兰花", "胡萝卜",
    "萝卜", "洋葱", "大蒜", "生姜", "辣椒", "生菜", "油菜", "韭菜", "蘑菇", "木耳",
    # 水果
    "苹果", "香蕉", "橙子", "葡萄", "西瓜", "梨", "桃", "草莓", "芒果", "菠萝",
    # 豆制品
    "豆腐", "豆浆", "豆干", "腐竹", "黄豆", "绿豆", "红豆",
    # 奶类
    "牛奶", "酸奶", "奶酪", "奶粉",
    # 油脂/其他
    "橄榄油", "花生油", "豆腐脑",
]

# 品牌关键词（用于识别和剥离品牌信息）
BRAND_KEYWORDS = [
    "伊利", "蒙牛", "光明", "三元", "完达山", "辉山", "圣牧", "夏进", "新希望", "麦趣尔",
    "天润", "西域春", "广泽", "龙丹", "乐百氏", "佳丽", "盖瑞", "瑞缘", "花园", "帕玛拉特",
    "美国牛", "德国牛", "德国艾德牧", "新西兰安佳", "新西兰恒天然", "明治", "澳大利亚德运",
    "澳大利亚澳田", "爱尔兰金凯利", "瑞士艾美", "法国得乐思", "波兰美波", "丹麦爱氏晨曦",
    "意大利培兰", "比利时纯牧", "亨氏", "方广", "旺仔", "特仑苏", "金典", "优+",
    "沙参牌", "长富牌", "爱氏晨曦", "安佳", "德运", "艾美", "培兰", "得乐思",
    "牌", "纯牛奶", "鲜牛奶", "复原乳", "巴氏杀菌乳", "风味发酵乳", "高温杀菌乳",
    "浓缩酸奶", "老酸奶", "凝固型", "草莓", "芒果", "蓝莓", "覆盆子", "菠萝味",
    "低脂风味", "全脂风味", "益家", "浓缩纯奶", "澳醇", "高品质", "有机",
    "牧场", "千岛湖", "松花江", "现代牧业", "现代牧场", "鲜博士", "醇壹",
]

# 需要合并的品种组（key=组名, value=匹配关键词列表）
VARIETY_GROUPS = {
    "苹果(普通)": ["伏苹果", "倭锦苹果", "印度苹果", "国光苹果", "旱苹果", "祝光苹果",
                  "秋里蒙苹果", "红元帅苹果", "红富士苹果", "红星苹果", "红玉苹果",
                  "红香蕉苹果", "金元帅苹果", "青香蕉苹果", "香玉苹果", "黄元帅苹果", "黄香蕉苹果"],
}


def add_priority_column():
    """添加 priority 字段"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE food ADD COLUMN priority INTEGER DEFAULT 0")
        conn.commit()
        print("已添加 priority 字段")
    except sqlite3.OperationalError:
        print("priority 字段已存在，跳过")
    conn.close()


def set_common_foods_priority():
    """为常用食物设置高优先级"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    updated = 0
    for food in COMMON_FOODS:
        cursor.execute("""
            UPDATE food SET priority = 10 
            WHERE food_name LIKE ? AND priority < 10
        """, (f"%{food}%",))
        updated += cursor.rowcount
    
    # 代表值类型的食物也设为高优先级
    cursor.execute("""
        UPDATE food SET priority = 9 
        WHERE (food_name LIKE '%代表值%' OR food_name LIKE '%（普通）%' OR food_name LIKE '%(普通)%')
        AND priority < 9
    """)
    updated += cursor.rowcount
    
    conn.commit()
    conn.close()
    print(f"已设置 {updated} 条常用食物的高优先级")


def normalize_name(food_name):
    """
    规范化食物名称，剥离品牌信息
    例：'纯牛奶(全脂,伊利牌)' → '纯牛奶(全脂)'
        '酸奶(全脂,佳丽牌,益家全脂风味发酵乳)' → '酸奶(全脂)'
    """
    # 处理括号内的品牌信息
    # 匹配 括号开头 + 脂肪等级（全脂/低脂/脱脂）+ 后续品牌信息
    patterns = [
        # (全脂,品牌...) → (全脂)
        (r'((?:纯牛奶|鲜牛奶|酸奶|牛奶|调制乳)\s*[\(（])\s*((?:全脂|低脂|脱脂|高蛋白|代表值|橘味|果料|果粒|调味)[^)）]*?)[,，]', r'\1\2)'),
        (r'((?:纯牛奶|鲜牛奶|酸奶|牛奶|调制乳)\s*[\(（])\s*((?:全脂|低脂|脱脂|高蛋白|代表值|橘味|果料|果粒|调味)[^)）]*?)[\)）]', r'\1\2)'),
    ]
    
    result = food_name
    for pat, repl in patterns:
        result = re.sub(pat, repl, result)
    
    # 如果名称还有品牌信息，尝试直接剥离
    if '(' in result or '（' in result:
        # 提取括号内容
        match = re.search(r'[\(（]([^)）]*)[\)）]', result)
        if match:
            inner = match.group(1)
            # 分割逗号
            parts = re.split(r'[,，]', inner)
            # 保留非品牌部分
            kept_parts = []
            for part in parts:
                part = part.strip()
                is_brand = False
                for brand in BRAND_KEYWORDS:
                    if brand in part:
                        is_brand = True
                        break
                if not is_brand and part:
                    kept_parts.append(part)
            
            if kept_parts:
                prefix = result[:match.start()].strip()
                new_inner = ','.join(kept_parts)
                result = f"{prefix}({new_inner})"
            else:
                # 全是品牌信息，只保留前缀
                result = result[:match.start()].strip()
    
    return result.strip()


def calculate_avg(records):
    """计算多条记录的平均值"""
    if not records:
        return None
    
    fields = ['calorie', 'protein', 'fat', 'carb', 'diet_fiber', 'gi_value', 
              'calcium', 'dha', 'folic_acid']
    avg = {}
    for field in fields:
        values = [r[field] for r in records if r[field] is not None]
        avg[field] = round(statistics.mean(values), 1) if values else None
    
    return avg


def calculate_variance(records, field='calorie'):
    """计算某字段的变异系数（标准差/均值），用于判断差异大小"""
    values = [r[field] for r in records if r[field] is not None]
    if len(values) < 2:
        return 0
    mean = statistics.mean(values)
    if mean == 0:
        return 0
    stdev = statistics.stdev(values)
    return stdev / mean


def merge_brand_variants():
    """合并品牌差异小的同类食物"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM food WHERE status = 'approved'")
    all_foods = [dict(row) for row in cursor.fetchall()]
    
    # 按规范化名称分组
    groups = {}
    for food in all_foods:
        normalized = normalize_name(food['food_name'])
        if normalized not in groups:
            groups[normalized] = []
        groups[normalized].append(food)
    
    # 找出需要合并的组（同名>1条且差异小）
    merged_count = 0
    deleted_count = 0
    new_records = []
    
    for normalized_name, records in groups.items():
        if len(records) <= 1:
            continue
        
        # 只处理包含品牌信息的原始名称（说明是品牌变体）
        has_brand_variant = any(
            any(brand in r['food_name'] for brand in BRAND_KEYWORDS)
            for r in records
        )
        if not has_brand_variant:
            continue
        
        # 计算热量变异系数，判断差异是否可接受
        cv = calculate_variance(records, 'calorie')
        
        if cv > 0.3:  # 差异过大，不合并
            continue
        
        # 计算平均值
        avg = calculate_avg(records)
        if not avg or avg['calorie'] is None:
            continue
        
        # 选择保留的记录（优先选 priority 最高的，其次 food_id 最小的）
        records.sort(key=lambda r: (-r.get('priority', 0) or 0, r['food_id']))
        keep_record = records[0]
        
        # 更新保留记录的名称和营养值
        new_name = normalized_name
        # 如果规范化名称为空或太短，用原名称
        if not new_name or len(new_name) < 2:
            new_name = keep_record['food_name']
        
        cursor.execute("""
            UPDATE food SET 
                food_name = ?,
                calorie = ?, protein = ?, fat = ?, carb = ?,
                diet_fiber = ?, gi_value = ?, calcium = ?, dha = ?, folic_acid = ?,
                priority = CASE WHEN priority < 8 THEN 8 ELSE priority END
            WHERE food_id = ?
        """, (new_name, avg['calorie'], avg['protein'], avg['fat'], avg['carb'],
              avg['diet_fiber'], avg['gi_value'], avg['calcium'], avg['dha'], 
              avg['folic_acid'], keep_record['food_id']))
        
        # 删除其他变体
        for r in records[1:]:
            cursor.execute("DELETE FROM food WHERE food_id = ?", (r['food_id'],))
            deleted_count += 1
        
        merged_count += 1
        new_records.append((new_name, len(records), avg['calorie']))
    
    conn.commit()
    conn.close()
    
    print(f"\n品牌合并完成:")
    print(f"  合并组数: {merged_count}")
    print(f"  删除冗余: {deleted_count} 条")
    print(f"\n部分合并示例:")
    for name, cnt, cal in new_records[:10]:
        print(f"  {name} (合并{cnt}条, 平均{cal}kcal)")


def merge_variety_groups():
    """合并品种差异小的同类食物（如不同品种苹果）"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    for group_name, keywords in VARIETY_GROUPS.items():
        # 查找所有匹配的品种
        placeholders = ' OR '.join(['food_name LIKE ?' for _ in keywords])
        params = [f"%{kw}%" for kw in keywords]
        
        cursor.execute(f"""
            SELECT * FROM food WHERE ({placeholders}) AND status = 'approved'
        """, params)
        records = [dict(row) for row in cursor.fetchall()]
        
        if len(records) < 2:
            continue
        
        # 检查差异大小
        cv = calculate_variance(records, 'calorie')
        if cv > 0.4:  # 品种差异较大，不合并
            print(f"  {group_name}: 变异系数 {cv:.2f} 较大，跳过")
            continue
        
        avg = calculate_avg(records)
        if not avg or avg['calorie'] is None:
            continue
        
        # 删除所有品种
        for r in records:
            cursor.execute("DELETE FROM food WHERE food_id = ?", (r['food_id'],))
        
        # 插入合并后的普通品种
        category = records[0]['food_category']
        cursor.execute("""
            INSERT INTO food (food_name, food_category, calorie, protein, fat, carb,
                             diet_fiber, gi_value, calcium, dha, folic_acid, status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 9)
        """, (group_name, category, avg['calorie'], avg['protein'], avg['fat'], avg['carb'],
              avg['diet_fiber'], avg['gi_value'], avg['calcium'], avg['dha'], avg['folic_acid']))
        
        print(f"  {group_name}: 合并 {len(records)} 个品种, 平均 {avg['calorie']}kcal")
    
    conn.commit()
    conn.close()


def cleanup_low_quality():
    """清理低质量数据"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 删除婴幼儿配方食品（不适合普通用户）
    cursor.execute("DELETE FROM food WHERE food_name LIKE '%婴幼儿%' OR food_name LIKE '%婴儿配方%'")
    deleted1 = cursor.rowcount
    
    # 删除名称异常的记录
    cursor.execute("DELETE FROM food WHERE food_name LIKE '%（）%' OR food_name LIKE '%()%'")
    deleted2 = cursor.rowcount
    
    conn.commit()
    conn.close()
    print(f"\n清理低质量数据: 删除婴幼儿食品 {deleted1} 条, 异常名称 {deleted2} 条")


def print_stats():
    """打印统计信息"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM food")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM food WHERE priority >= 9")
    common = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM food WHERE priority >= 10")
    top = cursor.fetchone()[0]
    
    print(f"\n{'='*50}")
    print(f"优化后统计:")
    print(f"  总记录数: {total}")
    print(f"  高优先级(>=9): {common}")
    print(f"  顶级常用(>=10): {top}")
    
    print(f"\n分类分布:")
    cursor.execute("""
        SELECT food_category, COUNT(*), 
               SUM(CASE WHEN priority >= 9 THEN 1 ELSE 0 END) as common_count
        FROM food GROUP BY food_category ORDER BY COUNT(*) DESC
    """)
    for cat, cnt, common_cnt in cursor.fetchall():
        print(f"  {cat}: {cnt} 条 (常用 {common_cnt})")
    
    print(f"\n常用食物示例(优先级>=10, 前20条):")
    cursor.execute("""
        SELECT food_name, food_category, calorie, protein 
        FROM food WHERE priority >= 10 
        ORDER BY food_category, food_name LIMIT 20
    """)
    for name, cat, cal, prot in cursor.fetchall():
        print(f"  [{cat}] {name}: {cal}kcal, 蛋白{prot}g")
    
    conn.close()


def main():
    print("=" * 60)
    print("食物数据优化工具")
    print("=" * 60)
    
    print("\n[1/5] 添加 priority 字段...")
    add_priority_column()
    
    print("\n[2/5] 设置常用食物优先级...")
    set_common_foods_priority()
    
    print("\n[3/5] 合并品牌变体...")
    merge_brand_variants()
    
    print("\n[4/5] 合并品种组...")
    merge_variety_groups()
    
    print("\n[5/5] 清理低质量数据...")
    cleanup_low_quality()
    
    print_stats()
    
    print(f"\n{'='*60}")
    print("优化完成！")
    print("="*60)


if __name__ == "__main__":
    main()
