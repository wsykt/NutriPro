"""语音文本解析 Agent

将语音/OCR 口语化文本转换为结构化食物项。
降级走 local_fallback_engine.py（由 orchestrator 统一处理）
"""

from agent.base import BaseAgent
from constants.food_units import MEASURE_WORDS_MAP, FOOD_DEFAULT_WEIGHT

VOICE_TEXT_PARSE_PROMPT = """你是饮食语音文本解析Agent。
输入：浏览器语音识别得到的口语化饮食描述，存在倒装、简称、语序混乱。

规则：
一碗≈200g，一小碗≈120g，一份≈150g，一个≈按食物类型估算，一杯≈250ml；
口语名称标准化：瘦肉→猪瘦肉、青菜→小白菜/西兰花，尽量匹配标准食材名称。
仅提取饮食食材，无关内容全部丢弃。
如果原文使用了"一个""一杯"等量词，请在weight字段填入估算重量。

常见量词换算参考：
- 一个鸡蛋≈50g，一个苹果≈200g，一个馒头≈100g
- 一杯牛奶≈250g，一杯豆浆≈300g，一杯酸奶≈200g
- 一碗米饭≈200g，一碗粥≈300g，一碗面条≈200g
- 一份菜≈150g，一块肉≈100g，一根香蕉≈100g

输出JSON：
{
  "items": [
    {"food_name":"米饭","weight":200},
    {"food_name":"西兰花","weight":200}
  ]
}

Few-Shot 示例：
输入：我中午吃了两碗米饭，一份红烧肉
输出：{"items":[{"food_name":"米饭","weight":400},{"food_name":"红烧肉","weight":150}]}

输入：早上喝了一杯牛奶，吃了两个鸡蛋
输出：{"items":[{"food_name":"牛奶","weight":250},{"food_name":"鸡蛋","weight":100}]}"""

# 兼容旧名称（供外部引用）
QUANTITY_MAP = FOOD_DEFAULT_WEIGHT


class VoiceTextParseAgent(BaseAgent):

    @staticmethod
    def _fill_weight_by_quantity(text: str, items: list) -> list:
        """根据量词和食物名称填充重量，优先使用 MEASURE_WORDS_MAP 和 FOOD_DEFAULT_WEIGHT"""
        for item in items:
            if item.get("weight") is not None:
                continue

            food_name = item.get("food_name", "")
            matched = False

            # 1. 尝试匹配量词短语（如"一杯"、"一碗"）
            for measure, weight in MEASURE_WORDS_MAP.items():
                if measure in text and (food_name in text or any(k in text for k in FOOD_DEFAULT_WEIGHT.keys())):
                    item["weight"] = weight
                    matched = True
                    break

            # 2. 尝试匹配食物默认重量
            if not matched:
                for keyword, default_weight in FOOD_DEFAULT_WEIGHT.items():
                    if keyword in food_name:
                        item["weight"] = default_weight
                        matched = True
                        break

            # 3. 使用 UNIT_TO_GRAMS 单位换算兜底
            if not matched:
                from constants.food_units import UNIT_TO_GRAMS
                for unit, grams in UNIT_TO_GRAMS.items():
                    if unit in text:
                        item["weight"] = grams
                        matched = True
                        break

            # 4. 最终兜底：100g
            if not matched:
                item["weight"] = 100

        return items

    @staticmethod
    def parse(text: str) -> dict:
        messages = [
            {"role": "system", "content": "你是一个饮食语音文本解析专家。只输出JSON。"},
            {"role": "user", "content": VOICE_TEXT_PARSE_PROMPT + f"\n\n用户语音文本：{text}"},
        ]

        parsed = VoiceTextParseAgent.chat_json(messages)
        items = parsed.get("items", [])
        if not items:
            # LLM 未识别出食物项（网络/解析失败被 chat_json 吞掉）→ 抛异常交给
            # orchestrator 走本地兜底引擎，避免"空结果"被持久化缓存污染后续请求
            raise ValueError("语音解析未识别到食物项")
        items = VoiceTextParseAgent._fill_weight_by_quantity(text, items)

        return {"items": items}


agent = VoiceTextParseAgent()
