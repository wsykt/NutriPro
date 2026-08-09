"""AI 服务主入口（v2 — 使用 AgentOrchestrator）

改造点：
- 所有 API 端点统一通过 orchestrator 调度，不硬编码 Agent
- lifespan 初始化全部依赖
- 新增 /api/v1/agent/stats 统计接口
- 新增 /api/v1/food/recommend 食材菜谱推荐
- 新增 /api/v1/exercise/advice 运动建议
- 新增全局入参校验中间件
- 新增 /api/v1/knowledge/stats 知识库统计
- 新增 /api/v1/agent/stats/export 数据导出
- loguru 结构化日志

架构收敛拆分（v2.1）：
- 本文件仅保留：app 创建、CORS、全局中间件（validate_request_middleware /
  trace_id_middleware）、lifespan、/health 健康检查、路由器注册与运行入口。
- 全部 API 端点按业务域拆分至 routers/ 子模块（chat / tasks / ollama /
  knowledge / agent / quality / dashboard），端点路径、方法、请求参数、
  返回结构、SSE 格式与日志关键词均与原实现完全一致。
"""

import json
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config.settings import settings
from utils.log_config import get_logger

# 全局编排器
from agent.orchestrator import orchestrator

# 异步任务服务（阶段一·举措5）：lifespan 关闭时回收线程池
from services.async_task_service import async_task_service

# 请求校验配置
MAX_MESSAGE_LENGTH = 2000
MAX_TEXT_LENGTH = 500
REQUIRED_POST_FIELDS = {
    "/api/v1/chat": ["message"],
    "/api/v1/chat/stream": ["message"],
    "/api/v1/nutrition/analyze": ["user_profile"],
    "/api/v1/food/audit": ["food_name"],
    "/api/v1/article/generate": ["topic"],
    "/api/v1/diet/plan": ["user_profile"],
    "/api/v1/food/recommend": ["ingredients"],
    "/api/v1/exercise/advice": ["user_profile"],
    "/api/v1/report/weekly-summary": ["user_profile"],
    "/api/v1/meal/parse": ["text"],
}


# ============================================================
# 生命周期管理
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup_logger = get_logger("startup")
    startup_logger.info(f"AICore v2 启动中... (并发上限: {settings.MAX_LLM_CONCURRENCY})")

    # 1. 初始化 LLM
    from llm.router import llm
    startup_logger.info(f"LLM 模式: {settings.LLM_MODE}, 超时: {settings.LLM_TIMEOUT}s")

    # 2. 初始化向量库
    from vector.retriever import retriever
    try:
        retriever.ensure_initial_data()
        startup_logger.info(f"向量知识库就绪，记录数: {retriever.count()}")
    except Exception as e:
        startup_logger.warning(f"向量知识库初始化失败: {e}")

    # 2.5 启动对账：SQLite 模板库与 ChromaDB 双写一致性校验
    try:
        from services.template_store import template_store
        result = template_store.reconcile(retriever)
        startup_logger.info(f"模板库对账结果: {result}")
    except Exception as e:
        startup_logger.warning(f"模板库对账失败（非关键）: {e}")

    # 3. 初始化对话存储
    from conversation.store import store

    # 4. 初始化记忆提取
    from conversation.memory_extract import memory_extractor

    # 5. 初始化离线引擎
    from local_fallback_engine import fallback_engine

    # 6. 初始化编排器（注入所有依赖）
    orchestrator.init(
        llm=llm,
        retriever=retriever,
        store=store,
        memory_extractor=memory_extractor,
        local_engine=fallback_engine,
    )
    startup_logger.info("AgentOrchestrator 就绪")
    startup_logger.info("AICore v2 启动完成")

    yield
    startup_logger.info("AICore 正在关闭...")
    async_task_service.shutdown()


app = FastAPI(title="AI Core - 个人健康管理系统 v2", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 全局入参校验中间件
# ============================================================

@app.middleware("http")
async def validate_request_middleware(request: Request, call_next):
    """全局参数校验：空值拦截 + 超长文本截断"""
    if request.method != "POST":
        return await call_next(request)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={
            "detail": "请求体必须为合法 JSON 格式", "code": "INVALID_JSON"
        })

    path = request.url.path

    # 1. 必填字段校验
    required = REQUIRED_POST_FIELDS.get(path, [])
    for field in required:
        val = body.get(field)
        if val is None or (isinstance(val, (str, list)) and len(val) == 0):
            return JSONResponse(status_code=400, content={
                "detail": f"缺少必填参数: {field}", "code": "MISSING_FIELD"
            })

    # 2. 超长文本截断
    for text_field in ["message", "query", "text", "topic", "question"]:
        if text_field in body and isinstance(body[text_field], str):
            if len(body[text_field]) > MAX_TEXT_LENGTH:
                body[text_field] = body[text_field][:MAX_TEXT_LENGTH]
                body["_truncated"] = True

    # 3. 非 POST 校验接口走正常流程
    request.state.validated_body = body
    request._body = json.dumps(body).encode()

    return await call_next(request)


# ============================================================
# TraceID 中间件
# ============================================================

@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    """全局 TraceID 中间件：为每个请求生成唯一追踪 ID"""
    trace_id = request.headers.get("X-Trace-ID", "")
    if not trace_id:
        trace_id = uuid.uuid4().hex[:12]
    request.state.trace_id = trace_id

    logger = get_logger(trace_id)
    start = time.time()

    # 请求日志
    path = request.url.path
    method = request.method
    logger.info(f"[REQUEST] {method} {path}")

    try:
        response = await call_next(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[ERROR] {method} {path}: {e}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "trace_id": trace_id},
        )

    elapsed = time.time() - start
    logger.info(f"[RESPONSE] {method} {path} -> {response.status_code} ({elapsed:.2f}s)")

    # 响应头注入 TraceID
    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Response-Time"] = f"{elapsed:.2f}s"
    return response


# ============================================================
# 健康检查
# ============================================================

@app.get("/health")
async def health():
    stats = orchestrator.get_stats()
    return {
        "status": "ok",
        "version": "2.0.0",
        "agents_available": list(orchestrator._agents.keys()),
        "stats": stats,
    }


# ============================================================
# 路由器注册（端点按业务域拆分至 routers/ 子模块）
# ============================================================

from routers import chat, tasks, ollama, knowledge, agent, quality, dashboard

app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(ollama.router)
app.include_router(knowledge.router)
app.include_router(agent.router)
app.include_router(quality.router)
app.include_router(dashboard.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.AI_SERVICE_PORT)
