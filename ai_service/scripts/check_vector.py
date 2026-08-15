import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

print(f"向量库当前记录数: {retriever.count()}")

results = retriever.search("苹果", top_k=5)
print("\n搜索'苹果'结果:")
for i, r in enumerate(results):
    print(f"{i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}")

results = retriever.search("蛋白质高的食物", top_k=5)
print("\n搜索'蛋白质高的食物'结果:")
for i, r in enumerate(results):
    print(f"{i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}")