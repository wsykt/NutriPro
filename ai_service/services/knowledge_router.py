"""知识路由层 KnowledgeRouter（五库物理隔离后的统一检索入口）

职责：
1. 查询意图识别：关键词规则 → 目标物理集合组合
2. 域独立检索参数：各集合独立 top_k（权威指南多取、食物成分少取）
3. 多库并行检索：按意图映射同时检索多个集合，跨库合并
4. 库内多标签并行：人群 + 类别标签 $in 过滤
5. 集合级 ACL：不同 Agent 仅能访问授权集合（p8）

不依赖 LLM（纯规则），保证离线/低延迟场景可用。
"""

import re
from typing import Dict, List, Optional

from utils.log_config import get_logger
from vector.retriever import retriever

_logger = get_logger("knowledge_router")

# ============================================================
# 域独立检索参数（各集合独立 top_k）
# ============================================================
KB_TOP_K: Dict[str, int] = {
    "kb_guide": 5,       # 权威指南：多取几条精确答案
    "kb_food": 3,        # 食物成分：3 条足够
    "kb_crowd": 4,       # 人群建议
    "kb_literature": 4,  # 文献
    "kb_templates": 4,   # AI 模板
}

ALL_COLLECTIONS = list(KB_TOP_K.keys())

# ============================================================
# 查询意图 → 目标集合映射（多库并行）
# ============================================================
INTENT_COLLECTIONS: Dict[str, List[str]] = {
    # 指南/原则类查询：指南 + 人群 + 文献
    "guide": ["kb_guide", "kb_crowd", "kb_literature"],
    # 食物/营养类查询：食物库 + 文献
    "food": ["kb_food", "kb_literature"],
    # 人群定制类查询（如"糖尿病怎么吃"）：人群 + 指南 + 食物（多库并行）
    "crowd": ["kb_crowd", "kb_guide", "kb_food"],
    # 学术/文献类查询：文献 + 指南
    "literature": ["kb_literature", "kb_guide"],
    # 模板命中类（四功能标准化输出）：模板库为主
    "template": ["kb_templates", "kb_crowd"],
    # 默认全库
    "general": ["kb_guide", "kb_crowd", "kb_literature", "kb_food"],
}

# ============================================================
# 集合级 ACL（Agent → 授权集合），p8
# ============================================================
AGENT_ALLOWED_COLLECTIONS: Dict[str, List[str]] = {
    # 健康问答：全知识域（但模板不作为权威来源）
    "qa": ["kb_guide", "kb_crowd", "kb_literature", "kb_food"],
    # 一日饮食方案：模板 + 食物 + 人群
    "diet_plan": ["kb_templates", "kb_food", "kb_crowd", "kb_guide"],
    # 食材菜谱推荐：模板 + 食物 + 人群
    "food_recommend": ["kb_templates", "kb_food", "kb_crowd", "kb_guide"],
    # 个性化运动方案：人群 + 指南（运动医学类权威内容在指南/文献库）
    "exercise": ["kb_crowd", "kb_guide", "kb_literature"],
    # 科普文章生成：文献 + 指南 + 人群
    "article": ["kb_literature", "kb_guide", "kb_crowd"],
}

# ============================================================
# 人群关键词表（意图识别 + 库内标签过滤）
# ============================================================
CROWD_KEYWORDS: Dict[str, List[str]] = {
    "糖尿病患者": ["糖尿病", "血糖", "糖友", "高血糖", "降糖", "胰岛", "低血糖"],
    "孕妇": ["孕妇", "孕期", "怀孕", "妊娠", "孕中", "孕晚", "孕早期", "哺乳", "产妇", "叶酸", "胎儿"],
    "老年人": ["老人", "老年", "中老年", "长辈", "骨质疏松", "肌少症"],
    "青少年": ["青少年", "学生", "儿童", "少年", "初中", "高中", "成长期"],
    "健身人群": ["健身", "增肌", "减脂", "肌肉", "蛋白粉", "塑形", "力量训练", "有氧"],
    "高血压": ["高血压", "血压", "降压", "收缩压", "舒张压"],
    "心血管": ["心血管", "心脏", "冠心病", "血脂", "胆固醇", "动脉粥样", "甘油三酯"],
}

# ============================================================
# 意图关键词
# ============================================================
FOOD_INTENT_WORDS = [
    "食物", "食材", "吃", "食补", "热量", "卡路里", "蛋白质", "碳水", "脂肪", "膳食纤维",
    "GI", "钙", "铁", "叶酸", "DHA", "维生素", "含量", "营养素", "补铁", "补钙", "补蛋白",
    "水果", "蔬菜", "肉类", "主食", "奶", "豆",
]
GUIDE_INTENT_WORDS = [
    "指南", "准则", "原则", "标准", "建议", "核心推荐", "膳食宝塔", "营养标准", "餐次",
]
LITERATURE_INTENT_WORDS = [
    "研究", "文献", "论文", "临床", "试验", "Meta", "荟萃", "循证", "统计", "队列",
    "综述", "RCT", "随机对照", "系统评价", "PMID",
]
TEMPLATE_INTENT_WORDS = [
    "饮食方案", "一日三餐", "食谱", "菜谱", "运动方案", "训练计划", "一周", "健身计划",
]

# ============================================================
# 三级检索粒度识别（document / paragraph / fact）
# ============================================================
DOC_LEVEL_WORDS = {
    # 整篇/全文：指南全文、整篇文献、完整方案
    "document": ["全文", "整篇", "完整指南", "完整版", "整份", "全篇", "原文", "原文档", "整篇文章"],
    # 段落/片段：某一段落、具体条文
    "paragraph": ["段落", "某段", "片段", "条文", "条款", "小节", "章节"],
    # 事实/单条：某个数据、单条卡片、具体数值
    "fact": ["数据", "数值", "单条", "卡片", "具体含量", "某个事实", "条目"],
}


def detect_doc_level(query: str) -> Optional[str]:
    """识别查询期望的检索粒度（无显式词 → None 不限粒度）"""
    for level, words in DOC_LEVEL_WORDS.items():
        for w in words:
            if w in query:
                return level
    return None


def detect_crowd(query: str) -> Optional[str]:
    """识别查询中的人群标签（库内标签过滤用）"""
    for crowd, words in CROWD_KEYWORDS.items():
        for w in words:
            if w in query:
                return crowd
    return None


def detect_intent(query: str) -> str:
    """规则意图识别（按优先级：食物 > 人群 > 指南 > 文献 > 模板）"""
    # 人群定制优先（如"糖尿病怎么吃" → crowd 意图，多库并行人群+食物）
    crowd = detect_crowd(query)
    if crowd and any(w in query for w in FOOD_INTENT_WORDS):
        return "crowd"
    if crowd:
        return "crowd"
    if any(w in query for w in FOOD_INTENT_WORDS):
        return "food"
    if any(w in query for w in GUIDE_INTENT_WORDS):
        return "guide"
    if any(w in query for w in LITERATURE_INTENT_WORDS):
        return "literature"
    if any(w in query for w in TEMPLATE_INTENT_WORDS):
        return "template"
    return "general"


class KnowledgeRouter:
    """五库路由 + 并行检索调度"""

    def __init__(self):
        self.collections = ALL_COLLECTIONS
        self.top_k_config = KB_TOP_K
        self.intent_map = INTENT_COLLECTIONS
        self.acl = AGENT_ALLOWED_COLLECTIONS

    # ---------- 路由解析 ----------

    def route(self, query: str, agent: Optional[str] = None) -> Dict:
        """解析查询 → {intent, crowd, collections, top_k, doc_level}"""
        intent = detect_intent(query)
        crowd = detect_crowd(query)
        doc_level = detect_doc_level(query)
        base_cols = self.intent_map.get(intent, self.intent_map["general"])

        # ACL：Agent 授权集合 ∩ 意图集合（未指定 agent → 全量）
        if agent and agent in self.acl:
            allowed = set(self.acl[agent])
            collections = [c for c in base_cols if c in allowed]
            if not collections:
                collections = [c for c in self.acl[agent]]  # 兜底：Agent 全部授权集合
        else:
            collections = base_cols

        top_k = {c: self.top_k_config.get(c, 4) for c in collections}
        return {
            "intent": intent,
            "crowd": crowd,
            "collections": collections,
            "top_k": top_k,
            "doc_level": doc_level,
        }

    # ---------- 并行多库检索 ----------

    def parallel_retrieve(self, query: str, top_k: int = 5,
                          target_crowd: Optional[str] = None,
                          agent: Optional[str] = None,
                          use_hybrid: bool = True,
                          doc_level: Optional[str] = None) -> List[Dict]:
        """多库并行检索（核心入口）

        按意图路由到多个集合，每集合按域独立 top_k 检索后合并；
        支持库内多标签并行（人群 + 类别 $in 过滤）；
        支持三级检索粒度（document/paragraph/fact）。
        """
        route_info = self.route(query, agent=agent)
        collections = route_info["collections"]
        crowd = target_crowd or route_info["crowd"]
        level = doc_level or route_info["doc_level"]

        _logger.info(
            f"[路由] intent={route_info['intent']} crowd={crowd} "
            f"doc_level={level} collections={collections} top_k={route_info['top_k']}"
        )

        merged = []
        # 单库（或指定子集）按域 top_k 检索
        for col_name in collections:
            per_k = route_info["top_k"].get(col_name, 4)
            per_k = max(per_k, top_k // max(1, len(collections)))  # 保证总结果量 ≥ top_k
            try:
                if use_hybrid:
                    hits = retriever.hybrid_retrieve(
                        query, top_k=per_k, target_crowd=crowd,
                        collections=[col_name], doc_level=level,
                    )
                else:
                    hits = retriever.search(
                        query, top_k=per_k, target_crowd=crowd,
                        collections=[col_name], doc_level=level,
                    )
                for h in hits:
                    h["_collection"] = col_name
                merged.extend(hits)
            except Exception as e:
                _logger.warning(f"并行检索失败 [{col_name}]: {e}")

        # 跨库合并：先按相似度，再保各库代表性（避免单库垄断）
        merged.sort(key=lambda x: -x.get("similarity", 0))
        # 简单交叉合并：轮询各集合取最相关，保证多库都有结果
        final = self._round_robin_merge(merged, top_k)
        return final

    @staticmethod
    def _round_robin_merge(merged: List[Dict], top_k: int) -> List[Dict]:
        """轮询合并：按集合轮流取当前最相关结果，保证多库覆盖"""
        by_col: Dict[str, List[Dict]] = {}
        for h in merged:
            by_col.setdefault(h.get("_collection", ""), []).append(h)
        final = []
        used_ids = set()
        while len(final) < top_k and by_col:
            for col, items in list(by_col.items()):
                if len(final) >= top_k:
                    break
                if not items:
                    by_col.pop(col, None)
                    continue
                # 取该库当前最相关且未使用的结果
                candidate = None
                for it in items:
                    if id(it) not in used_ids:
                        candidate = it
                        break
                if candidate:
                    final.append(candidate)
                    used_ids.add(id(candidate))
        return final[:top_k]


# 全局单例
knowledge_router = KnowledgeRouter()
