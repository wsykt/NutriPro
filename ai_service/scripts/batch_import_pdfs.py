import sys
import os
import re
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

PDF_DIR = r"C:\Users\13425\Desktop\个人健康助手"
KB_DOC_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\ai_service\knowledge\knowledge_base.md"

CATEGORY_MAP = {
    "糖尿病": "crowd_specific",
    "肥胖": "crowd_specific",
    "儿童": "crowd_specific",
    "青少年": "crowd_specific",
    "老年人": "crowd_specific",
    "孕妇": "crowd_specific",
    "妊娠": "crowd_specific",
    "学生": "crowd_specific",
    "膳食指南": "dietary_guideline",
    "食养指南": "dietary_guideline",
    "膳食指导": "dietary_guideline",
    "膳食规范": "nutrition_standard",
    "标示规范": "nutrition_standard",
    "技术规范": "nutrition_standard",
    "管理规范": "nutrition_standard",
    "营养指南": "nutrition_standard",
    "维生素": "food_knowledge",
    "元素": "food_knowledge",
    "营养素": "food_knowledge",
    "蛋白质": "food_knowledge",
    "嘌呤": "food_knowledge",
    "GI": "food_knowledge",
    "血糖生成指数": "food_knowledge",
    "减盐": "health_standard",
    "报告": "nutrition_standard",
}

FOOD_CATEGORIES = ['主食', '蔬菜', '水果', '肉蛋类', '豆制品', '奶类', '水产', '油脂类']


def extract_text_from_pdf(pdf_path):
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text
    except ImportError:
        return None
    except Exception as e:
        print(f"  读取失败: {e}")
        return None


def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\u4e00-\u9fff0-9a-zA-Z，。！？、；：""''（）【】《》—…·]', '', text)
    return text.strip()


def split_into_chunks(text, chunk_size=500):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end < len(text):
            last_period = text.rfind('。', start, end)
            last_comma = text.rfind('，', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
            elif last_comma > start + chunk_size // 2:
                end = last_comma + 1
        chunk = text[start:end].strip()
        if len(chunk) >= 30:
            chunks.append(chunk)
        start = end
    return chunks


def get_category_from_filename(filename):
    for keyword, category in CATEGORY_MAP.items():
        if keyword in filename:
            return category
    return "nutrition_standard"


def import_single_pdf(pdf_path):
    filename = os.path.basename(pdf_path)
    name_without_ext = filename.replace('.pdf', '')
    
    print(f"\n处理: {filename}")
    
    text = extract_text_from_pdf(pdf_path)
    
    if not text or len(text) < 100:
        print("  跳过: 文本内容过少或无法提取")
        return None
    
    print(f"  提取文本: {len(text)} 字符")
    
    clean = clean_text(text)
    print(f"  清理后: {len(clean)} 字符")
    
    chunks = split_into_chunks(clean, chunk_size=500)
    print(f"  分割为: {len(chunks)} 个片段")
    
    if len(chunks) == 0:
        print("  跳过: 没有有效片段")
        return None
    
    category = get_category_from_filename(name_without_ext)
    
    documents = []
    metadatas = []
    ids = []
    
    safe_name = re.sub(r'[^\w]', '_', name_without_ext)[:30]
    
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({
            "category": category,
            "source": name_without_ext,
            "chunk_index": i,
        })
        ids.append(f"pdf_{safe_name}_{i}")
    
    batch_size = 100
    success_count = 0
    
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        try:
            retriever.add(batch_docs, batch_metas, batch_ids)
            success_count += len(batch_docs)
        except Exception as e:
            print(f"  添加失败: {e}")
            return None
    
    print(f"  成功添加: {success_count} 条")
    
    return {
        "filename": filename,
        "name": name_without_ext,
        "category": category,
        "chunks": len(chunks),
        "chars": len(clean),
    }


def generate_kb_doc(import_results):
    if not os.path.exists(os.path.dirname(KB_DOC_FILE)):
        os.makedirs(os.path.dirname(KB_DOC_FILE))
    
    content = """# 健康助手知识库文档

## 概述

本文档记录个人健康助手AI系统中引入的所有知识资源，包括向量知识库中的结构化知识、食物成分数据以及PDF文档内容。

---

## 一、基础健康知识（30条）

### 1.1 膳食指南
- 中国居民膳食指南2022核心推荐一：食物多样，合理搭配
- 中国居民膳食指南2022核心推荐二：少盐少油，控糖限酒
- 中国居民膳食指南2022核心推荐三：吃动平衡，健康体重
- 中国居民膳食指南2022核心推荐四：杜绝浪费，兴新食尚

### 1.2 营养标准
- 成人蛋白质推荐摄入量
- 膳食纤维推荐摄入量
- 钙推荐摄入量
- 铁推荐摄入量
- 维生素D推荐摄入量
- 三大营养素供能比

### 1.3 健康标准
- BMI健康标准（中国标准）
- 每日饮水建议

### 1.4 人群特定指南
- 老年人膳食建议
- 孕妇膳食建议
- 青少年膳食建议
- 糖尿病患者膳食建议
- 健身人群膳食建议

### 1.5 食物知识
- 常见主食GI值
- 常见水果GI值
- 常见蔬菜GI值
- 常见豆类GI值
- 常见奶制品GI值
- 常见肉类蛋类GI值
- 常见零食GI值
- 常见饮料GI值
- 优质脂肪来源
- 不良脂肪来源

### 1.6 餐食指导
- 早餐建议
- 午餐建议
- 晚餐建议

---

## 二、食物成分数据

### 2.1 数据来源
- **Open Food Facts** - 开源食物成分数据库（英文）

### 2.2 数据规模
- 总记录数：8,335条
- 覆盖类别：主食、肉蛋类、蔬菜、水果、豆制品、奶类、水产、油脂类

### 2.3 营养指标
| 指标 | 说明 |
|------|------|
| calorie | 热量（kcal/100g） |
| protein | 蛋白质（g/100g） |
| fat | 脂肪（g/100g） |
| carb | 碳水化合物（g/100g） |
| diet_fiber | 膳食纤维（g/100g） |
| gi_value | GI值 |
| calcium | 钙（mg/100g） |
| folic_acid | 叶酸（μg/100g） |
| dha | DHA（mg/100g） |

### 2.4 分类分布
| 分类 | 数量 |
|------|------|
"""
    
    category_counts = {
        "主食": 2981,
        "肉蛋类": 450,
        "蔬菜": 258,
        "水果": 3467,
        "豆制品": 100,
        "奶类": 1055,
        "水产": 15,
        "油脂类": 9,
    }
    
    for cat, cnt in category_counts.items():
        content += f"| {cat} | {cnt} |\n"
    
    content += """
---

## 三、PDF文档知识

### 3.1 导入统计

"""
    
    for result in import_results:
        content += f"### {result['name']}\n\n"
        content += f"- **类别**: {result['category']}\n"
        content += f"- **文本长度**: {result['chars']} 字符\n"
        content += f"- **知识片段**: {result['chunks']} 条\n\n"
    
    content += """
### 3.2 文档分类汇总

| 分类 | 文档数 | 知识片段数 |
|------|--------|-----------|
"""
    
    category_stats = {}
    for result in import_results:
        cat = result['category']
        if cat not in category_stats:
            category_stats[cat] = {'docs': 0, 'chunks': 0}
        category_stats[cat]['docs'] += 1
        category_stats[cat]['chunks'] += result['chunks']
    
    for cat, stats in category_stats.items():
        content += f"| {cat} | {stats['docs']} | {stats['chunks']} |\n"
    
    content += """
---

## 四、向量知识库总览

### 4.1 知识结构
```
健康知识库
├── 基础健康知识（30条）
│   ├── dietary_guideline（膳食指南）
│   ├── nutrition_standard（营养标准）
│   ├── health_standard（健康标准）
│   ├── crowd_specific（人群特定）
│   ├── food_knowledge（食物知识）
│   └── meal_guidance（餐食指导）
├── 食物成分数据（145条）
│   └── food_knowledge（食物知识）
└── PDF文档知识（动态）
    ├── dietary_guideline（膳食指南）
    ├── nutrition_standard（营养标准）
    ├── crowd_specific（人群特定）
    ├── food_knowledge（食物知识）
    └── health_standard（健康标准）
```

### 4.2 更新记录
- **最后更新**: 2026-07-23
- **总记录数**: 动态统计

---

## 五、知识库使用说明

### 5.1 检索方式
- 语义搜索：基于向量相似度匹配
- 人群过滤：支持按目标人群（糖尿病患者、孕妇、老年人等）过滤
- 分类过滤：支持按知识类别过滤

### 5.2 AI Agent应用
- QuestionAnswerAgent：基于知识库回答健康咨询
- NutritionAnalysisAgent：基于知识库进行营养分析
- FoodAuditAgent：基于知识库审核食材信息
- DietPlanAgent：基于知识库生成饮食计划

### 5.3 扩展建议
1. 定期更新食物成分数据
2. 持续导入新的营养规范文档
3. 根据用户反馈优化知识分类
4. 增加更多人群特定的饮食指南
"""
    
    with open(KB_DOC_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n知识库文档已生成: {KB_DOC_FILE}")


def main():
    print("=" * 60)
    print("批量导入PDF到向量知识库")
    print("=" * 60)
    
    pdf_files = glob.glob(os.path.join(PDF_DIR, '*.pdf'))
    pdf_files = [f for f in pdf_files if not f.startswith(os.path.join(PDF_DIR, 'health'))]
    
    print(f"\n发现 {len(pdf_files)} 个PDF文件")
    
    import_results = []
    
    for pdf_path in pdf_files:
        result = import_single_pdf(pdf_path)
        if result:
            import_results.append(result)
    
    print("\n" + "=" * 60)
    print(f"导入完成! 共处理 {len(import_results)} 个PDF文件")
    print("=" * 60)
    
    total_chunks = sum(r['chunks'] for r in import_results)
    print(f"\n总知识片段: {total_chunks} 条")
    
    generate_kb_doc(import_results)
    
    print(f"\n向量库总记录数: {retriever.count()}")


if __name__ == "__main__":
    main()