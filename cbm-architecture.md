# 个人健康助手 知识图谱架构报告

> 由 CBM (Codebase Memory) 知识图谱自动导出 · 生成时间：2026-08-23 12:33:01

> 数据源：CBM 图谱数据库 · 项目：`wsl-Ubuntu-22.04-root-health`


## 1. 总体概览

| 指标 | 数值 |
|---|---|
| 节点总数 | **5930** |
| 边（关系）总数 | **24427** |
| 文件数 | **387** |
| 模块目录数 | **52** |

## 2. 节点类型分布

| 类型 | 数量 | 涉及文件数 |
|---|---|---|
| Method（方法） | 1805 | 166 |
| Variable（变量） | 1084 | 239 |
| Function（函数） | 678 | 109 |
| Field（字段） | 550 | 86 |
| Section（区块） | 418 | 14 |
| File（文件） | 387 | 387 |
| Module（模块） | 272 | 272 |
| Route（路由） | 259 | 23 |
| Class（类） | 245 | 153 |
| EnvVar（环境变量） | 66 | 0 |
| Folder（目录） | 66 | 66 |
| Decorator（装饰器） | 46 | 0 |
| Interface（接口） | 37 | 29 |
| Package（包） | 10 | 1 |
| Type（类型） | 4 | 4 |
| Enum（枚举） | 1 | 1 |
| Project（项目） | 1 | 1 |
| Branch（分支） | 1 | 1 |

## 3. 关系（边）类型分布

| 关系类型 | 数量 |
|---|---|
| DEFINES（定义） | 7252 |
| CALLS（调用） | 5553 |
| USAGE（使用） | 5035 |
| WRITES（写入） | 1964 |
| DEFINES_METHOD（定义方法） | 1800 |
| DECORATES（装饰） | 692 |
| IMPORTS（导入） | 585 |
| CONTAINS_FILE（包含文件） | 387 |
| TESTS（测试） | 326 |
| HANDLES（处理路由） | 203 |
| SEMANTICALLY_RELATED（语义相关） | 178 |
| SIMILAR_TO（相似） | 176 |
| HTTP_CALLS（HTTP调用） | 83 |
| CONFIGURES（配置） | 72 |
| CONTAINS_FOLDER（包含目录） | 57 |
| INHERITS（继承） | 18 |
| CALL_REFERENCE（调用引用） | 17 |
| OVERRIDE（覆写） | 11 |
| DEPENDS_ON（依赖） | 10 |
| RAISES（抛出） | 7 |
| HAS_BRANCH（分支） | 1 |

## 4. 模块结构

| 模块目录 | 文件数 |
|---|---|
| `backend-health/src` | 116 |
| `frontend-health/src` | 76 |
| `ai_service/scripts` | 63 |
| `ai_service/agent` | 18 |
| `ai_service/crawler` | 15 |
| `ai_service/services` | 14 |
| `backend-health/scripts` | 11 |
| `ai_service/tests` | 9 |
| `ai_service/routers` | 8 |
| `ai_service/utils` | 8 |
| `ai_service/prompts` | 3 |
| `ai_service/vector` | 3 |
| `ai_service/constants` | 2 |
| `ai_service/conversation` | 2 |
| `frontend-health/public` | 2 |
| `AI模块架构设计文档.md` | 1 |
| `DOCKER_DEPLOY.md` | 1 |
| `README.md` | 1 |
| `ai_service/.env.template` | 1 |
| `ai_service/Dockerfile` | 1 |
| `ai_service/_check_health_db.py` | 1 |
| `ai_service/config` | 1 |
| `ai_service/dashboard` | 1 |
| `ai_service/llm` | 1 |
| `ai_service/local_fallback_engine.py` | 1 |
| `ai_service/main.py` | 1 |
| `ai_service/pipeline_v32.py` | 1 |
| `ai_service/pytest.ini` | 1 |
| `ai_service/requirements.txt` | 1 |
| `backend-health/Dockerfile` | 1 |
| `backend-health/SQL建表演进报告.md` | 1 |
| `backend-health/pom.xml` | 1 |
| `batch_generate_articles.py` | 1 |
| `docker-compose.yml` | 1 |
| `frontend-health/Dockerfile` | 1 |
| `frontend-health/index.html` | 1 |
| `frontend-health/nginx.conf` | 1 |
| `frontend-health/postcss.config.js` | 1 |
| `frontend-health/tailwind.config.js` | 1 |
| `frontend-health/tsconfig.node.json` | 1 |
| `frontend-health/vite.config.ts` | 1 |
| `start_all.ps1` | 1 |
| `start_demo_offline.ps1` | 1 |
| `优化后项目架构说明.md` | 1 |
| `前端应用架构设计文档.md` | 1 |
| `功能实现详解.md` | 1 |
| `后端系统架构设计文档.md` | 1 |
| `启动说明.md` | 1 |
| `提示词文档_v3.2.md` | 1 |
| `数据库设计说明.md` | 1 |
| `架构与功能说明.md` | 1 |
| `项目当前架构说明.md` | 1 |

## 5. 热点文件（被引用最多，核心模块）

| 文件 | 被引用次数 |
|---|---|
| `<python-builtins>` | 3001 |
| `backend-health/src/main/java/com/health/entity/Article.java` | 549 |
| `backend-health/src/main/java/com/health/dto/ApiResponse.java` | 523 |
| `backend-health/src/main/java/com/health/vo/ArticleVO.java` | 505 |
| `ai_service/utils/cache_utils.py` | 447 |
| `backend-health/src/main/java/com/health/controller/AdminController.java` | 336 |
| `backend-health/src/main/java/com/health/entity/Food.java` | 328 |
| `backend-health/src/main/java/com/health/entity/User.java` | 308 |
| `backend-health/src/main/java/com/health/vo/RecipeVO.java` | 300 |
| `frontend-health/src/api/index.ts` | 283 |
| `backend-health/src/main/java/com/health/service/RecipeService.java` | 281 |
| `backend-health/src/main/java/com/health/vo/UserProfileVO.java` | 271 |
| `backend-health/src/main/java/com/health/entity/NutritionReport.java` | 265 |
| `backend-health/src/main/java/com/health/dto/FoodDTO.java` | 237 |
| `ai_service/utils/log_config.py` | 225 |

## 6. 关键调用关系示例

以下为部分核心调用链（Controller/Service 层）：

```
Start-Ollama  -->  Test-PortListen   [CALLS]
Start-Ollama  -->  Wait-Port   [CALLS]
Start-AIService  -->  Test-PortListen   [CALLS]
Start-AIService  -->  Wait-Port   [CALLS]
Start-Backend  -->  Test-PortListen   [CALLS]
Start-Backend  -->  Wait-Port   [CALLS]
Start-Frontend  -->  Test-PortListen   [CALLS]
Start-Frontend  -->  Wait-Port   [CALLS]
Check-Offline  -->  Test-PortListen   [CALLS]
parseBlocks  -->  length   [CALLS]
splitMotherDraft  -->  normalizeMarkers   [CALLS]
splitMotherDraft  -->  parseBlocks   [CALLS]
splitMotherDraft  -->  SplitResult   [CALLS]
splitMotherDraft  -->  cleanTemplateLines   [CALLS]
splitMotherDraft  -->  joinNonEmpty   [CALLS]
splitMotherDraft  -->  cleanShortContent   [CALLS]
splitMotherDraft  -->  parseMeta   [CALLS]
splitMotherDraft  -->  parseRefs   [CALLS]
validate  -->  countChinese   [CALLS]
validate  -->  size   [CALLS]
validate  -->  ValidationResult   [CALLS]
joinNonEmpty  -->  length   [CALLS]
joinNonEmpty  -->  append   [CALLS]
addRelation  -->  info   [CALLS]
addRelation  -->  findByUsername   [CALLS]
addRelation  -->  getUserId   [CALLS]
addRelation  -->  findByGuardianIdAndWardId   [CALLS]
addRelation  -->  getStatus   [CALLS]
addRelation  -->  getStatus   [CALLS]
addRelation  -->  setStatus   [CALLS]
```

> 完整图谱数据见 `cbm-graph.json`（节点 + 全部边）。
