import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever

print(f"当前向量库记录数: {retriever.count()}")

retriever.clear()
print("向量库已清空")

retriever.ensure_initial_data()
print(f"已重新初始化基础知识库，记录数: {retriever.count()}")