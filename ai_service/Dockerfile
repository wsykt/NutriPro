# AI 服务（FastAPI + ChromaDB + BGE 向量检索）
# 说明：
#  - 模型（bge-base-zh-v1.5 / bge-reranker-base）较大（约 1.5GB），
#    通过卷挂载到 /app/models，不烧进镜像。
#  - 知识库 ChromaDB（/app/knowledge）与运行时数据（/app/data）同样挂卷。
#  - 密钥/LLM 配置通过环境变量注入（见 docker-compose.yml），勿写入镜像。
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    TRANSFORMERS_OFFLINE=1 \
    SENTENCE_TRANSFORMERS_HOME=/app/models \
    TORCH_HOME=/app/models

WORKDIR /app

# 先装依赖（利用层缓存）；requirements.txt 目前为 >= 版本范围，
# 生产建议锁定版本（见 DOCKER_DEPLOY.md 第 4 节）。
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY . .

EXPOSE 8002
# 端口与启动方式与本地一致（AI_SERVICE_PORT 环境变量可覆盖）
CMD ["sh", "-c", "python main.py"]
