"""统一知识库检索服务

消除 7 个 Agent 中重复的检索代码。
所有 Agent 通过此服务获取知识库上下文，不再重复写检索逻辑。
API 端点也通过此服务统一访问向量知识库，不直接依赖 vector.retriever。
"""

import uuid
from datetime import datetime as dt
from typing import Any, Dict, List, Optional, Tuple
from vector.retriever import retriever
from services.knowledge_router import knowledge_router


# ============================================================
# 文档分块工具（内部使用）
# ============================================================

def _chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> List[str]:
    """将长文本分块：优先按段落分割，段落过长则按句号分割"""
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks = []

    # 1. 按双换行分割段落
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""
    for para in paragraphs:
        if len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            sentences = para.replace("。", "。\n").replace("！", "！\n").replace("？", "？\n").split("\n")
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                if len(current_chunk) + len(sent) <= chunk_size:
                    current_chunk += sent
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        if overlap > 0 and len(current_chunk) > overlap:
                            current_chunk = current_chunk[-overlap:] + sent
                        else:
                            current_chunk = sent
                    else:
                        chunks.append(sent[:chunk_size])
                        current_chunk = sent[chunk_size - overlap:] if overlap > 0 else ""
        else:
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    chunks = [c for c in chunks if len(c.strip()) >= 20]
    return chunks


# ============================================================
# Agent 使用的上下文构建（已有）
# ============================================================

def build_kb_context(query: str, top_k: int = 3) -> str:
    """构建知识库上下文字符串

    参数:
        query: 检索查询
        top_k: 返回条数

    返回:
        格式化的知识库上下文文本，无结果时返回空字符串
    """
    if retriever.count() == 0:
        return ""

    results = retriever.search(query, top_k=top_k)
    if not results:
        return ""

    context = "\n---知识库参考---\n"
    for r in results:
        context += f"- {r['content']}\n"
    return context


def hybrid_kb_context(query: str, top_k: int = 5, target_crowd: str = "",
                      agent: str = "qa") -> Tuple[str, List[dict]]:
    """混合检索构建知识库上下文（含 judge 判定，接入 KnowledgeRouter 多库并行）

    用于 orchestrator.chat() 的完整检索流程。

    返回:
        (context_str, raw_results)
    """
    if retriever.count() == 0:
        return "", []

    try:
        from agent.retrieve_judge import agent as judge
        judge_result = judge.judge(query)

        if not judge_result.get("need_retrieve"):
            return "", []

        # 多库并行检索：按意图路由到多集合，ACL 限制 agent 可访问集合
        results = knowledge_router.parallel_retrieve(
            query, top_k=top_k,
            target_crowd=target_crowd if judge_result.get("need_retrieve") else None,
            agent=agent,
        )

        if results:
            context = "\n---知识库参考---\n"
            for r in results:
                source = r.get("metadata", {}).get("source", "")
                tag = " [权威]" if r.get("is_authority") else ""
                context += f"- {r['content']}{tag}\n"
            return context, results
    except Exception:
        pass

    return "", []


# ============================================================
# API 端点统一入口（消除 main.py 对 vector.retriever 的直接依赖）
# ============================================================

def retrieve_knowledge(query: str, persona: str = "", top_k: int = 5,
                       doc_level: str = "") -> List[dict]:
    """混合检索知识（BM25 + 向量双路融合，多库并行路由）

    参数:
        query: 检索查询
        persona: 目标人群（如"糖尿病患者"、"孕妇"等）
        top_k: 返回条数
        doc_level: 三级检索粒度（document/paragraph/fact，空则不限制）

    返回:
        检索结果列表，知识库为空时返回空列表
    """
    if retriever.count() == 0:
        return []
    # API 端统一走 KnowledgeRouter：意图路由 + 多库并行 + 默认 qa ACL
    return knowledge_router.parallel_retrieve(
        query, top_k=top_k, target_crowd=persona or None,
        agent="qa", doc_level=doc_level or None,
    )


def get_knowledge_stats() -> dict:
    """获取知识库丰富统计数据

    返回包含分类分布、来源分布、人群分布、内容统计等完整信息的字典。
    """
    return retriever.get_rich_stats()


def ingest_document(
    content: str,
    source: str = "未知来源",
    category: str = "dietary_guideline",
    target_crowd: str = "",
    chunk_size: int = 600,
    overlap: int = 100,
) -> dict:
    """摄入文档到向量知识库（含自动分块）

    参数:
        content: 文档全文文本
        source: 来源标识
        category: 分类
        target_crowd: 适用人群
        chunk_size: 分块大小
        overlap: 分块重叠

    返回:
        {"success": True/False, "chunks_added": int, ...}
    """
    if not content or not content.strip():
        return {"success": False, "detail": "content 不能为空"}

    chunks = _chunk_text(content, chunk_size, overlap)
    if not chunks:
        return {"success": False, "detail": "分块后无有效内容"}

    documents = []
    metadatas = []
    ids = []
    for i, chunk in enumerate(chunks):
        documents.append(chunk)
        metadatas.append({
            "source": source,
            "category": category,
            "target_crowd": target_crowd,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "ingested_at": dt.now().isoformat(),
        })
        ids.append(f"{source}_{i}_{uuid.uuid4().hex[:8]}")

    try:
        retriever.add(documents=documents, metadatas=metadatas, ids=ids)
        return {
            "success": True,
            "chunks_added": len(chunks),
            "source": source,
            "category": category,
            "target_crowd": target_crowd,
            "message": f"成功写入 {len(chunks)} 个知识片段",
        }
    except Exception as e:
        return {"success": False, "detail": f"写入失败: {str(e)}"}


def list_documents(limit: int = 50) -> Dict[str, Any]:
    """列出知识库中的文档（跨五库聚合，最近写入优先）

    参数:
        limit: 最大返回条数

    返回:
        {"total": int, "documents": [...], "metadatas": [...], "ids": [...]}
    """
    total = retriever.count()

    # 跨五库聚合：每个集合取 limit 条（Chroma 按内部序返回），合并后按 limit 截断
    documents, metadatas, ids = [], [], []
    for col_def in retriever.COLLECTION_DEFS:
        col_name = col_def["name"]
        col = retriever.collections[col_name]
        if col.count() == 0:
            continue
        try:
            data = col.get(
                limit=limit,
                include=["documents", "metadatas"]
            )
            documents.extend(data.get("documents", []) or [])
            metadatas.extend(data.get("metadatas", []) or [])
            ids.extend(data.get("ids", []) or [])
        except Exception:
            continue

    return {
        "total": total,
        "documents": documents[:limit],
        "metadatas": metadatas[:limit],
        "ids": ids[:limit],
    }
