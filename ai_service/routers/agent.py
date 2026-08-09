"""混合架构 Agent 端点与统计 API 路由

由原 main.py 拆分而来，对应以下业务域：
- Agent 统计（GET /api/v1/agent/stats）
- 资料搜集 Agent（POST /api/v1/agent/search-materials，含 _call_llm / _fetch_url_content_simple）
- 事实校验 Agent（POST /api/v1/agent/fact-check）
- Agent 统计导出（GET /api/v1/agent/stats/export）
"""

from datetime import datetime

from fastapi import APIRouter

# 全局编排器
from agent.orchestrator import orchestrator

# 异步任务服务：LLM 调用卸载到线程池
from services.async_task_service import run_in_thread

# 统一响应包装
from utils.response_utils import success_response, error_response

# 权威资料搜索（实现于 knowledge 路由模块，供资料搜集 Agent 复用）
from routers.knowledge import _web_search_authoritative

router = APIRouter()


# ============================================================
# Agent 统计接口
# ============================================================

@router.get("/api/v1/agent/stats")
async def agent_stats():
    return success_response(stats=orchestrator.get_stats())


# ============================================================
# 方案C：混合架构 Agent 端点（资料搜集 + 事实校验 + 混合编排）
# ============================================================

@router.post("/api/v1/agent/search-materials")
async def agent_search_materials(data: dict):
    """资料搜集Agent：基于主题 + 已有素材S1，联网搜索补充缺失的权威资料S2

    输入:
    {
        "topic": "糖尿病饮食原则",
        "existing_materials": "已有素材S1摘要文本...",
        "max_results": 3,
        "target_crowd": "糖尿病"
    }

    输出:
    {
        "success": true,
        "new_materials": [
            {"url": "...", "title": "...", "content": "原文片段...", "source": "..."},
            ...
        ],
        "search_keywords": ["2型糖尿病膳食原则", "糖尿病GI食物选择"],
        "message": "搜集到 3 份补充资料"
    }
    """
    topic = data.get("topic", "")
    existing = data.get("existing_materials", "")
    max_results = data.get("max_results", 3)
    target_crowd = data.get("target_crowd", "")

    if not topic:
        return error_response(
            message="topic 不能为空", code=400, detail="MISSING_TOPIC"
        )

    # 步骤1：用LLM分析S1缺失的内容角度，生成搜索关键词
    analysis_prompt = f"""你是一个营养学资料检索专家。

主题：{topic}
目标人群：{target_crowd}
已有素材摘要：
{existing[:1500] if existing else '暂无'}

请分析已有素材缺失了哪些重要角度，输出3个用于联网搜索的关键词。
要求：
1. 每个关键词聚焦一个具体角度（如：某人群膳食原则、某营养素需求、某食物GI值）
2. 不要重复已有素材覆盖的内容
3. 直接输出3个关键词，用换行分隔，不要编号不要解释"""

    try:
        analysis_response = await _call_llm(analysis_prompt)
        keywords = [k.strip() for k in analysis_response.strip().split("\n") if k.strip()][:3]
        if not keywords:
            keywords = [f"{topic} 膳食指南", f"{topic} 营养研究", f"{topic} 饮食禁忌"]
    except Exception:
        keywords = [f"{topic} 膳食指南", f"{topic} 营养研究", f"{topic} 饮食禁忌"]

    # 步骤2：对每个关键词执行权威搜索 + 抓取
    new_materials = []
    for kw in keywords:
        if len(new_materials) >= max_results:
            break
        search_results = _web_search_authoritative(kw, 2)
        for item in search_results:
            if len(new_materials) >= max_results:
                break
            url = item.get("url", "")
            if not url:
                continue
            # 抓取内容
            fetched = await _fetch_url_content_simple(url)
            if fetched and len(fetched["content"]) > 100:
                new_materials.append({
                    "url": url,
                    "title": item.get("title", fetched.get("title", kw)),
                    "content": fetched["content"][:2000],
                    "source": fetched.get("title", url),
                    "search_keyword": kw,
                })
            # 合规限速
            import time as _time
            import random as _rand
            _time.sleep(_rand.uniform(1.0, 2.0))

    return {
        "success": len(new_materials) > 0,
        "new_materials": new_materials,
        "search_keywords": keywords,
        "message": f"搜集到 {len(new_materials)} 份补充资料"
    }


@router.post("/api/v1/agent/fact-check")
async def agent_fact_check(data: dict):
    """独立事实校验Agent：核查母稿中所有引用是否有素材支撑，检测编造内容

    输入:
    {
        "draft": "科普母稿全文（含 [1][2] 等引用编号）...",
        "source_materials": "素材集合S全文（编号 [1] [2] ... 对应原始素材）..."
    }

    输出:
    {
        "passed": true/false,
        "score": 85,
        "defects": [
            {"type": "unsourced_claim", "description": "第3段关于维生素D的结论缺少素材支撑", "severity": "high"},
            {"type": "fabricated_data", "description": "文中'研究显示90%改善率'未在素材中找到", "severity": "high"},
            ...
        ],
        "summary": "校验通过/发现N处问题需修正"
    }
    """
    draft = data.get("draft", "")
    sources = data.get("source_materials", "")

    if not draft:
        return error_response(
            message="draft 不能为空", code=400, detail="MISSING_DRAFT"
        )

    check_prompt = f"""你是一个严格的事实校验编辑。请核查以下科普文章母稿，对照提供的参考素材，执行核验清单。

【参考素材集合】
{sources[:3000] if sources else '无素材'}

【待校验母稿】
{draft[:4000]}

【核验清单】请逐条检查并输出JSON：
1. unsourced_claim：文中所有引用编号 [x] 是否都能在素材中找到对应原文支撑？有无无素材支撑的论点？
2. fabricated_data：文中营养数值、研究结论是否和原始素材一致？有无编造的临床试验、不存在的参考文献？
3. absolute_language：是否存在绝对化违规用语（一定、根治、百分百、特效、彻底）？
4. source_mismatch：文中标注的素材编号和实际引用内容是否匹配？

请严格输出以下JSON格式（不要输出其他内容）：
{{
  "passed": true或false,
  "score": 0到100的整数,
  "defects": [
    {{"type": "问题类型", "description": "具体描述", "severity": "high/medium/low"}}
  ],
  "summary": "一句话总结"
}}

判定标准：
- 存在任何 high 级别缺陷 → passed=false
- score < 70 → passed=false
- 无缺陷且 score≥80 → passed=true"""

    try:
        response = await _call_llm(check_prompt)

        # 尝试解析JSON
        import json as _json
        import re as _re
        # 提取JSON块
        json_match = _re.search(r'\{[\s\S]*\}', response)
        if json_match:
            result = _json.loads(json_match.group())
            # 确保字段完整
            result.setdefault("passed", result.get("score", 0) >= 80)
            result.setdefault("score", 80)
            result.setdefault("defects", [])
            result.setdefault("summary", "校验完成")
            result["success"] = True
            return result
        else:
            # JSON解析失败，返回保守结果
            return {
                "success": True,
                "passed": False,
                "score": 60,
                "defects": [{"type": "parse_error", "description": "校验结果解析失败，需人工复核", "severity": "medium"}],
                "summary": "校验Agent返回格式异常，默认不通过，需人工复核"
            }
    except Exception as e:
        return {
            "success": False,
            "passed": False,
            "score": 0,
            "defects": [{"type": "agent_error", "description": str(e), "severity": "high"}],
            "summary": f"校验Agent执行失败: {str(e)}"
        }


async def _call_llm(prompt: str) -> str:
    """调用 LLM（复用 llm/router 双链路：本地 Ollama / 云端 DeepSeek）

    修复：原实现引用了不存在的 services.chat_service，导致 search-materials /
    fact-check 端点的 LLM 环节永远走默认分支。现改为复用 llm.router 统一入口。
    """
    from llm.router import llm as llm_router
    result = await run_in_thread(
        llm_router.chat,
        [{"role": "user", "content": prompt}],
    )
    return str(result)


async def _fetch_url_content_simple(url: str) -> dict:
    """简化版URL内容抓取（返回标题+正文）"""
    try:
        import requests as req
        from bs4 import BeautifulSoup

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = req.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.encoding = resp.apparent_encoding or "utf-8"

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        article = soup.find("article") or soup.find("main") or soup.find("body")
        text = article.get_text(separator="\n", strip=True) if article else ""
        title = soup.title.string.strip() if soup.title and soup.title.string else url

        if len(text) > 3000:
            text = text[:3000]
        if len(text) < 100:
            return None

        return {"title": title, "content": text}
    except Exception:
        return None


# ============================================================
# Agent 统计导出
# ============================================================

@router.get("/api/v1/agent/stats/export")
async def agent_stats_export():
    """导出 Agent 运行统计数据（JSON 格式，可直接用于绘图）"""
    stats = orchestrator.get_stats()
    full_stats = orchestrator.get_full_stats()

    return {
        "export_time": datetime.now().isoformat(),
        "summary": stats,
        "detailed_logs": full_stats,
    }
