import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ---- LLM 配置 ----
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    LLM_MODE = os.getenv("LLM_MODE", "cloud")  # cloud / local
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))          # LLM 请求超时秒数
    LLM_TIMEOUT_HIGH_PERF = int(os.getenv("LLM_TIMEOUT_HIGH_PERF", "45"))  # 高性能模式（演示）云端超时放宽
    # 输出上限：deepseek-chat 默认 max_tokens=4096，长报告（周报分析/科普文章）会被硬截断，显式放宽到上限 8192
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "8192"))
    MAX_LLM_CONCURRENCY = int(os.getenv("MAX_LLM_CONCURRENCY", "5"))  # 最大并发数
    LLM_DAILY_TOKEN_LIMIT = int(os.getenv("LLM_DAILY_TOKEN_LIMIT", "1000000"))  # 每日 token 阈值

    # ---- DeepSeek Responses API（方案1：语义化流式，默认关闭，验证跑通后再切换）----
    # 开关：false 走原有 Chat Completions；true 走 Responses API（仅 deepseek-v4-flash）
    RESPONSES_API_ENABLED = os.getenv("RESPONSES_API_ENABLED", "false").lower() in ("1", "true", "yes", "on")
    RESPONSES_API_BASE = os.getenv("RESPONSES_API_BASE", "https://api.deepseek.com")  # 文档示例 base_url（不带 /v1）
    RESPONSES_MODEL = os.getenv("RESPONSES_MODEL", "deepseek-v4-flash")              # 目前仅支持 v4-flash
    # 流式结束语义：completed 正常 / incomplete 截断 / failed 失败，前端据此区分结束态

    # ---- Ollama 本地大模型配置 ----
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-7b-local")
    # 上下文窗口：用户实测最大约 13000 token（6G RTX 3060）
    # 2048 → 8192，容纳复杂 prompt（知识库检索+健康快照+NLU）
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
    OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    # 本地模式独立超时：本地大模型（qwen2.5-7b）在复杂 prompt 下耗时较长，
    # 放宽到 300s 以避免普通模式（A方案本地改写/Stage1框架）被超时误杀。
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5分钟兜底

    # ---- 向量模型 ----
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "./models/bge-base-zh-v1.5")
    EMBEDDING_DIM = 768

    # ---- 存储路径 ----
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./knowledge/chroma_db_storage")
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    CACHE_DB_PATH = os.getenv("CACHE_DB_PATH", "./data/cache.db")   # 持久化缓存路径
    MEMORY_DB_PATH = os.getenv("MEMORY_DB_PATH", "./data/user_memory.db")  # 用户记忆库
    TOKEN_USAGE_DB = os.getenv("TOKEN_USAGE_DB", "./data/token_usage.db")  # Token 用量库
    TEMPLATES_DB_PATH = os.getenv("TEMPLATES_DB_PATH", "./data/templates.db")  # AI 模板库（SQLite 双写）

    # ---- 服务端口 ----
    AI_SERVICE_PORT = int(os.getenv("AI_SERVICE_PORT", "8002"))  # 与 start_all.ps1 一致

    # ---- 环境配置 ----
    ENV_MODE = os.getenv("ENV_MODE", "dev")  # dev / demo / prod

    # ---- 知识库自增长配置（mode_router 的 C 方案结果自动入库） ----
    KB_AUTO_INGEST_C_RESULTS = os.getenv("KB_AUTO_INGEST_C_RESULTS", "true").lower() in ("1", "true", "yes", "on")
    KB_DUP_SIMILARITY_THRESHOLD = float(os.getenv("KB_DUP_SIMILARITY_THRESHOLD", "0.45"))

    # ---- 知识库去重配置（四层漏斗） ----
    KB_DEDUP_ENABLED = os.getenv("KB_DEDUP_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    KB_DEDUP_HIGH_THRESHOLD = float(os.getenv("KB_DEDUP_HIGH_THRESHOLD", "0.75"))       # 高相似→云端合并
    KB_DEDUP_MEDIUM_THRESHOLD = float(os.getenv("KB_DEDUP_MEDIUM_THRESHOLD", "0.50"))   # 中相似→标记变体
    KB_DEDUP_TOP_K_CANDIDATES = int(os.getenv("KB_DEDUP_TOP_K_CANDIDATES", "5"))         # 候选集大小

    # ---- 知识库双层智能聚类配置（kb_cluster.py） ----
    KB_CLUSTER_ENABLED = os.getenv("KB_CLUSTER_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    KB_CLUSTER_HIGH_THRESHOLD = float(os.getenv("KB_CLUSTER_HIGH_THRESHOLD", "0.70"))   # BGE 高相似→直接归簇
    KB_CLUSTER_LOW_THRESHOLD = float(os.getenv("KB_CLUSTER_LOW_THRESHOLD", "0.40"))     # BGE 低相似→直接无关
    KB_CLUSTER_LLM_AMBIGUOUS = os.getenv("KB_CLUSTER_LLM_AMBIGUOUS", "true").lower() in ("1", "true", "yes", "on")  # 灰色区间启用 LLM 终审

    # ---- 文献智能合并配置（literature_merge.py） ----
    KB_MERGE_ENABLED = os.getenv("KB_MERGE_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    KB_MERGE_TARGET_WORDS = int(os.getenv("KB_MERGE_TARGET_WORDS", "500"))              # 复合卡片目标字数

    # ---- 学术争议识别配置（dispute_detect.py） ----
    KB_DISPUTE_ENABLED = os.getenv("KB_DISPUTE_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    KB_DISPUTE_MIN_CARDS = int(os.getenv("KB_DISPUTE_MIN_CARDS", "2"))                  # 至少卡片数才判争议

    # ---- 知识库内容长度配置 ----
    KB_CONTENT_MAX_LENGTH = int(os.getenv("KB_CONTENT_MAX_LENGTH", "500"))   # 单篇内容上限（字）
    KB_CONTENT_DISPLAY_LENGTH = int(os.getenv("KB_CONTENT_DISPLAY_LENGTH", "200"))  # 精简展示版长度

    # ---- 双层存储配置 ----
    KB_DUAL_LAYER_STORAGE = os.getenv("KB_DUAL_LAYER_STORAGE", "true").lower() in ("1", "true", "yes", "on")

    # ---- 冷数据清理（比赛阶段默认关闭） ----
    KB_AUTO_COLD_CLEANUP = os.getenv("KB_AUTO_COLD_CLEANUP", "false").lower() in ("1", "true", "yes", "on")

    # ---- 本地大模型相关性校验 ----
    KB_LOCAL_RELEVANCE_CHECK = os.getenv("KB_LOCAL_RELEVANCE_CHECK", "true").lower() in ("1", "true", "yes", "on")

    # ---- RAG 动态 top_k 检索（阈值按实际相似度分布校准，可配置）----
    # 分段策略：≥ HIGH 取 RAG_TOPK_HIGH_COUNT 条；[LOW, HIGH) 取 RAG_TOPK_LOW_COUNT 条；更低按 default_top_k
    RAG_DYNAMIC_TOPK_ENABLED = os.getenv("RAG_DYNAMIC_TOPK_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    RAG_TOPK_HIGH_THRESHOLD = float(os.getenv("RAG_TOPK_HIGH_THRESHOLD", "0.70"))   # 高相似度阈值
    RAG_TOPK_LOW_THRESHOLD = float(os.getenv("RAG_TOPK_LOW_THRESHOLD", "0.45"))     # 低相似度阈值
    RAG_TOPK_HIGH_COUNT = int(os.getenv("RAG_TOPK_HIGH_COUNT", "5"))                # 高相似段取条数
    RAG_TOPK_LOW_COUNT = int(os.getenv("RAG_TOPK_LOW_COUNT", "3"))                  # 中相似段取条数
    RAG_TOPK_CANDIDATE_MULTIPLIER = int(os.getenv("RAG_TOPK_CANDIDATE_MULTIPLIER", "2"))  # 候选集倍数

    # ---- 本地 reranker 重排序（bge-reranker 交叉编码精排） ----
    RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    RERANKER_MODEL_PATH = os.getenv("RERANKER_MODEL_PATH", "./models/bge-reranker-base")
    RERANKER_CANDIDATE_MULTIPLIER = int(os.getenv("RERANKER_CANDIDATE_MULTIPLIER", "3"))  # 候选集 = top_k × 倍数

    # ---- 模板召回 ----
    TEMPLATE_MIN_SIMILARITY = float(os.getenv("TEMPLATE_MIN_SIMILARITY", "0.40"))   # 模板召回最低相似度（实际分布约 0.45，取低值保证命中）
    TEMPLATE_MATCH_SKIP_LLM_THRESHOLD = float(os.getenv("TEMPLATE_MATCH_SKIP_LLM_THRESHOLD", "0.95"))  # 极高匹配直接返回模板，跳过 LLM 改写

    # ---- 权威文献数据源配置 ----
    TRIP_DATABASE_API_KEY = os.getenv("TRIP_DATABASE_API_KEY", "")  # Trip Database 公开API Key（可选，无Key时跳过该源）
    PUBMED_EUTILS_EMAIL = os.getenv("PUBMED_EUTILS_EMAIL", "")      # NCBI E-utilities 要求提供邮箱（可选）

    # ---- 校验组件配置（事实校验/数值检查/安全拦截） ----
    VALIDATOR_ENABLED = os.getenv("VALIDATOR_ENABLED", "true").lower() in ("1", "true", "yes", "on")
    VALIDATOR_BLOCK_SAFETY = os.getenv("VALIDATOR_BLOCK_SAFETY", "true").lower() in ("1", "true", "yes", "on")  # 安全风险BLOCK时替换响应

    @property
    def is_prod(self) -> bool:
        return self.ENV_MODE == "prod"

    @property
    def is_demo(self) -> bool:
        return self.ENV_MODE == "demo"

    @property
    def cache_ttl(self) -> int:
        """环境感知的缓存 TTL"""
        if self.is_demo:
            return 86400  # 演示环境 24h
        return 3600  # 开发环境 1h


settings = Settings()