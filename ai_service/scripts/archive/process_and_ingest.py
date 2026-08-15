"""
食物营养数据处理与知识库入库脚本
====================================
功能：将爬取的原始食物营养数据清洗、格式化，并导入到向量知识库（ChromaDB）
"""

import json
import os
from datetime import datetime

# 路径配置
AI_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
KB_JSON_PATH = os.path.join(AI_SERVICE_DIR, 'knowledge_base', 'full_knowledge_base.json')
RAW_DATA_PATH = os.path.join(AI_SERVICE_DIR, 'crawler', 'demo_food_data.json')  # 输入的爬取数据

# 加载现有知识库
print(f"加载现有知识库: {KB_JSON_PATH}")
with open(KB_JSON_PATH, 'r', encoding='utf-8') as f:
    existing_cards = json.load(f)

existing_ids = {c['card_id'] for c in existing_cards}
print(f"现有文档数: {len(existing_cards)}")

# 加载爬取的原始数据
print(f"加载原始爬取数据: {RAW_DATA_PATH}")
with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
    raw_food_data = json.load(f)

print(f"原始数据条目数: {len(raw_food_data)}")

# ========== 数据清洗与转换 ==========

def clean_food_data(raw_item):
    """
    清洗单个食物数据，转换为标准格式
    """
    nutrition = raw_item.get('nutrition', {})
    
    # 标准化数值（处理 None, '微量', '-' 等异常值）
    def safe_float(value, default=0.0):
        if value is None or value == '' or value == '微量' or value == '-':
            return default
        try:
            return float(value)
        except:
            return default

    return {
        'name': raw_item['name'],
        'source_url': raw_item.get('source_url', 'https://nlc.chinanutri.cn/'),
        'nutrition': {
            '能量(kcal/100g)': safe_float(nutrition.get('energy_kcal')),
            '蛋白质(g/100g)': safe_float(nutrition.get('protein_g')),
            '脂肪(g/100g)': safe_float(nutrition.get('fat_g')),
            '碳水化合物(g/100g)': safe_float(nutrition.get('carbohydrate_g')),
            '膳食纤维(g/100g)': safe_float(nutrition.get('fiber_g')),
            '钠(mg/100g)': safe_float(nutrition.get('sodium_mg')),
            '维生素A(μg/100g)': safe_float(nutrition.get('vitamin_a_ug')),
            '维生素C(mg/100g)': safe_float(nutrition.get('vitamin_c_mg')),
            '钙(mg/100g)': safe_float(nutrition.get('calcium_mg')),
            '铁(mg/100g)': safe_float(nutrition.get('iron_mg')),
            '锌(mg/100g)': safe_float(nutrition.get('zinc_mg')),
        }
    }

def generate_purified_content(cleaned_item):
    """
    生成结构化的提纯内容（供RAG检索使用）
    """
    name = cleaned_item['name']
    nutrition = cleaned_item['nutrition']
    
    # 构建核心循证结论（以数据为导向）
    content_lines = [
        f"【食物名称】{name}",
        f"【每100克营养成分】",
    ]
    
    # 添加主要营养素
    for nutrient, value in nutrition.items():
        if value > 0:
            content_lines.append(f"- {nutrient}: {value}")
    
    # 添加临床应用建议（简单规则生成）
    protein = nutrition.get('蛋白质(g/100g)', 0)
    energy = nutrition.get('能量(kcal/100g)', 0)
    fiber = nutrition.get('膳食纤维(g/100g)', 0)
    
    content_lines.append(f"【营养评估】")
    if protein >= 15:
        content_lines.append(f"- 优质高蛋白来源（蛋白质≥15g/100g），适合健身人群和增肌需求者。")
    elif protein >= 8:
        content_lines.append(f"- 中等蛋白来源（蛋白质8-15g/100g），可作为日常蛋白质补充。")
    else:
        content_lines.append(f"- 低蛋白来源（蛋白质<8g/100g），主要提供能量和微量营养素。")
    
    if energy >= 300:
        content_lines.append(f"- 高能量密度食物（≥300kcal/100g），减脂人群需控制摄入量。")
    elif energy <= 100:
        content_lines.append(f"- 低能量密度食物（≤100kcal/100g），适合减脂期食用，饱腹感强。")
    
    if fiber >= 5:
        content_lines.append(f"- 富含膳食纤维（≥5g/100g），有助于肠道健康和血糖控制。")
    
    return "\n".join(content_lines)

# ========== 转换为知识库卡片格式 ==========

print("\n转换数据为知识库卡片格式...")
new_cards = []
skipped = 0

for item in raw_food_data:
    food_name = item['name']
    card_id = f"FOOD_{food_name}"
    
    # 去重检查
    if card_id in existing_ids:
        skipped += 1
        continue
    
    # 数据清洗
    cleaned = clean_food_data(item)
    
    # 生成提纯内容
    purified_content = generate_purified_content(cleaned)
    
    # 构建知识库卡片
    card = {
        "card_id": card_id,
        "title": f"食物营养成分数据：{food_name}",
        "group": "通用",
        "topic": "食物营养成分",
        "source_channel": "中国食物营养成分查询平台",
        "source_url": item.get('source_url', 'https://nlc.chinanutri.cn/'),
        "authors": "中国疾病预防控制中心营养与健康所",
        "journal": "国家食物营养成分数据库",
        "pubdate": "2024",
        "purified_content": purified_content,
        "is_official_guide": True,
        "ingest_time": datetime.now().isoformat(),
        "version": 1,
        "sub_group": "食物成分数据",
        # 额外元数据
        "raw_nutrition": cleaned['nutrition'],  # 保存原始营养数据供后续查询
        "food_category": "待定"  # 可在后续分类处理中填充
    }
    
    new_cards.append(card)

print(f"成功转换: {len(new_cards)} 条")
print(f"跳过（已存在）: {skipped} 条")

# ========== 保存到知识库 ==========

if new_cards:
    print(f"\n保存到知识库: {KB_JSON_PATH}")
    all_cards = existing_cards + new_cards
    
    with open(KB_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_cards, f, ensure_ascii=False, indent=2)
    
    print(f"已保存，知识库总文档数: {len(all_cards)}")
else:
    print("\n无新数据需要添加。")
    all_cards = existing_cards

# ========== 统计报告 ==========

print("\n" + "=" * 60)
print("知识库统计报告")
print("=" * 60)

# 按来源统计
channel_counts = {}
for c in all_cards:
    ch = c.get('source_channel', '未知')
    channel_counts[ch] = channel_counts.get(ch, 0) + 1

print("\n【按来源统计】")
for ch, count in sorted(channel_counts.items(), key=lambda x: -x[1]):
    pct = count / len(all_cards) * 100
    print(f"  {ch}: {count} 篇 ({pct:.1f}%)")

# 按主题统计
topic_counts = {}
for c in all_cards:
    t = c.get('topic', '未知')
    topic_counts[t] = topic_counts.get(t, 0) + 1

print("\n【按主题统计 (TOP 15)】")
for t, count in sorted(topic_counts.items(), key=lambda x: -x[1])[:15]:
    print(f"  {t}: {count} 篇")

# 按人群统计
group_counts = {}
for c in all_cards:
    g = c.get('group', '未知')
    group_counts[g] = group_counts.get(g, 0) + 1

print("\n【按人群统计】")
for g, count in sorted(group_counts.items(), key=lambda x: -x[1]):
    print(f"  {g}: {count} 篇")

print(f"\n总文档数: {len(all_cards)}")
print("=" * 60)
print("\n注意：要使新数据在RAG检索中生效，需要运行 import_cards_to_chromadb.py 更新向量数据库。")