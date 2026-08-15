import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.question_answer import QuestionAnswerAgent

questions = [
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
]

qa_agent = QuestionAnswerAgent()

for i, question in enumerate(questions):
    print(f"\n{'='*60}")
    print(f"问题 {i+1}: {question}")
    print("-" * 60)
    
    answer = qa_agent.answer(question)
    print(f"回答: {answer}")