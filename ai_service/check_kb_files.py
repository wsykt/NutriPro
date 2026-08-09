import json
import os

kb_path = r'c:\Users\13425\Desktop\个人健康助手\health\ai_service\knowledge_base\full_knowledge_base.json'
data = json.load(open(kb_path, 'r', encoding='utf-8'))

files_to_check = [
    "《2025—2030年美国膳食指南》的科学性与适用性评价及其对我国的启示",
    "《成人糖尿病食养指南（2023 年版）》",
    "2025-2030美国膳食指南中文版",
    "成人肥胖食养指南（2024年版）",
    "常量元素",
    "成人糖尿病食养指南（2023年版）",
    "儿童青少年肥胖食养指南（2024年版）",
    "儿童青少年生长迟缓食养指南（2023年版）",
    "宏量营养素",
    "家庭减盐行为指南（TCNSS+022-2023）",
    "健康食堂建设管理规范（TCNSS+012-2021）",
    "科学营养餐桌·全民高质量膳食促进行动报告(1)",
    "妊娠期糖尿病患者膳食指导",
    "老年人膳食指导",
    "食物蛋白质质量评价技术规范（TCNSS+035-2025）",
    "水溶性维生素",
    "微量元素",
    "预包装食品蛋白质质量标示规范（TCNSS+046-2026）",
    "预包装食品嘌呤含量分级和标示（TCNSS+026-2024）",
    "预包装食品血糖生成指数标示规范（TCNSS+018-2023）",
    "脂溶性维生素"
]

print("=" * 60)
print("知识库文档核查报告")
print("=" * 60)

results = []

for f in files_to_check:
    matched = False
    matched_docs = []
    
    # 提取文件名中的核心关键词进行匹配
    # 例如："成人糖尿病食养指南" -> "糖尿病" 或 "成人糖尿病"
    keywords = []
    if "美国膳食指南" in f:
        keywords = ["美国膳食指南", "膳食指南"]
    elif "糖尿病食养指南" in f or "妊娠期糖尿病" in f:
        keywords = ["糖尿病", "糖尿病食养", "妊娠期糖尿病"]
    elif "肥胖食养指南" in f:
        keywords = ["肥胖", "食养"]
    elif "生长迟缓" in f:
        keywords = ["生长迟缓"]
    elif "减盐" in f:
        keywords = ["减盐", "钠"]
    elif "维生素" in f:
        if "水溶性" in f:
            keywords = ["水溶性维生素", "维生素B", "维生素C"]
        elif "脂溶性" in f:
            keywords = ["脂溶性维生素", "维生素A", "维生素D", "维生素E"]
        else:
            keywords = ["维生素"]
    elif "常量元素" in f:
        keywords = ["常量元素", "矿物质", "钙", "镁"]
    elif "微量元素" in f:
        keywords = ["微量元素", "铁", "锌", "硒"]
    elif "宏量营养素" in f:
        keywords = ["宏量营养素", "碳水化合物", "蛋白质", "脂肪"]
    elif "嘌呤" in f:
        keywords = ["嘌呤", "痛风"]
    elif "血糖生成指数" in f:
        keywords = ["血糖生成指数", "GI", "血糖控制"]
    elif "蛋白质质量" in f:
        keywords = ["蛋白质质量", "优质蛋白"]
    elif "老年人" in f:
        keywords = ["老年人", "老年营养"]
    elif "儿童青少年" in f:
        keywords = ["儿童青少年", "青少年营养", "儿童营养"]
    elif "高质量膳食" in f:
        keywords = ["高质量膳食", "膳食模式"]
    elif "健康食堂" in f:
        keywords = ["健康食堂", "餐饮规范"]
    else:
        keywords = [f[:10]]

    for doc in data:
        title = doc.get('title', '')
        topic = doc.get('topic', '')
        content = doc.get('purified_content', '')
        
        # 检查标题、主题或内容中是否包含关键词
        if any(kw in title or kw in topic or kw in content for kw in keywords):
            matched = True
            matched_docs.append({
                'title': title[:50] + '...' if len(title) > 50 else title,
                'topic': topic,
                'channel': doc.get('source_channel', '')
            })
    
    status = "✅ 已在库" if matched else "❌ 不在库"
    print(f"\n[{status}] {f}")
    if matched:
        print(f"   匹配到 {len(matched_docs)} 篇相关文档:")
        for md in matched_docs[:3]:  # 最多显示3篇
            print(f"   - [{md['channel']}] {md['topic']}: {md['title']}")
        if len(matched_docs) > 3:
            print(f"   ... 还有 {len(matched_docs) - 3} 篇")
    else:
        print(f"   ⚠️  未找到相关文档，建议添加。")

print("\n" + "=" * 60)
print("核查完毕。")
