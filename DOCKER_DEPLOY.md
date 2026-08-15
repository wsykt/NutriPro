# Docker 部署指南（可移植性方案）

> **重要**：本套 Docker 文件是在无 Docker 环境的机器上编写产出的，
> **尚未在本机实测**。首次使用请逐项核对下方「风险点清单」。

## 前置条件

- Docker Desktop（Windows）或任意 Docker Engine 24+
- 磁盘空间：镜像约 2~3GB（AI 服务含 torch/chromadb）+ 模型数据（约 1.5GB，挂卷不入镜像）

## 部署步骤

```powershell
# 0. 进入项目根目录
cd C:\Users\13425\Desktop\个人健康助手\health

# 1. 准备密钥（复制模板并填写 DEEPSEEK_API_KEY）
Copy-Item .env.docker.example .env.docker
#   编辑 .env.docker，填入真实 DEEPSEEK_API_KEY

# 2. 确认大数据目录存在（compose 挂载来源）
#    ai_service/models / ai_service/knowledge / ai_service/data / backend-health/data

# 3. 构建并启动
docker compose --env-file .env.docker up -d --build

# 4. 验证
#    前端:   http://localhost:8080
#    AI:     http://localhost:8002/health
#    后端:   http://localhost:8082
#    日志:   docker compose logs -f
```

## 服务拓扑

```
浏览器 → nginx(:8080) ──/api──→ backend(:8082) ──/api/v1──→ ai_service(:8002) ──→ DeepSeek / Ollama
                    └──静态资源──→ dist/
```

## 风险点清单（未实测确认项）

| # | 风险点 | 说明与核对方式 |
|---|--------|----------------|
| 1 | 后端基础镜像 maven:3.8-openjdk-8 | 若拉取失败换 maven:3.9-eclipse-temurin-8（pom 为 Java 1.8，构建兼容） |
| 2 | 后端健康检查用了 wget | temurin:8-jre 可能无 wget，启动后手动 curl http://localhost:8082 核对；失败可改用 curl 镜像 |
| 3 | AI 服务启动加载 BGE 模型耗时 | start_period 已放宽 60s，若仍超时可在 healthcheck 中去掉 condition: service_healthy |
| 4 | Windows 路径映射 | compose 内相对路径基于 health/ 目录；Ollama 卷注释为 /d/ollama/models，按实际路径调整 |
| 5 | Ollama 容器化 | 默认走宿主机 11434（host.docker.internal）；如需容器化 Ollama 取消 profile 注释 |
| 6 | 密钥 | .env.docker 与 ai_service/.env 均可注入；切勿把真实 key 提交到镜像/仓库 |

## 依赖锁定（已完成）

- ai_service/requirements.lock 已生成：锁定版本来自通过全部 75 项单测的实际运行环境
  （fastapi 0.141.1 / chromadb 1.5.9 / torch 2.13.0 等）。镜像内建议改为
  `pip install --no-cache-dir -r requirements.lock` 保证可复现（当前 Dockerfile 用 requirements.txt）。
- 前端已使用 package-lock.json（npm ci），后端依赖由 Maven 坐标锁定，无需额外处理。
