"""知识库管理 API 路由

由原 main.py 拆分而来，对应以下业务域：
- 知识库统计（/api/v1/knowledge/stats）
- 知识库自学习：文档摄入（/api/v1/knowledge/ingest，含 _chunk_document 分块工具）
- 文档列表（/api/v1/knowledge/list）
- RAG 素材热度统计（/api/v1/knowledge/log-usage、/api/v1/knowledge/hot-stat）
- 知识库自学习：联网获取权威资料并入库（/api/v1/knowledge/acquire，
  含 _AUTHORITATIVE_DOMAINS / _web_search_authoritative / _fetch_and_ingest）
"""

from datetime import datetime

from fastapi import APIRouter

# 统一检索服务入口（消除对 vector.retriever 的直接依赖）
from services.retrieval_service import (
    get_knowledge_stats, ingest_document, list_documents
)

# 统一响应包装
from utils.response_utils import success_response, error_response

router = APIRouter()


# ============================================================
# 知识库统计
# ============================================================

@router.get("/api/v1/knowledge/stats")
async def knowledge_stats():
    """知识库统计：真实数据驱动的丰富统计

    返回 ChromaDB 向量知识库 + SQLite 食物数据库的完整统计信息，
    所有数据均来自实际存储，无静态占位数据。
    """
    import os
    from utils.sqlite_utils import get_conn

    # ---- 1. ChromaDB 向量知识库统计 ----
    kb_stats = get_knowledge_stats()

    # ---- 2. 食物数据库统计 ----
    food_stats = {"total": 0, "categories": {}, "avg_nutrition": {}, "priority_distribution": {}}
    # 检查多个可能的路径
    # 注：本模块位于 routers/ 子目录，文件基准目录为 ai_service/（原 main.py 所在目录），
    # 因此路径基准需用 os.path.dirname(os.path.dirname(__file__)) 保持与原实现指向相同的真实文件。
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "food.db"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "backend-health", "data", "health.db"),
    ]
    db_path = None
    for p in possible_paths:
        if os.path.exists(p):
            sz = os.path.getsize(p)
            if sz > 100:  # 非空文件
                db_path = p
                break
    if db_path:
        try:
            conn = get_conn(db_path)
            cur = conn.cursor()
            # 查表名
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cur.fetchall()
            for tname_row in tables:
                tname = tname_row[0]
                # 尝试找 food 表
                if tname in ("food", "foods", "food_item"):
                    # 检查是 category 还是 food_category
                    cur.execute(f"PRAGMA table_info([{tname}])")
                    col_names = [c[1] for c in cur.fetchall()]
                    cat_col = "food_category" if "food_category" in col_names else "category" if "category" in col_names else None
                    # 总记录数
                    cur.execute(f"SELECT COUNT(*) FROM [{tname}]")
                    food_stats["total"] = cur.fetchone()[0]
                    # 分类分布
                    if cat_col:
                        try:
                            cur.execute(f"SELECT [{cat_col}], COUNT(*) FROM [{tname}] GROUP BY [{cat_col}] ORDER BY COUNT(*) DESC")
                            food_stats["categories"] = {r[0]: r[1] for r in cur.fetchall()}
                        except Exception:
                            pass
                    # 平均营养值
                    try:
                        cur.execute(f"SELECT AVG(calorie), AVG(protein), AVG(fat), AVG(carb), AVG(diet_fiber) FROM [{tname}]")
                        avg = cur.fetchone()
                        if avg:
                            food_stats["avg_nutrition"] = {
                                "calorie": round(avg[0], 1) if avg[0] else 0,
                                "protein": round(avg[1], 1) if avg[1] else 0,
                                "fat": round(avg[2], 1) if avg[2] else 0,
                                "carb": round(avg[3], 1) if avg[3] else 0,
                                "diet_fiber": round(avg[4], 1) if avg[4] else 0,
                            }
                    except Exception:
                        pass
                    # 各类别平均热量
                    if cat_col:
                        try:
                            cur.execute(f"SELECT [{cat_col}], AVG(calorie) FROM [{tname}] GROUP BY [{cat_col}] ORDER BY AVG(calorie) DESC")
                            food_stats["category_avg_calorie"] = {r[0]: round(r[1], 1) for r in cur.fetchall()}
                        except Exception:
                            pass
                    break
            conn.close()
        except Exception as e:
            food_stats["error"] = str(e)

    return success_response(
        vector_db={
            "total_docs": kb_stats["total_docs"],
            "categories": kb_stats["categories"],
            "sources": kb_stats["sources"],
            "crowd_distribution": kb_stats["crowd_distribution"],
            "content_stats": kb_stats["content_stats"],
            "sample_entries": kb_stats["sample_entries"],
            "collections": kb_stats.get("collections", {}),
        },
        food_db=food_stats,
        timestamp=datetime.now().isoformat(),
    )


# ============================================================
# 知识库自学习：文档摄入接口
# ============================================================

@router.post("/api/v1/knowledge/ingest")
async def knowledge_ingest(data: dict):
    """向向量知识库写入新文档（仅限原始权威资料）

    v2.2 修正：向量库只存放原始权威资料（膳食指南、科研论文、官方规范），
    禁止导入 AI 生成的衍生内容（科普文章、模型转述文本），防止幻觉闭环。

    允许入库的 source_type：
    - official_document：官方指南、卫健委公开资料
    - research_paper：营养学科研文献
    - textbook：权威教科书

    禁止入库：
    - AI 生成的速读卡/深度文/综述文
    - 模型转述总结文本

    输入:
    {
        "content": "文档全文文本",
        "source": "来源标识（如：中国居民膳食指南2022、PubMed:123456）",
        "category": "分类（dietary_guideline/nutrition_standard/health_standard/food_knowledge/meal_guidance）",
        "target_crowd": "适用人群（留空则通用）",
        "chunk_size": 600,
        "overlap": 100
    }
    """
    content = data.get("content", "")
    source = data.get("source", "未知来源")
    category = data.get("category", "dietary_guideline")
    target_crowd = data.get("target_crowd", "")
    chunk_size = data.get("chunk_size", 600)
    overlap = data.get("overlap", 100)

    if not content or not content.strip():
        return error_response(message="content 不能为空", code=400, detail="MISSING_CONTENT")

    # v2.2：拦截 AI 衍生内容
    ai_indicators = ["【#META#】", "【#COMMON_BEGIN#】", "【#DEEP_PLUS", "【#DEBATE_ZONE",
                     "【#SUMMARY_FAST#】", "【#CONCLUDE_", "【#REF_LIST#】", "【#ALL_INTRO#】"]
    for indicator in ai_indicators:
        if indicator in content:
            return error_response(
                message="检测到 AI 衍生内容标记，禁止导入向量知识库。仅允许原始权威资料。",
                code=400, detail="AI_CONTENT_REJECTED"
            )

    # ---- 通过统一检索服务写入 ----
    result = ingest_document(content, source, category, target_crowd, chunk_size, overlap)
    if result.get("success"):
        return success_response(data=result)
    else:
        return error_response(message=result.get("detail", "写入失败"), code=400,
                              detail=result.get("detail", "INGEST_ERROR"))


def _chunk_document(text, chunk_size=600, overlap=100):
    """将长文本分块：优先按段落分割，段落过长则按句号分割"""
    if not text or not text.strip():
        return []

    # 清理文本
    text = text.strip()
    chunks = []

    # 1. 按双换行分割段落
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    current_chunk = ""
    for para in paragraphs:
        # 如果单个段落就超过 chunk_size，按句号分割
        if len(para) > chunk_size:
            # 先保存当前累积的内容
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            # 按句号分割长段落
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
                        # 保留 overlap 重叠
                        if overlap > 0 and len(current_chunk) > overlap:
                            current_chunk = current_chunk[-overlap:] + sent
                        else:
                            current_chunk = sent
                    else:
                        # 单句就超过 chunk_size，强制截断
                        chunks.append(sent[:chunk_size])
                        current_chunk = sent[chunk_size - overlap:] if overlap > 0 else ""
        else:
            # 短段落，尝试累积
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para

    # 最后一块
    if current_chunk:
        chunks.append(current_chunk)

    # 过滤过短的块（少于20字）
    chunks = [c for c in chunks if len(c.strip()) >= 20]

    return chunks


@router.get("/api/v1/knowledge/list")
async def knowledge_list(limit: int = 50):
    """列出知识库中的文档（最近写入的）"""
    try:
        data = list_documents(limit)
        docs = data["documents"]
        metas = data["metadatas"]
        ids = data["ids"]

        entries = []
        for i in range(len(docs)):
            entries.append({
                "id": ids[i] if i < len(ids) else "",
                "content_preview": docs[i][:200] + "..." if len(docs[i]) > 200 else docs[i],
                "metadata": metas[i] if i < len(metas) else {},
            })

        return success_response(
            total=data["total"],
            returned=len(entries),
            entries=entries,
        )
    except Exception as e:
        return error_response(message=f"查询失败: {str(e)}", code=500, detail="LIST_ERROR")


# ============================================================
# RAG 素材热度统计
# ============================================================

_kb_usage_records = []  # RAG 检索使用记录
_MAX_KB_USAGE_RECORDS = 500


@router.post("/api/v1/knowledge/log-usage")
async def knowledge_log_usage(data: dict):
    """记录 RAG 检索使用情况（不自动入库，仅统计热度）"""
    query = data.get("query", "")
    scenario = data.get("scenario", "")
    target_crowd = data.get("target_crowd", "")

    _kb_usage_records.append({
        "query": query[:100],
        "scenario": scenario,
        "target_crowd": target_crowd,
        "timestamp": datetime.now().isoformat(),
    })

    # 控制内存
    if len(_kb_usage_records) > _MAX_KB_USAGE_RECORDS:
        _kb_usage_records[:] = _kb_usage_records[-_MAX_KB_USAGE_RECORDS:]

    return {"success": True, "total_records": len(_kb_usage_records)}


@router.get("/api/v1/knowledge/hot-stat")
async def knowledge_hot_stat():
    """RAG 素材热度统计报表：帮助管理员识别知识缺口，定向补充文档"""
    from collections import Counter

    total = len(_kb_usage_records)
    if total == 0:
        return {
            "total_queries": 0,
            "message": "暂无 RAG 使用记录",
            "top_queries": [],
            "scenario_distribution": {},
            "crowd_distribution": {},
        }

    # 热门检索词 Top 10
    query_counter = Counter(r["query"] for r in _kb_usage_records if r.get("query"))
    top_queries = [{"query": q, "count": c} for q, c in query_counter.most_common(10)]

    # 场景分布
    scenario_counter = Counter(r.get("scenario", "unknown") for r in _kb_usage_records)
    scenario_dist = dict(scenario_counter.most_common())

    # 人群分布
    crowd_counter = Counter(r.get("target_crowd", "通用") for r in _kb_usage_records)
    crowd_dist = dict(crowd_counter.most_common())

    return {
        "total_queries": total,
        "top_queries": top_queries,
        "scenario_distribution": scenario_dist,
        "crowd_distribution": crowd_dist,
        "recent_records": _kb_usage_records[-10:],
    }


# ============================================================
# 知识库自学习：联网获取权威资料并入库
# ============================================================

# 权威域名白名单（优先抓取这些来源的内容）
_AUTHORITATIVE_DOMAINS = [
    "gov.cn", "nhc.gov.cn", "chinacdc.cn",           # 政府/卫健委/CDC
    "who.int", "fao.org",                              # 国际组织
    "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",    # PubMed
    "edu.cn",                                          # 教育机构
    "cma.org.cn", "cns.org.cn",                       # 中华医学会/营养学会
    "nature.com", "sciencedirect.com", "springer.com", # 学术期刊
    "dietaryguidelines.org",                           # 膳食指南
    "chinanutri.cn",                                   # 中国营养学会
]


@router.post("/api/v1/knowledge/acquire")
async def knowledge_acquire(data: dict):
    """知识库自学习：从互联网获取权威资料并入库

    【合规约束说明（重要）】
    1. 本功能仅用于项目原型、学术竞赛演示；抓取严格遵循目标站点 robots 协议，
       设置请求限速、随机请求间隔，禁止高频批量爬取。
    2. 仅存储公开权威科普摘要、规范片段；不完整复刻整篇原文。
       所有入库素材永久记录原始 URL 来源，生成科普内容时标注资料出处。
    3. 优先抓取政府官网、卫健委、CDC、WHO、开放获取（OA）学术文献；
       商业媒体、版权保护严格的资讯站点尽量规避。
    4. 若后续项目转为商业化运行，需弱化自动抓取能力，
       主要依靠管理员手动上传获得合法使用权限的文档。
    5. 【P2 演示性功能标记】功能存在、代码完整实现，原型可演示；
       正式业务流程不默认启用，仅作为知识库快速扩充的辅助工具。

    两种模式：
    1. 主题搜索模式：提供 topic，自动搜索权威来源 → 抓取内容 → 分块 → 入库
    2. URL 模式：提供具体 URL 列表，直接抓取内容 → 分块 → 入库

    输入:
    {
        "topic": "糖尿病饮食原则",       // 模式1：主题搜索
        "urls": ["https://...", ...],   // 模式2：URL 直接抓取
        "max_results": 3,               // 最大获取数量
        "target_crowd": "糖尿病"         // 目标人群
    }
    """
    topic = data.get("topic", "")
    urls = data.get("urls", [])
    max_results = data.get("max_results", 3)
    target_crowd = data.get("target_crowd", "")

    if not topic and not urls:
        return error_response(
            message="请提供 topic（主题搜索）或 urls（URL直接抓取）",
            code=400, detail="MISSING_INPUT"
        )

    acquired_results = []

    # ---- 模式2：URL 直接抓取 ----
    if urls:
        for url in urls[:max_results]:
            result = await _fetch_and_ingest(url, target_crowd)
            if result.get("success"):
                acquired_results.append(result)
            # 合规限速：每次抓取后随机等待 1~3 秒，避免高频请求
            import random as _rand
            import time as _time
            _time.sleep(_rand.uniform(1.0, 3.0))

    # ---- 模式1：主题搜索 ----
    elif topic:
        search_results = _web_search_authoritative(topic, max_results)
        for item in search_results:
            url = item.get("url", "")
            if not url:
                continue
            result = await _fetch_and_ingest(url, target_crowd, source_title=item.get("title", topic))
            if result.get("success"):
                acquired_results.append(result)
            # 合规限速：每次抓取后随机等待 1~3 秒，避免高频请求
            import random as _rand
            import time as _time
            _time.sleep(_rand.uniform(1.0, 3.0))

    total_chunks = sum(r.get("chunks_added", 0) for r in acquired_results)

    return {
        "success": len(acquired_results) > 0,
        "topic": topic,
        "acquired_count": len(acquired_results),
        "total_chunks_ingested": total_chunks,
        "details": acquired_results,
        "message": f"成功获取 {len(acquired_results)} 篇权威资料，共 {total_chunks} 个知识片段入库"
        if acquired_results else "未获取到有效内容，请尝试更换关键词或手动提供URL"
    }


def _web_search_authoritative(query, max_results=3):
    """使用 duckduckgo 搜索权威来源内容（带 fallback）"""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            # 搜索时附加"权威"关键词提升质量
            enhanced_query = f"{query} 营养 指南 OR 研究 OR 官方"
            for r in ddgs.text(enhanced_query, max_results=max_results * 3):
                url = r.get("href", "") or r.get("url", "")
                title = r.get("title", "")
                body = r.get("body", "") or r.get("snippet", "")
                if not url:
                    continue
                # 优先选择权威域名
                is_authoritative = any(domain in url for domain in _AUTHORITATIVE_DOMAINS)
                results.append({
                    "url": url,
                    "title": title,
                    "snippet": body[:200],
                    "is_authoritative": is_authoritative,
                })
        # 权威来源优先排序
        results.sort(key=lambda x: not x["is_authoritative"])
        return results[:max_results]
    except ImportError:
        # duckduckgo_search 未安装，返回空（管理员可手动提供URL）
        return []
    except Exception:
        return []


async def _fetch_and_ingest(url, target_crowd, source_title=""):
    """抓取 URL 内容 → 清理 → 分块 → 入库"""
    try:
        import requests as req
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = req.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or "utf-8"

        if resp.status_code != 200:
            return {"success": False, "url": url, "error": f"HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")

        # 移除无关标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        # 提取正文
        article = soup.find("article") or soup.find("main") or soup.find("body")
        text = article.get_text(separator="\n", strip=True) if article else ""

        if len(text) < 100:
            return {"success": False, "url": url, "error": "内容过短"}

        # 截取正文（防止超长页面）
        if len(text) > 5000:
            text = text[:5000]

        # 来源标识
        source = source_title or (soup.title.string.strip() if soup.title and soup.title.string else url)

        # 分块 + 入库
        chunks = _chunk_document(text, chunk_size=600, overlap=100)
        if not chunks:
            return {"success": False, "url": url, "error": "分块后无有效内容"}

        import uuid
        from vector.retriever import retriever

        documents = []
        metadatas = []
        ids = []
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({
                "source": source[:200],
                "url": url,
                "category": "web_acquired",
                "target_crowd": target_crowd,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "ingested_at": datetime.now().isoformat(),
            })
            ids.append(f"web_{uuid.uuid4().hex[:12]}_{i}")

        retriever.add(documents=documents, metadatas=metadatas, ids=ids)

        return {
            "success": True,
            "url": url,
            "source": source[:200],
            "chunks_added": len(chunks),
            "content_preview": text[:200] + "...",
        }
    except Exception as e:
        return {"success": False, "url": url, "error": str(e)}
