# 一次性/离线脚本归档

以下脚本为知识库构建、数据导入、模型配置等**一次性离线任务**，不参与 AI 服务运行时
（经核查无任何运行时代码引用；运行时入口为 main.py 及其依赖模块）。归档仅为整理目录，
脚本仍可直接运行（工作目录需为 ai_service）。

| 脚本 | 用途 |
|------|------|
| build_knowledge_base_full.py | 全量构建知识库（ChromaDB 写入） |
| generate_kb_templates.py | 生成知识库模板 JSON |
| import_cards_to_chromadb.py | 知识卡片导入 ChromaDB |
| merge_kb_channels.py | 多渠道知识合并 |
| kb_extend.py | 知识库扩展 |
| knowledge_builder_channels.py | 分渠道构建知识库 |
| process_and_ingest.py | 数据处理并摄入 |
| augment_knowledge_base.py | 知识库增强 |
| check_kb.py / check_kb_files.py | 知识库检查 |
| import_mother_to_backend.py | 母稿导入后端 |
| manage_articles.py | 文章管理 |
| setup_ollama_model.py | Ollama 模型配置（会写回 ollama_service.py） |
| source_verifier.py | 知识库链接/PMID 校验 |
| ollama_service.py | 独立 Ollama 服务封装（当前未被运行时引用） |
| _check_db.py | 数据库检查（开发用） |

> 若某脚本确需回归运行时，请移回 ai_service/ 根目录，并确保无 import 循环。
