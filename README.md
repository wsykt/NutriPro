# 个人健康助手

基于 **RAG + 云端大模型（DeepSeek）+ 本地向量检索（BGE）** 的个人健康管理平台，提供饮食记录、营养分析、食谱推荐、科普文章、AI 健康咨询与运动建议等一体化功能。

## 系统架构

```
health/
├─ frontend-health/   # Vue 3 + TypeScript + Vite 前端（:5173）
├─ backend-health/    # Spring Boot 2.7 后端（:8082）
└─ ai_service/        # FastAPI AI 服务（:8002，RAG 检索 + Agent 编排 + LLM）
```

## 快速开始

1. **准备环境**：JDK 8、Maven 3.6+、Node.js 18+、Python 3.10+
2. **下载向量模型**：将 `bge-base-zh-v1.5` 放入 `ai_service/models/`（必装，维度 768，与仓库内知识库匹配，详见"向量模型下载"）
3. **配置云端 API Key（必填）**：AI 服务默认调用云端 DeepSeek 大模型，需自行申请并配置 Key：
   ```bash
   cd ai_service
   copy .env.template .env        # Linux/macOS: cp .env.template .env
   ```
   编辑 `.env`，将 `DEEPSEEK_API_KEY` 替换为你自己的 Key（可在 DeepSeek 开放平台申请），完成后重启 AI 服务。
4. **配置 Ollama 本地大模型（可选但推荐）**：详见"Ollama 本地大模型配置"，不装则科普文章本地框架能力自动降级，云端功能不受影响
5. **安装依赖**：`ai_service` 用 pip、`frontend-health` 用 npm、`backend-health` 用 Maven（详见"依赖安装"）
6. **启动服务**（顺序）：AI 服务 → 后端 → 前端（详见"启动步骤"）
7. **访问系统**：http://localhost:5173

## 账号密码对照表

系统预置 7 个账号，覆盖管理员与 6 类典型人群，可直接登录演示。

| 账号 | 密码 | 角色 | 人群 | 说明 |
|---|---|---|---|---|
| `admin` | `admin123` | 管理员 | 普通人 | 管理员后台（用户管理 / 食品管理 / 食谱管理 / 文章管理 / AI 统计） |
| `test001` | `123456` | 普通用户 | 普通人 | 基础功能演示 |
| `test002` | `123456` | 普通用户 | 健身 | 高蛋白、低脂人群 |
| `test003` | `123456` | 普通用户 | 老年 | 低盐、低脂人群 |
| `test004` | `123456` | 普通用户 | 孕妇 | 孕期营养关注 |
| `test005` | `123456` | 普通用户 | 青少年 | 高蛋白成长人群 |
| `test006` | `123456` | 普通用户 | 糖尿病 | 低糖饮食人群 |

> 说明：6 个测试账号已预置"今日饮食记录"与"近三日运动记录"，用于演示营养分析、AI 咨询、健康周报等流程。后端首次启动会自动校验以上账号（密码固定、属性与人群匹配），若数据库中被修改，重启后端即恢复默认值。

## 端口一览

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 | 5173 | 用户界面（已代理 `/api` 到后端） |
| 后端 | 8082 | REST API + JWT 认证 |
| AI 服务 | 8002 | RAG 检索 / Agent 编排 / LLM 调用 |

## 环境要求

| 组件 | 版本要求 | 用途 |
|---|---|---|
| JDK | 8（1.8.x） | 后端编译与运行 |
| Maven | 3.6+ | 后端构建 |
| Node.js | 18+ | 前端依赖安装与运行 |
| Python | 3.10+ | AI 服务运行 |

## 向量模型下载（唯一需要手动准备的部分）

AI 服务的 RAG 检索依赖本地向量模型，为控制仓库体积**未包含模型文件**（约 1.4GB），需手动下载。

### 必装：嵌入模型 bge-base-zh-v1.5

知识库向量按此模型的 768 维生成，**必须使用该模型**（换用其他模型会导致维度不匹配、检索失败）。

```bash
# 方式一：huggingface-cli（需先 pip install huggingface_hub）
huggingface-cli download BAAI/bge-base-zh-v1.5 --local-dir ai_service/models/bge-base-zh-v1.5

# 方式二：Git 拉取
git clone https://huggingface.co/BAAI/bge-base-zh-v1.5 ai_service/models/bge-base-zh-v1.5

# 方式三：国内镜像（下载慢时使用）
git clone https://hf-mirror.com/BAAI/bge-base-zh-v1.5 ai_service/models/bge-base-zh-v1.5
```

下载完成后确认目录结构为：

```
ai_service/models/bge-base-zh-v1.5/
├─ config.json
├─ model.safetensors   （或 pytorch_model.bin）
├─ tokenizer.json
├─ tokenizer_config.json
└─ vocab.txt
```

### 可选：重排序模型 bge-reranker-base

用于检索结果精排，可显著提升问答质量；**未下载时自动降级为原始排序，不影响系统运行**。

```bash
git clone https://huggingface.co/BAAI/bge-reranker-base ai_service/models/bge-reranker-base
# 或国内镜像
git clone https://hf-mirror.com/BAAI/bge-reranker-base ai_service/models/bge-reranker-base
```

模型路径在 `ai_service/.env` 中通过 `EMBEDDING_MODEL_NAME`、`RERANKER_MODEL_PATH` 配置（默认相对路径 `./models/...`，无需修改）。

## Ollama 本地大模型配置（可选但推荐）

AI 服务采用**本地 + 云端双模型混合架构**：

- **云端 DeepSeek**：负责 AI 咨询、营养分析、运动建议、周报等主流程（默认）；
- **本地 Ollama（qwen2.5）**：负责科普文章双模型流水线的"本地搭框架 / 格式校验"、正常模式下的本地改写与云端失败时的兜底。

> 说明：不装 Ollama，系统核心功能仍可通过云端正常运行（本地能力自动降级跳过）；但**科普文章生成（本地框架→云端外扩）、本地改写、本地兜底等能力不可用**，且无法体现本项目"本地 + 云端混合架构"的设计特色，故建议安装。

### 1. 安装 Ollama

从官网下载 Windows 版并安装：https://ollama.com/download/windows

安装后命令行验证：

```bash
ollama --version
```

### 2. 拉取基础模型

```bash
# 6G 显存安全版（推荐，Modelfile 按此版本调优）
ollama pull qwen2.5:7b-instruct-q4_K_M

# 显存 8G 以上可用标准版
ollama pull qwen2.5:7b
```

### 3. 创建系统专用模型

在 `ai_service` 目录下执行（使用仓库内的 `Modelfile.health_framework`，该文件针对 6G 显存配置了上下文窗口与温度参数）：

```bash
cd ai_service
ollama create qwen2.5-7b-local -f Modelfile.health_framework
```

创建完成后验证：

```bash
ollama list
# 应能看到 qwen2.5-7b-local:latest
```

### 4. 模式说明（已默认配置好，无需修改）

`.env` 中相关配置：

```ini
LLM_MODE=cloud               # 云端主用 + 本地辅助（推荐，默认）
OLLAMA_MODEL=qwen2.5-7b-local:latest   # 本地模型名（第 3 步创建）
OLLAMA_BASE_URL=http://localhost:11434 # Ollama 默认地址
```

- `LLM_MODE=cloud`（默认）：所有功能云端 DeepSeek 为主，本地 Ollama 承担文章框架、改写与兜底——**推荐演示此模式**；
- `LLM_MODE=local`：全部走本地模型（需显存充足，速度较慢）。

## 预置数据

- 后端 `data/health.db`：预置 7 个账号（1 管理员 + 6 类人群测试账号）及演示数据
- AI 服务 `data/`：缓存、会话、食物库、模板库、Token 用量、用户记忆 6 个 SQLite
- AI 服务 `knowledge/chroma_db_storage`：RAG 向量知识库（已包含在仓库中，无需重建）

## 依赖安装

按顺序在三个目录下安装依赖：

```bash
# 1. AI 服务（ai_service/ 目录）
pip install -r requirements.lock
# 或（无锁文件时）pip install -r requirements.txt

# 2. 前端（frontend-health/ 目录）
npm install

# 3. 后端（backend-health/ 目录）
mvn dependency:resolve
```

## 启动步骤

**务必按顺序启动**（AI 服务 → 后端 → 前端）：

### 1. 启动 AI 服务（端口 8002）

```bash
cd ai_service
python main.py
```

看到日志 `AICore v2 启动完成` 即成功（首次启动会加载向量模型，耗时较长属正常）。

### 2. 启动后端（端口 8082）

```bash
cd backend-health
mvn spring-boot:run
```

启动时会自动执行数据库校验与演示数据补齐，看到 `Started HealthApplication` 即成功。

> 备选：也可先打包再运行
> ```
> mvn package -DskipTests
> java -jar target/health-backend-1.0.0.jar
> ```

### 3. 启动前端（端口 5173）

```bash
cd frontend-health
npm run dev
```

### 4. 访问系统

- 前端界面：http://localhost:5173
- 后端健康检查：http://localhost:8082/api/health
- AI 服务健康检查：http://localhost:8002/health

## 常见问题

| 问题 | 处理方式 |
|---|---|
| AI 服务启动报模型维度错误 | 检查 `bge-base-zh-v1.5` 是否完整下载、路径是否为 `ai_service/models/bge-base-zh-v1.5` |
| 后端编译失败 `cannot find symbol` | 确认使用 JDK 8（`java -version` 应为 1.8.x），并用 Maven 3.6+ 构建 |
| 前端 `npm run dev` 报错 | 确认 `npm install` 已执行且 Node ≥ 18 |
| 端口被占用 | 三个端口 5173/8082/8002 分别被占用时，先结束占用进程或按需修改配置 |
| 登录后提示 Token 失效 | 后端未设置 `JWT_SECRET` 环境变量时每次重启会生成随机密钥，属正常现象，重新登录即可 |
| AI 功能无响应 | 确认 AI 服务（8002）已启动且 `.env` 中 `DEEPSEEK_API_KEY` 有效 |
| 科普文章生成失败"Stage 1 本地框架生成失败" | 未安装/未启动 Ollama，或未创建 `qwen2.5-7b-local` 模型，按上文 Ollama 章节配置后重启 AI 服务 |

## 技术栈

- 前端：Vue 3 + TypeScript + Pinia + Element Plus + ECharts + GSAP
- 后端：Spring Boot 2.7 + JPA + SQLite + JWT + Caffeine
- AI：FastAPI + ChromaDB + sentence-transformers（BGE）+ DeepSeek / Ollama
