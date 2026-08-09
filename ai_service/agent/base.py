"""Agent 基类 — 统一 LLM 调用 + 异常处理模式

所有 Agent 继承此类以消除重复的样板代码。
"""

from llm.router import llm
from services.disclaimer import STANDARD_DISCLAIMER
from services.retrieval_service import build_kb_context


class BaseAgent:
    """Agent 基类，提供统一的 LLM 调用和异常处理"""

    @staticmethod
    def chat_json(messages, max_retries: int = 2) -> dict:
        """统一 LLM JSON 调用

        所有 Agent 的 LLM 调用都走这里，确保重试次数一致。
        """
        return llm.chat_json(messages, max_retries=max_retries)

    @staticmethod
    def chat(messages) -> str:
        """统一 LLM 文本调用"""
        return llm.chat(messages)

    @staticmethod
    def get_kb_context(query: str, top_k: int = 3) -> str:
        """统一知识库检索"""
        return build_kb_context(query, top_k=top_k)

    @staticmethod
    def add_disclaimer(text: str) -> str:
        """统一添加免责声明（去重）"""
        if STANDARD_DISCLAIMER not in text:
            text += "\n\n" + STANDARD_DISCLAIMER
        return text.strip()
