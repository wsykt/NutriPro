"""科普文章生成 Agent

依赖统一服务层：知识库检索走 services/retrieval_service.py
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
免责声明走 services/disclaimer.py
"""

from agent.base import BaseAgent
from services.disclaimer import STANDARD_DISCLAIMER

ARTICLE_GENERATE_PROMPT = """你是健康科普文章生成Agent。

输入：文章主题、目标人群。

任务：生成一篇1000字左右的健康科普文章。

输出JSON：
{
  "title": "文章标题",
  "author": "AI健康助手",
  "publish_time": "2024-01-01",
  "article_type": "科普",
  "content": "文章正文（markdown格式）",
  "keywords": ["关键词1", "关键词2"],
  "summary": "文章摘要"
}

约束：内容要科学严谨，不提供疾病诊断，最后附带免责声明。

Few-Shot 示例：
输入：文章主题：糖尿病患者如何科学饮食，目标人群：糖尿病
输出：{"title":"糖尿病患者科学饮食指南","author":"AI健康助手","publish_time":"2024-01-01","article_type":"科普","content":"# 糖尿病患者科学饮食指南\n\n## 一、控制总热量，保持健康体重\n- 根据身高体重、活动量计算每日所需热量\n- 超重患者适当减少热量摄入\n\n## 二、选择低GI食物\n- 主食：燕麦、糙米、荞麦面代替白米饭\n- 蔬菜：多吃非淀粉类蔬菜（绿叶蔬菜、西兰花、黄瓜）\n- 水果：选择低糖水果（苹果、梨、柚子，每次一份不超过200g）\n\n## 三、合理安排餐次\n- 少食多餐，每日5-6餐\n- 每餐主食量不超过一个拳头大小\n- 定时定量，不暴饮暴食\n\n【温馨提示：本内容仅为膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。】","keywords":["糖尿病","饮食","GI值","血糖","健康饮食"],"summary":"本文为糖尿病患者提供科学的饮食指导意见，涵盖热量控制、GI值选择和餐次安排三方面，帮助患者通过饮食管理血糖。"}"""


class ArticleGenerateAgent(BaseAgent):

    @staticmethod
    def generate(topic: str, target_crowd: str = "") -> dict:
        kb_context = ArticleGenerateAgent.get_kb_context(f"{topic} {target_crowd}")

        prompt = ARTICLE_GENERATE_PROMPT + "\n\n"
        prompt += f"文章主题：{topic}\n"
        prompt += f"目标人群：{target_crowd}\n"
        prompt += kb_context

        messages = [
            {"role": "system", "content": "你是一个专业的健康科普文章撰写专家。只输出JSON。"},
            {"role": "user", "content": prompt},
        ]

        parsed = ArticleGenerateAgent.chat_json(messages)

        if not parsed or "title" not in parsed:
            raise ValueError("Invalid JSON response")

        if "content" in parsed:
            parsed["content"] = ArticleGenerateAgent.add_disclaimer(parsed["content"])

        parsed["target_crowd"] = target_crowd
        parsed.setdefault("author", "AI健康助手")
        parsed.setdefault("article_type", "科普")

        return parsed


agent = ArticleGenerateAgent()
