# 个人健康助手 AI 系统

## 快速开始

### 1. 启动 Ollama 服务
```bash
ollama serve
```

### 2. 拉取所需模型
```bash
ollama pull qwen2.5:7b    # 对话模型
ollama pull bge-m3        # 嵌入模型
```

### 3. 一键启动所有服务
```powershell
# Windows
powershell -ExecutionPolicy Bypass -File "启动说明.md 同级的 start_all.ps1"
```

### 4. 访问系统
- 前端界面: http://localhost:5173
- 后端 API: http://localhost:8082
- AI 服务: http://localhost:8002

## 功能特性

- **智能营养问答**: 基于 RAG 的专业营养咨询
- **个性化膳食推荐**: 根据用户档案生成食谱
- **科普文章生成**: AI 辅助生成健康科普内容
- **运动营养指导**: 针对健身人群的专业建议
- **多端数据同步**: 前后端实时数据交互

## 技术栈

- **前端**: Vue 3 + TypeScript + Pinia
- **后端**: Spring Boot + JPA + SQLite
- **AI**: FastAPI + ChromaDB + Ollama

## 文档

详细技术文档请查看: AI系统技术文档与优化策略.md

## 支持

如有问题，请查看技术文档或联系开发团队。
