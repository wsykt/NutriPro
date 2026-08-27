"""聊天与营养分析类 API 路由

由原 main.py 拆分而来，对应以下业务域：
- 聊天交互（/api/v1/chat）
- SSE 流式对话（/api/v1/chat/stream，含 _sse_event / _chunk_sse_text 辅助函数）
- NLU 饮食描述解析（/api/v1/meal/parse）
- 知识库检索（/api/v1/retrieve）
- Agent 调用路由（nutrition/analyze、food/audit、voice/parse、weekly-summary、
  article/generate、diet/plan、reflection、health/reflection）
- 食材菜谱推荐（/api/v1/food/recommend）
- 运动建议（/api/v1/exercise/advice）
"""

import asyncio
import json
import re
import time

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from utils.log_config import get_logger

# 全局编排器
from agent.orchestrator import orchestrator

# 统一检索服务入口（消除对 vector.retriever 的直接依赖）
from services.retrieval_service import retrieve_knowledge

# 统一响应包装
from utils.response_utils import success_response, error_response

# 异步任务服务：长任务线程池卸载
from services.async_task_service import run_in_thread

# 配置与 LLM 单例（透传通道使用）
from config.settings import settings
from llm.router import llm

router = APIRouter()


# ============================================================
# 聊天交互
# ============================================================

@router.post("/api/v1/chat")
async def chat(data: dict):
    message = data.get("message", "")
    user_id = data.get("user_id", 0)
    conversation_id = data.get("conversation_id", "")
    health_snapshot = data.get("health_snapshot", {})
    # 新增：高性能模式开关（true=直接云端C方案，演示用速度快）
    high_performance = bool(data.get("high_performance", False))

    if not message:
        return error_response(message="缺少 message 参数", code=400, detail="MISSING_MESSAGE")

    # 透传通道：文章母稿等带标记的完整 prompt 直接交 LLM，不经健康咨询管线
    # （qa 管线会用 CLOUD_PROMPTS 重新包装 message，导致标记格式丢失）
    if data.get("_raw_prompt", False):
        _lp = get_logger("raw_prompt")
        _lp.info(f"[透传] prompt_full={message!r}")
        messages = [
            {"role": "system", "content": "你是营养学科普写作专家，严格按用户要求输出文章母稿。必须完整保留并遵循用户给出的全部【#标记#】与格式要求，直接输出正文，不要添加额外说明。"},
            {"role": "user", "content": message},
        ]
        try:
            text = await run_in_thread(
                llm.chat, messages, max_retries=1,
                timeout=settings.LLM_TIMEOUT_HIGH_PERF,
                temperature=0.5,
            )
        except Exception as e:
            return error_response(message=f"LLM 调用失败: {e}", code=502, detail="RAW_PROMPT_LLM_ERROR")
        # 临时诊断：打印母稿标记完整性
        _logger = get_logger("raw_prompt")
        _missing = [t for t in ("META", "ALL_INTRO", "SUMMARY_FAST", "SUMMARY_DEEP", "SUMMARY_ALL",
                                "COMMON_BEGIN", "COMMON_END", "DEEP_PLUS_BEGIN", "DEEP_PLUS_END",
                                "DEBATE_ZONE_BEGIN", "DEBATE_ZONE_END", "CONCLUDE_FAST",
                                "CONCLUDE_DEEP", "CONCLUDE_ALL") if ("【#%s#】" % t) not in text]
        _logger.info(f"[透传母稿] len={len(text)} missing={_missing} head={text[:120]!r}")
        return success_response(data={
            "response": text,
            "provider": "raw",
            "mode": "raw",
            "route": "raw_prompt",
            "high_performance": False,
        })

    result = await run_in_thread(
        orchestrator.chat,
        user_id=user_id,
        message=message,
        health_snapshot=health_snapshot,
        conversation_id=conversation_id,
        force_fallback=data.get("_force_fallback", False),
        high_performance=high_performance,
    )
    return success_response(data=result)


# ============================================================
# SSE 流式对话（阶段一·举措8）
# ============================================================

def _sse_event(event_type: str, payload: dict) -> str:
    """构造单条 SSE 事件（event: 类型 + data: JSON + 空行）

    标准 SSE 格式，前端可通过事件名区分 thinking / delta / done / error。
    """
    data_str = json.dumps(payload, ensure_ascii=False)
    return f"event: {event_type}\ndata: {data_str}\n\n"


def _chunk_sse_text(text: str, max_chunk: int = 30) -> list:
    """将回答文本切分为 SSE 分块（优先按句子边界，兼顾打字机节奏）"""
    if not text:
        return []
    # 按句号/感叹号/问号/换行切分（保留标点）
    parts = re.split(r"(?<=[。！？!?\n])", text)
    chunks = []
    buf = ""
    for p in parts:
        if not p:
            continue
        buf += p
        if len(buf) >= max_chunk or p.endswith("\n"):
            chunks.append(buf)
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks or [text]


_STREAM_SENTINEL = object()


async def _iter_sync_stream(gen):
    """把同步生成器逐项桥接到事件循环（线程池执行 next，避免阻塞）

    LLM 流式生成器每次 next() 会阻塞等待网络分块返回；
    放到线程池执行可保证事件循环持续响应其他请求。

    注意：不能依赖 `except StopIteration` 捕获生成器耗尽——Python 3.7+
    会把线程内（to_thread）抛出的 StopIteration 包装成 RuntimeError，
    因此改用 `next(gen, _STREAM_SENTINEL)` 哨兵默认值来识别流结束。
    """
    while True:
        item = await asyncio.to_thread(next, gen, _STREAM_SENTINEL)
        if item is _STREAM_SENTINEL:
            break
        yield item


@router.post("/api/v1/chat/stream")
async def chat_stream(data: dict):
    """SSE 流式对话（打字机效果）

    事件序列：
    - thinking: 立即反馈（"正在检索知识库并生成回答..."），前端展示加载态
    - delta:    回答分块逐段推送（每块 10~30 字）
    - done:     完成，携带完整结果 meta（conversation_id/provider/mode/route/timing）
    - error:    执行失败

    双路径：
    - high_performance=true:  真流式。复用 orchestrator 高性能 QA prompt，直接调用
      LLM 云端流式接口逐字/逐句推送（C_direct 流式版），打字机体验最真实。
    - high_performance=false: 完整业务链路（模板召回/模式路由/校验/存储），
      完成后分块推送实现流式观感，不破坏既有链路，离线演示同样可用。
    """
    user_id = int(data.get("user_id", 0))
    message = data.get("message", "")
    health_snapshot = data.get("health_snapshot", {}) or {}
    conversation_id = data.get("conversation_id", "")
    high_performance = bool(data.get("high_performance", False))
    # report 透传：前端把结构化报告数据（基本信息/体重/运动/饮食/issueTable/知识库卡片）
    # 直接通过 _report_context 传过来，不走 orchestrator 的 qa 包装（避免双层 prompt + 重复知识库检索）。
    # 直接用 CLOUD_PROMPTS["report"] 模板拼云端流式，prompt 最短。
    report_ctx = data.get("_report_context") or None

    if not message:
        return error_response(message="缺少 message 参数", code=400, detail="MISSING_MESSAGE")

    async def event_stream():
        yield _sse_event("thinking", {"message": "正在生成"+(report_ctx.get("period_label") if isinstance(report_ctx, dict) else "")+"健康分析报告..."})
        try:
            # ========== report 专属透传分支：最短 prompt，直接云端 report 模板 ==========
            if isinstance(report_ctx, dict):
                from prompts.cloud import CLOUD_PROMPTS
                tmpl = CLOUD_PROMPTS.get("report")
                if tmpl:
                    # 1. 取字段（空值兜底）
                    period_label = str(report_ctx.get("period_label") or "本期")
                    report_body = str(report_ctx.get("report_body") or "（数据为空）").strip()
                    kb_snippets = str(report_ctx.get("kb_snippets") or "（无本地知识库参考）").strip()
                    issue_table = str(report_ctx.get("issue_table") or "|（暂无明显营养问题）| - | - | - |").strip()

                    # 2. 用 mode_router 复用「系统自动推导健康上下文」逻辑（精简版）
                    try:
                        from services.mode_router import mode_router
                        ctx = mode_router._compute_user_derived_context(
                            user_profile=(health_snapshot or {}).get("profile", {}) or {},
                            health_snapshot=health_snapshot or {},
                        )
                    except Exception:
                        ctx = "（无）"

                    # 3. 拼 prompt
                    prompt = tmpl.format(
                        period_label=period_label,
                        user_derived_context=ctx,
                        report_body=report_body,
                        kb_snippets=kb_snippets,
                        issue_table=issue_table,
                    )

                    # 4. 对话记录（同 orchestrator.chat_stream_setup 行为一致）
                    try:
                        conv_id = orchestrator._stage_conversation(
                            user_id, message, conversation_id, health_snapshot,
                        )
                    except Exception:
                        conv_id = conversation_id or f"report_{int(time.time())}"

                    # 5. 云端流式
                    start_ts = time.time()
                    messages = [
                        {"role": "system", "content": "你是专业注册营养师与运动医学顾问。严格按用户要求的 Markdown 结构输出报告，不要添加任何额外引导语。"},
                        {"role": "user", "content": prompt},
                    ]
                    gen = llm.chat_stream(
                        messages,
                        timeout=settings.LLM_TIMEOUT_HIGH_PERF,
                    )
                    parts = []
                    async for delta in _iter_sync_stream(gen):
                        if delta:
                            parts.append(delta)
                            yield _sse_event("delta", {"content": delta})
                    full_text = "".join(parts)
                    response_text = orchestrator.finalize_chat_stream(conv_id, full_text, health_snapshot)
                    elapsed = round(time.time() - start_ts, 2)
                    result = {
                        "conversation_id": conv_id,
                        "response": response_text,
                        "provider": "deepseek",
                        "mode": "high_performance",
                        "route": "C_report_direct_stream",
                        "high_performance": True,
                        "validation": {"skipped": True, "reason": "report专属真流式"},
                        "elapsed_seconds": elapsed,
                        "retrieve_info": [],
                        "timing_breakdown": {"stream_ms": round(elapsed * 1000)},
                    }
                    yield _sse_event("done", result)
                    return

            if high_performance:
                # ---- 真流式路径（高性能模式）----
                setup = orchestrator.chat_stream_setup(
                    user_id=user_id,
                    message=message,
                    health_snapshot=health_snapshot,
                    conversation_id=conversation_id,
                    high_performance=True,
                )
                if setup is not None:
                    start_ts = time.time()
                    conv_id, gen = setup
                    parts = []
                    async for delta in _iter_sync_stream(gen):
                        if delta:
                            parts.append(delta)
                            yield _sse_event("delta", {"content": delta})
                    full_text = "".join(parts)
                    response_text = orchestrator.finalize_chat_stream(conv_id, full_text, health_snapshot)
                    elapsed = round(time.time() - start_ts, 2)
                    result = {
                        "conversation_id": conv_id,
                        "response": response_text,
                        "provider": "deepseek",
                        "mode": "high_performance",
                        "route": "C_direct_stream",
                        "high_performance": True,
                        "validation": {"skipped": True, "reason": "high_performance真流式"},
                        "elapsed_seconds": elapsed,
                        "retrieve_info": [],
                        "timing_breakdown": {"stream_ms": round(elapsed * 1000)},
                    }
                    yield _sse_event("done", result)
                    return

            # ---- 完整业务链路（正常模式 / 流式不可用）----
            result = await run_in_thread(
                orchestrator.chat,
                user_id=user_id,
                message=message,
                health_snapshot=health_snapshot,
                conversation_id=conversation_id,
                force_fallback=data.get("_force_fallback", False),
                high_performance=high_performance,
            )
            response_text = str(result.get("response", ""))
            # 分块推送（打字机效果），期间事件循环保持响应
            for chunk in _chunk_sse_text(response_text):
                yield _sse_event("delta", {"content": chunk})
                await asyncio.sleep(0.01)
            yield _sse_event("done", result)
        except Exception as e:
            logger = get_logger("chat_stream")
            logger.exception(f"SSE 流式对话失败: {e}")
            yield _sse_event("error", {"message": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# NLU 饮食描述解析（语音/OCR/文字→结构化营养数据）
# ============================================================

@router.post("/api/v1/meal/parse")
async def meal_parse(data: dict):
    """将自然语言饮食描述解析为结构化营养数据

    支持:
    - 语音录入结果解析
    - OCR 文本解析
    - 自由文本饮食描述解析

    输入示例:
    {"text": "早餐吃了2个鸡蛋和1碗燕麦，午餐200g鸡胸肉配西兰花"}

    输出: {
        "raw_text": "...",
        "meals": { "早餐": { "foods": [...], "totals": {...} }, ... },
        "daily_totals": {...},
        "warnings": [...]
    }
    """
    text = data.get("text", "")
    meal_type = data.get("meal_type", "")

    if not text:
        return error_response(message="缺少 text 参数", code=400, detail="MISSING_TEXT")

    result = await run_in_thread(orchestrator.parse_meal, text, meal_type)
    return result


# ============================================================
# 知识库检索
# ============================================================

@router.post("/api/v1/retrieve")
async def retrieve(data: dict):
    query = data.get("query", "")
    top_k = data.get("top_k", 3)
    target_crowd = data.get("target_crowd", "")
    doc_level = data.get("doc_level", "")  # document/paragraph/fact 三级检索粒度

    if not query:
        return success_response(query=query, results=[], total=0)

    results = retrieve_knowledge(query, persona=target_crowd, top_k=top_k, doc_level=doc_level)

    return success_response(query=query, results=results, total=len(results))


# ============================================================
# Agent 调用路由（全部通过编排器）
# ============================================================

@router.post("/api/v1/nutrition/analyze")
async def nutrition_analyze(data: dict):
    user_profile = data.get("user_profile", {})
    daily_nutrition = data.get("daily_nutrition", {})
    daily_exercise = data.get("daily_exercise", {})
    if not user_profile:
        return error_response(message="缺少 user_profile 参数", code=400, detail="MISSING_USER_PROFILE")
    return await run_in_thread(orchestrator.process, "nutrition", user_profile, daily_nutrition, daily_exercise)


@router.post("/api/v1/food/audit")
async def food_audit(data: dict):
    if not data.get("food_name"):
        return error_response(message="缺少 food_name 参数", code=400, detail="MISSING_FOOD_NAME")
    return await run_in_thread(orchestrator.process, "food_audit", data)


@router.post("/api/v1/voice/parse")
async def voice_parse(data: dict):
    text = data.get("text", "")
    if not text:
        return {"items": []}
    return await run_in_thread(orchestrator.process, "voice", text=text)


@router.post("/api/v1/report/weekly-summary")
async def weekly_summary(data: dict):
    user_profile = data.get("user_profile", {})
    weekly_stats = data.get("weekly_stats", {})
    if not user_profile:
        return error_response(message="缺少 user_profile 参数", code=400, detail="MISSING_USER_PROFILE")
    return await run_in_thread(orchestrator.process, "weekly", user_profile, weekly_stats)


@router.post("/api/v1/article/generate")
async def article_generate(data: dict):
    topic = data.get("topic", "")
    target_crowd = data.get("target_crowd", "")
    if not topic:
        return error_response(message="缺少 topic 参数", code=400, detail="MISSING_TOPIC")
    return await run_in_thread(orchestrator.process, "article", topic, target_crowd)


# ============================================================
# 科普文章母稿（B方案：本地Ollama框架 → 云端API外扩 → 本地格式校验）
# ============================================================

def _generate_mother_draft_v32(topic, group, persona, keywords):
    """B方案双模型流水线（pipeline_v32）：Stage1 本地Ollama出框架 → Stage2 DeepSeek外扩 → Stage3 本地格式校验，
    外加五道质量闸门（知识库预处理/主题过滤/PMID校验/截断检测/引用自检）。

    延迟导入 pipeline_v32 并恢复 cwd：该模块顶层有 os.chdir 副作用，不应影响整个 AI 服务进程。
    """
    import os as _os
    _cwd = _os.getcwd()
    try:
        from pipeline_v32 import run_pipeline
        result = run_pipeline(group, persona, topic, keywords or [])
        if not result:
            return {"error": "流水线未返回结果（Stage 1 本地框架生成失败）"}
        article = (result.get("article") or "").strip()
        if not article:
            return {"error": "流水线返回空母稿"}
        return {
            "article": article,
            "validation": result.get("validation"),
            "tracker": result.get("tracker"),
            "output_file": result.get("output_file"),
        }
    except Exception as e:
        return {"error": "流水线异常: %s" % e}
    finally:
        _os.chdir(_cwd)


@router.post("/api/v1/articles/mother-draft")
async def article_mother_draft(data: dict):
    """科普文章母稿生成（B方案）：本地出框架 → 云端外扩 → 本地校验。

    Body: {topic 必填, target_crowd/group 二选一(默认普通人), persona, keywords[]}
    keywords 为 PubMed 检索关键词列表，缺省按人群默认映射。
    """
    topic = (data.get("topic") or "").strip()
    if not topic:
        return error_response(message="缺少 topic 参数", code=400, detail="MISSING_TOPIC")
    group = (data.get("target_crowd") or data.get("group") or data.get("persona") or "普通人").strip()
    persona = (data.get("persona") or group).strip()
    keywords = data.get("keywords") or data.get("pubmed_keywords") or None
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    result = await run_in_thread(_generate_mother_draft_v32, topic, group, persona, keywords)
    if "error" in result:
        return error_response(message=result["error"], code=502, detail="MOTHER_DRAFT_PIPELINE_ERROR")

    tracker = result.get("tracker") or {}
    data = {
        "response": result["article"],
        "provider": "pipeline_v32",
        "mode": "B方案（本地框架→云端外扩→本地校验）",
        "route": "pipeline_v32",
        "validation": result.get("validation"),
    }
    # B方案双模型流水线的 token 明细（区分本地 Ollama 框架/校验 与 云端 DeepSeek 扩写）
    data["tokens"] = {
        "local": {
            "total": tracker.get("local_total", 0),
            "input": 0, "output": tracker.get("local_total", 0),
            "calls": tracker.get("local_calls", 0),
            "model": "ollama(qwen2.5-7b)",
        },
        "cloud": {
            "total": tracker.get("cloud_total", 0),
            "input": 0, "output": tracker.get("cloud_total", 0),
            "calls": tracker.get("cloud_calls", 0),
            "cached": 0,
            "model": "deepseek(外扩)",
        },
        "total": tracker.get("total", 0),
        "estimated": True,  # 本地 token 为字符数估算
    }
    return success_response(data=data)


@router.post("/api/v1/diet/plan")
async def diet_plan(data: dict):
    user_profile = data.get("user_profile", {})
    goal = data.get("goal", "")
    # 新增：高性能模式开关
    high_performance = bool(data.get("high_performance", False))
    if not user_profile:
        return error_response(message="缺少 user_profile 参数", code=400, detail="MISSING_USER_PROFILE")
    return await run_in_thread(
        orchestrator.process,
        "diet", user_profile, goal, high_performance=high_performance,
        today_diet=data.get("today_diet", []),
        today_diet_total=data.get("today_diet_total", {}),
        recent_exercise=data.get("recent_exercise", {}),
        today_body_metrics=data.get("today_body_metrics", {}),
    )


@router.post("/api/v1/reflection")
async def reflection(data: dict):
    question = data.get("question", "")
    resp = data.get("response", "")
    rating = data.get("rating", 3)
    reason = data.get("reason", "")
    return await run_in_thread(orchestrator.process, "reflect", question, resp, rating, reason)


@router.post("/api/v1/health/reflection")
async def health_reflection(data: dict):
    user_profile = data.get("user_profile", {})
    health_data = data.get("health_data", {})
    concerns = data.get("concerns", [])
    return await run_in_thread(orchestrator.process, "reflect_health", user_profile, health_data, concerns)


# ============================================================
# 新增：食材菜谱推荐
# ============================================================

@router.post("/api/v1/food/recommend")
async def food_recommend(data: dict):
    ingredients = data.get("ingredients", [])
    crowd_type = data.get("crowd_type", "普通人")
    goal = data.get("goal", "健康饮食")
    # 新增：高性能模式开关
    high_performance = bool(data.get("high_performance", False))

    if not ingredients:
        return error_response(message="缺少 ingredients 参数", code=400, detail="MISSING_INGREDIENTS")

    return await run_in_thread(
        orchestrator.process,
        "food_recommend", ingredients, crowd_type, goal, high_performance=high_performance,
        user_profile=data.get("user_profile", {}),
        today_diet=data.get("today_diet", []),
        today_diet_total=data.get("today_diet_total", {}),
        recent_exercise=data.get("recent_exercise", {}),
        today_body_metrics=data.get("today_body_metrics", {}),
    )


# ============================================================
# 新增：运动建议
# ============================================================

@router.post("/api/v1/exercise/advice")
async def exercise_advice(data: dict):
    user_profile = data.get("user_profile", {})
    goal = data.get("goal", "保持健康")
    preferences = data.get("preferences", "")
    chronic_diseases = data.get("chronic_diseases", [])
    # 新增：高性能模式开关
    high_performance = bool(data.get("high_performance", False))

    if not user_profile:
        return error_response(message="缺少 user_profile 参数", code=400, detail="MISSING_USER_PROFILE")
    return await run_in_thread(
        orchestrator.process,
        "exercise", user_profile, goal, preferences, chronic_diseases, high_performance=high_performance,
        today_diet=data.get("today_diet", []),
        today_diet_total=data.get("today_diet_total", {}),
        recent_exercise=data.get("recent_exercise", {}),
        today_body_metrics=data.get("today_body_metrics", {}),
    )
