"""
个人健康助手 AI 系统 - 自动化维护与性能优化文档生成
======================================================
"""

doc = """
# 个人健康助手 AI 系统 - 技术文档与优化策略

## 一、系统架构概览

### 1.1 三大服务架构
```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   前端应用   │────▶│  Spring Boot    │────▶│  FastAPI AI     │
│  (Vue 3)    │     │  后端服务        │     │  智能服务        │
└─────────────┘     │  (Java 8)       │     │  (Python 3.9+)  │
                    │                 │     │                 │
                    │  - REST API     │     │  - RAG 检索     │
                    │  - JWT 鉴权     │     │  - Agent 编排   │
                    │  - 数据持久化   │     │  - Ollama 本地  │
                    │  - 业务逻辑    │     │    大模型调用    │
                    └─────────────────┘     └─────────────────┘
                             │                         │
                             ▼                         ▼
                    ┌─────────────┐           ┌─────────────┐
                    │  SQLite     │           │  ChromaDB   │
                    │  关系数据库  │           │  向量数据库  │
                    └─────────────┘           └─────────────┘
```

### 1.2 核心技术栈
| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端 | Vue 3 + TypeScript | 3.4 | SPA 应用框架 |
| 前端 | Pinia | 2.1 | 状态管理 |
| 前端 | Vite | 5.x | 构建工具 |
| 后端 | Spring Boot | 2.7.18 | REST API 服务 |
| 后端 | JPA + Hibernate | 5.6 | ORM 框架 |
| 后端 | SQLite | 3.x | 关系数据库 |
| AI 服务 | FastAPI | 0.109 | AI 微服务 |
| AI 服务 | ChromaDB | 0.4 | 向量数据库 |
| AI 服务 | Ollama | 0.5+ | 本地大模型运行时 |
| AI 模型 | BGE-base-zh | 1.5 | 向量嵌入模型 |
| AI 模型 | qwen2.5:7b | 7B | 本地对话模型 |

---

## 二、功能模块详解

### 2.1 知识库系统 (Knowledge Base)

#### 数据流程
```
[新资料输入] → [预处理/清洗] → [向量化嵌入] → [ChromaDB 存储]
                                      │
                                      ▼
                               [元数据标记]
                               (来源/人群/主题)
```

#### 数据规范
| 字段 | 说明 | 示例 |
|------|------|------|
| card_id | 唯一标识符 | GUIDE_CDG_2022 |
| title | 文档标题 | 中国居民膳食指南（2022） |
| group | 目标人群 | 孕妇/老年人/糖尿病患者 |
| topic | 主题分类 | 均衡营养与膳食模式 |
| source_channel | 来源渠道 | 官方指南/PubMed |
| purified_content | 提纯内容 | 结构化文本 |

#### 现有数据统计
- **总文档数**: 610 篇
- **来源分布**: PubMed (87.2%), Europe-PMC (6.9%), 官方指南 (5.6%), 中国食物营养成分查询平台 (0.3%)
- **人群覆盖**: 普通人, 孕妇, 青少年, 老年人, 糖尿病患者, 健身用户

---

## 三、本地大模型集成方案

### 3.1 Ollama 配置指南

#### 安装与模型拉取
```bash
# 安装 Ollama (Windows)
# 下载地址: https://ollama.com/download/windows

# 拉取所需模型
ollama pull qwen2.5:7b          # 对话生成模型 (4.7GB)
ollama pull bge-m3              # 向量嵌入模型 (570MB)
ollama pull llama3.2:3b         # 轻量对话模型 (2GB, 备选)

# 启动服务
ollama serve
```

#### 服务验证
```bash
# 检查服务状态
curl http://localhost:11434/api/tags

# 简单对话测试
curl -X POST http://localhost:11434/api/chat \
  -d '{
    "model": "qwen2.5:7b",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 3.2 模型对比评估

| 维度 | qwen2.5:7b (本地) | 云端模型 (参考) |
|------|-------------------|----------------|
| **响应速度** | 2-5秒/query | 1-3秒/query |
| **回答质量** | 中等，适合日常对话 | 高，支持复杂推理 |
| **数据隐私** | 完全本地 | 需上传 |
| **成本** | 零额外成本 | 按token计费 |
| **稳定性** | 依赖GPU | 稳定API |
| **最大上下文** | 2048 tokens | 32K+ tokens |
| **专业领域** | 中等医学知识 | 专业医学知识 |

### 3.3 推荐使用场景

✅ **适合本地模型的场景**:
- 日常营养问答（基础建议）
- 食物营养成分查询
- 简单数据总结和分析
- 用户档案整理
- 隐私敏感数据处理
- 离线环境使用

❌ **建议使用云端模型的场景**:
- 复杂医学诊断建议
- 最新研究文献查询
- 多步骤推理任务
- 长文本生成（文章、报告）
- 需要最新信息的查询

### 3.4 性能监控指标

| 指标 | 监控方法 | 目标值 |
|------|----------|--------|
| 响应延迟 | API 计时 | < 5秒 |
| Token 使用 | Ollama response | < 2000/query |
| 成功率 | 错误率统计 | > 95% |
| GPU 利用率 | nvidia-smi | < 80% |
| 内存使用 | 系统监控 | < 12GB |

---

## 四、知识库优化策略

### 4.1 现有数据覆盖分析

#### 优势领域
1. **宏观营养**: 三大营养素、膳食纤维、能量代谢
2. **人群专项**: 孕妇、老年人、青少年、糖尿病患者
3. **膳食指南**: 中国居民膳食指南2022全系列
4. **运动营养**: 肌酸、蛋白质、咖啡因等补剂研究

#### 薄弱领域
1. **健身人群**: 仅69篇（最少）
2. **特定疾病**: 痛风、骨质疏松、脂肪肝
3. **食物数据库**: 正在建立系统的食物成分数据
4. **实操食谱**: 缺少标准化的健康食谱库
5. **心理学营养**: 情绪性进食、饮食行为矫正

### 4.2 数据扩充计划

#### 第一阶段 (已完成)
- [x] 增加官方指南比例（已从2.8%提升至5.6%）
- [x] 补充健身人群专项文献（已增加5篇PubMed）
- [x] 建立食物营养数据爬取管道
- [x] 实现Ollama本地模型集成

#### 第二阶段 (短期规划)
- [ ] 大规模爬取中国食物营养成分数据库（nlc.chinanutri.cn）
- [ ] 补充常见疾病的营养干预方案（痛风、脂肪肝）
- [ ] 构建健康食谱库（50+标准食谱）
- [ ] 完善维生素、矿物质的专项指南

#### 第三阶段 (长期规划)
- [ ] 接入 USDA 食品成分数据库
- [ ] 建立用户生成内容（UGC）审核机制
- [ ] 发展社区贡献者体系
- [ ] 实现知识图谱可视化

### 4.3 检索效率优化

#### 当前问题
1. 向量检索仅使用余弦相似度，缺少关键词匹配
2. 文档分块策略固定，未考虑语义边界
3. 缺少查询重写（query rewriting）能力

#### 优化方案
```python
# 方案1: 混合检索（Hybrid Search）
# 向量相似度 + 关键词BM25 加权排序

# 方案2: 动态分块
# 根据文档结构自动调整分块大小

# 方案3: 查询增强
# 使用LLM将用户问题扩展为多个相关查询
```

---

## 五、系统维护指南

### 5.1 日常操作手册

#### 一键启动所有服务
```powershell
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File "C:\\...\\health\\start_all.ps1"
```

#### 知识库更新流程
```bash
# Step 1: 添加新文档到 knowledge_base/full_knowledge_base.json
# Step 2: 运行扩充脚本
python augment_knowledge_base.py

# Step 3: 同步到向量数据库
python import_cards_to_chromadb.py

# Step 4: 验证更新
python check_kb.py
```

#### 模型切换
```python
# 在 ollama_service.py 中修改
service = OllamaService(model_name="qwen2.5:7b")  # 本地
# 或通过环境变量
export OLLAMA_MODEL="qwen2.5:14b"  # 更大模型
```

### 5.2 故障排查

| 问题 | 排查步骤 | 解决方案 |
|------|----------|----------|
| Ollama 连接失败 | 1. 检查 ollama 是否运行<br>2. 检查端口11434 | `ollama serve` |
| 模型找不到 | 检查可用模型列表 | `ollama pull <model_name>` |
| GPU 内存不足 | 检查显存占用 | 切换更小模型/关闭其他GPU应用 |
| 知识库检索为空 | 1. 检查向量库是否为空<br>2. 检查嵌入模型 | 重新执行 `import_cards_to_chromadb.py` |
| 响应超时 | 检查网络/GPU负载 | 增加超时时间或切换模型 |

### 5.3 数据安全

#### 备份策略
```bash
# 每日备份向量数据库
cp chroma_db_storage/chroma.sqlite3 backup/chroma_$(date +%Y%m%d).db

# 每周备份知识库JSON
cp full_knowledge_base.json backup/kb_$(date +%Y%m%d).json
```

#### 版本管理
- 每次重大更新后打标签
- 保留最近 30 天的快照
- 使用 Git 管理知识库变更日志

---

## 六、未来发展方向

### 6.1 短期目标 (3个月)
1. 实现完整的食物营养成分数据库
2. 构建智能膳食推荐引擎
3. 增加营养计算工具（BMR/TDEE计算）
4. 完善用户反馈闭环

### 6.2 中期目标 (6个月)
1. 引入多模态能力（图片识别食物）
2. 实现个性化学习用户画像
3. 开发健康数据可视化面板
4. 建立社区问答机制

### 6.3 长期愿景 (12个月+)
1. 发展为开放的健康知识平台
2. 建立专家审核委员会
3. 对接医院/体检中心数据
4. 开发健康管理SaaS平台

---

## 附录

### A. 相关文件索引
| 文件 | 路径 | 说明 |
|------|------|------|
| 知识库数据 | ai_service/knowledge_base/full_knowledge_base.json | 610篇结构化文档 |
| 向量数据库 | ai_service/knowledge/chroma_db_storage/ | ChromaDB存储 |
| 爬虫脚本 | ai_service/crawler/food_crawler.py | 食物数据爬取框架 |
| 数据处理 | ai_service/process_and_ingest.py | 数据清洗与入库 |
| Ollama服务 | ai_service/ollama_service.py | 本地大模型封装 |
| 扩充脚本 | ai_service/augment_knowledge_base.py | 知识库扩充工具 |

### B. API 端点速查
| 服务 | 端点 | 说明 |
|------|------|------|
| Spring Boot | /api/users/auth | 用户认证 |
| Spring Boot | /api/foods/search | 食物搜索 |
| Spring Boot | /api/recipes/recommend | 食谱推荐 |
| Spring Boot | /api/articles/list | 科普文章列表 |
| FastAPI | /api/v1/chat | AI对话 |
| FastAPI | /api/v1/agent/search | Agent搜索 |
| FastAPI | /api/v1/knowledge/ingest | 知识库写入 |
| Ollama | /api/chat | 本地模型对话 |
| Ollama | /api/embeddings | 本地嵌入 |

---

> 文档生成时间: 2026-08-06
> 版本: v3.2
> 维护者: AI 技术团队
"""

# 保存文档
output_path = r"c:\Users\13425\Desktop\个人健康助手\health\AI系统技术文档与优化策略.md"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(doc)

print(f"技术文档已生成: {output_path}")
print(f"文档长度: {len(doc)} 字符")

# 同时生成一个简化的 README
readme_content = """# 个人健康助手 AI 系统

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
"""

readme_path = r"c:\Users\13425\Desktop\个人健康助手\health\README.md"
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"README.md 已生成: {readme_path}")
