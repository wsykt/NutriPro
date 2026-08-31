# 个人健康助手

基于 **RAG + 云端大模型（DeepSeek）+ 本地向量检索（BGE）** 的个人健康管理平台，提供饮食记录、营养分析、食谱推荐、科普文章、AI 健康咨询与运动建议等一体化功能。

## 系统架构

```
health/
├─ frontend-health/   # Vue 3 + TypeScript + Vite 前端（:5173）
├─ backend-health/    # Spring Boot 2.7 后端（:8082）
├─ ai_service/        # FastAPI AI 服务（:8002，RAG 检索 + Agent 编排 + LLM）
└─ apache-maven-3.9.6 # 随包附带的 Maven（后端编译用）
```

## 快速开始

详见 [账号与环境配置说明.md](账号与环境配置说明.md)，简要步骤如下：

1. **准备环境**：JDK 8、Node.js 18+、Python 3.10+（详见配置说明）
2. **下载向量模型**：将 `bge-base-zh-v1.5` 放入 `ai_service/models/`（必装，维度 768，与随包知识库匹配）
3. **安装依赖**：`ai_service` 用 pip、`frontend-health` 用 npm、`backend-health` 用 Maven
4. **启动服务**（顺序）：AI 服务 → 后端 → 前端
5. **访问系统**：http://localhost:5173

## 端口一览

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 | 5173 | 用户界面（已代理 `/api` 到后端） |
| 后端 | 8082 | REST API + JWT 认证 |
| AI 服务 | 8002 | RAG 检索 / Agent 编排 / LLM 调用 |

## 预置数据

- 后端 `data/health.db`：预置 7 个账号（1 管理员 + 6 类人群测试账号）及演示数据
- AI 服务 `data/`：缓存、会话、食物库、模板库、Token 用量、用户记忆 6 个 SQLite
- AI 服务 `knowledge/chroma_db_storage`：RAG 向量知识库（随包已包含，无需重建）

## 技术栈

- 前端：Vue 3 + TypeScript + Pinia + Element Plus + ECharts + GSAP
- 后端：Spring Boot 2.7 + JPA + SQLite + JWT + Caffeine
- AI：FastAPI + ChromaDB + sentence-transformers（BGE）+ DeepSeek / Ollama
