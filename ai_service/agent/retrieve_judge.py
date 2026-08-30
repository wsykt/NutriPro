from agent.base import BaseAgent
from llm.router import llm
from vector.retriever import retriever

RETRIEVE_JUDGE_PROMPT = """你是检索判定Agent。

输入：用户原始问题。

任务：
1. 判断是否需要调用向量知识库检索；
2. 提取检索关键词；
3. 如果是复杂多问题提问，拆分成多个检索关键词；
4. 判断知识库是否有相关资料（相似度阈值）。

输出JSON：
{
  "need_retrieve": true,
  "search_keywords": ["关键词1", "关键词2"],
  "is_complex": false,
  "has_knowledge": true
}

规则：
- 健康咨询、营养建议、膳食搭配、人群相关问题：need_retrieve=true
- 闲聊、问候、确认信息等：need_retrieve=false
- 长文本多问题提问：is_complex=true，拆分成多个关键词分别检索
- 检索相似度全部低于阈值0.6：has_knowledge=false

Few-Shot 示例：
输入：糖尿病患者早餐适合吃什么？
输出：{"need_retrieve":true,"search_keywords":["糖尿病","早餐","低GI"],"is_complex":false,"has_knowledge":true}

输入：你好，今天天气不错
输出：{"need_retrieve":false,"search_keywords":[],"is_complex":false,"has_knowledge":false}

输入：我最近在健身，想增肌，蛋白质应该怎么吃？还要不要控制碳水？脂肪该吃多少？
输出：{"need_retrieve":true,"search_keywords":["健身增肌","蛋白质","碳水","脂肪"],"is_complex":true,"has_knowledge":true}"""

QUESTION_SPLIT_PROMPT = """你是问题拆分专家。

输入：用户长文本多问题提问。

任务：将复杂问题拆分成多个独立的检索关键词。

规则：
1. 每个关键词不超过10个字符；
2. 保留核心健康相关词汇；
3. 去除语气词和无关内容；
4. 最少1个，最多5个关键词。

输出JSON：
{
  "keywords": ["关键词1", "关键词2", "关键词3"]
}"""

HEALTH_KEYWORDS = [
    "营养", "膳食", "饮食", "健康", "食谱", "热量", "蛋白质", "脂肪", "碳水",
    "减肥", "增肌", "减脂", "控糖", "糖尿病", "孕妇", "老年", "青少年", "健身",
    "早餐", "午餐", "晚餐", "加餐", "食材", "食物", "GI", "膳食纤维", "钙",
    "铁", "维生素", "BMI", "体重", "身高", "运动", "锻炼", "跑步", "瑜伽",
    "过敏", "禁忌", "推荐", "建议", "指南", "标准", "摄入量", "搭配", "均衡",
]


class RetrieveJudgeAgent(BaseAgent):

    @staticmethod
    def _is_health_related(query: str) -> bool:
        for keyword in HEALTH_KEYWORDS:
            if keyword in query:
                return True
        return False

    @staticmethod
    def _split_complex_question(query: str) -> list:
        if len(query) < 20:
            return [query]

        messages = [
            {"role": "system", "content": "你是一个问题拆分专家。只输出JSON。"},
            {"role": "user", "content": QUESTION_SPLIT_PROMPT + "\n\n用户问题：" + query[:200]},
        ]

        try:
            result = RetrieveJudgeAgent.chat(messages)
            parsed = llm.safe_parse_json(result)
            if parsed and "keywords" in parsed:
                return parsed["keywords"][:5]
        except Exception:
            pass

        keywords = []
        for kw in HEALTH_KEYWORDS:
            if kw in query and kw not in keywords:
                keywords.append(kw)
                if len(keywords) >= 5:
                    break
        
        if not keywords:
            keywords = [query[:10]]
        
        return keywords

    @staticmethod
    def _check_knowledge_exists(keywords: list, threshold: float = 0.6) -> bool:
        if not retriever or retriever.count() == 0:
            return False
        
        for keyword in keywords:
            try:
                results = retriever.search(keyword, top_k=1)
                if results and results[0].get("similarity", 0) >= threshold:
                    return True
            except Exception:
                continue
        
        return False

    @staticmethod
    def judge(query: str) -> dict:
        query = query.strip()
        
        if not query:
            return {"need_retrieve": False, "search_keywords": [], "is_complex": False, "has_knowledge": False}

        is_health = RetrieveJudgeAgent._is_health_related(query)
        
        if not is_health:
            return {"need_retrieve": False, "search_keywords": [query], "is_complex": False, "has_knowledge": False}

        keywords = RetrieveJudgeAgent._split_complex_question(query)
        is_complex = len(keywords) > 1
        has_knowledge = RetrieveJudgeAgent._check_knowledge_exists(keywords)

        try:
            messages = [
                {"role": "system", "content": "你是一个检索判定专家。只输出JSON。"},
                {"role": "user", "content": RETRIEVE_JUDGE_PROMPT + "\n\n用户问题：" + query[:200]},
            ]

            result = RetrieveJudgeAgent.chat(messages)
            parsed = llm.safe_parse_json(result)

            if not parsed or "need_retrieve" not in parsed:
                need_retrieve = is_health
            else:
                need_retrieve = parsed.get("need_retrieve", is_health)
        except Exception:
            need_retrieve = is_health

        if not need_retrieve:
            return {
                "need_retrieve": False,
                "search_keywords": keywords,
                "is_complex": is_complex,
                "has_knowledge": has_knowledge,
            }

        return {
            "need_retrieve": need_retrieve,
            "search_keywords": keywords,
            "is_complex": is_complex,
            "has_knowledge": has_knowledge,
        }

    @staticmethod
    def batch_retrieve(keywords: list, top_k: int = 3) -> list:
        all_results = []
        seen_contents = []
        
        for keyword in keywords:
            try:
                results = retriever.search(keyword, top_k=top_k)
                for r in results:
                    content = r.get("content", "")
                    if content and content not in seen_contents:
                        seen_contents.append(content)
                        all_results.append(r)
            except Exception:
                continue
        
        all_results = sorted(all_results, key=lambda x: x.get("similarity", 0), reverse=True)
        
        return all_results[:top_k * 2]


agent = RetrieveJudgeAgent()