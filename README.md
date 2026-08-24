# 个人健康助手

基于 RAG + 双模型（本地 Ollama / 云端 DeepSeek）的个人健康管理平台，提供饮食记录、营养分析、食谱推荐、科普文章、AI 咨询与运动建议。

## 项目结构

```
health/
├─ frontend-health/   # Vue 3 + TypeScript + Vite 前端（:5173）
├─ backend-health/    # Spring Boot 2.7 后端（:8082）
├─ ai_service/        # FastAPI AI 服务（:8002）
└─ 启动说明.md         # 四服务一键启动指南
```

## 快速开始

1. 启动 Ollama（本地模型服务，:11434）
2. 拉取对话模型：`ollama pull qwen2.5:7b-instruct-q4_K_M`（BGE 嵌入/重排模型已内置在 `ai_service/models/`，无需拉取）
3. 一键启动：`powershell -ExecutionPolicy Bypass -File start_all.ps1`
4. 访问系统：
   - 前端界面：http://localhost:5173
   - 后端 API：http://localhost:8082
   - AI 服务：http://localhost:8002

详细启动步骤与环境要求见 [启动说明.md](启动说明.md)。

## 其他部署方式

- **Docker 一键部署**（可选，未实测）：见 [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)。包含三个服务的
  Dockerfile、nginx 反向代理与 docker-compose.yml。
- **启动脚本路径可移植**：`start_all.ps1` 的路径均可用环境变量覆盖（`DSH_HEALTH_ROOT` /
  `DSH_JDK8` / `DSH_MVN` / `DSH_NODEJS` / `DSH_PY312` / `DSH_OLLAMA_MODELS`），
  换机器/CI 无需改脚本。

## 文档

- [启动说明.md](启动说明.md) —— 启动流程与环境要求
- [项目当前架构说明.md](项目当前架构说明.md) —— 当前代码实况架构
- [优化后项目架构说明.md](优化后项目架构说明.md) —— 目标架构（v3.0）
- [AI模块架构设计文档.md](AI模块架构设计文档.md) —— AI 服务设计
- [前端应用架构设计文档.md](前端应用架构设计文档.md) —— 前端设计
- [后端系统架构设计文档.md](后端系统架构设计文档.md) —— 后端设计
- [数据库设计说明.md](数据库设计说明.md) —— 数据模型

## 技术栈

- 前端：Vue 3 + TypeScript + Pinia
- 后端：Spring Boot 2.7 + JPA + SQLite + Caffeine
- AI：FastAPI + ChromaDB + sentence-transformers（BGE）+ Ollama / DeepSeek
