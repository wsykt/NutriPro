import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

test_queries = [
    "苹果的热量是多少？",
    "鸡蛋的蛋白质含量是多少？",
    "哪些食物适合糖尿病患者？",
    "什么水果适合减肥？",
    "牛肉和鸡肉哪个蛋白质更高？",
    "牛奶的营养成分有哪些？",
    "西兰花有什么营养价值？",
    "全麦面包和白面包哪个更健康？",
    "孕妇应该多吃什么食物？",
    "老年人适合吃什么？",
    "蔬菜的热量",
    "肉类的蛋白质",
    "水果的GI值",
    "主食的碳水化合物",
    "酸奶的营养",
]

print(f"向量库记录总数: {retriever.count()}")
print("=" * 80)

for query in test_queries:
    print(f"\n查询: {query}")
    print("-" * 40)
    
    results = retriever.search(query, top_k=3)
    
    for i, r in enumerate(results):
        similarity = r.get("similarity", 0)
        content = r.get("content", "")
        metadata = r.get("metadata", {})
        print(f"{i+1}. 相似度: {similarity:.4f}, 类别: {metadata.get('food_category', '')}")
        print(f"   内容: {content}")