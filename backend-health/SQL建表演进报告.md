# SQL 建表演进报告（Backend Schema 演进记录）

> 版本：v1.0
> 日期：2026-08-08
> 定位：本报告记录「个人健康助手」Spring Boot 后端数据库建表方式的**持续演进过程**。
> 当前阶段：**继续保持自动建表（`ddl-auto: update`）**，逐步补齐优化，最终过渡到**手动 SQL 建表**。

---

## 一、决策背景

### 1.1 现状

当前后端使用 **Hibernate + SQLite**，`application.yml` 配置：

```yaml
spring:
  jpa:
    database-platform: org.sqlite.hibernate.dialect.SQLiteDialect
    hibernate:
      ddl-auto: update
    show-sql: true
```

即：**实体类（JPA 注解）→ 应用启动时 Hibernate 自动比对/创建/更新表结构**。开发期新增字段、新增表，重启即生效，迭代速度最快。

### 1.2 决策：现阶段不切换手动建表

| 考量 | 说明 |
|------|------|
| 开发效率 | 自动建表免去写建表 SQL 与实体同步维护，字段迭代即时生效 |
| 数据库单一 | 项目固定 SQLite，无 MySQL/PostgreSQL 多方言一致性问题 |
| 数据量级 | 单机演示 + 竞赛场景，`update` 模式不会清空数据（非 `create`） |
| Token 预算 | 手动建表 SQL 与实体长期双维护，成本高；现阶段收益不明显 |

**结论**：继续采用 `ddl-auto: update`，但建立「演进记录 + 逐项优化」机制，为最终切换到手动 SQL 建表铺路。

### 1.3 最终目标（远期）

当项目进入**交付冻结期**后，将 `ddl-auto` 切换为 `none` + 手动 SQL 脚本（幂等建表 + 索引 + 约束），实现：
- 表结构**版本可控、可审计、可回滚**
- 索引、约束、外键**显式声明**（自动建表不生成自定义索引/外键）
- 多环境（开发/演示/局域网）表结构完全一致

---

## 二、现有表结构基线（2026-08-08 实测）

> 以下为 `health.db` 中由 Hibernate 自动生成的实际表结构（17 张表）。

| # | 表名 | 用途 | 主键 |
|:-:|------|------|------|
| 1 | `user` | 用户信息（含人群/角色/口味约束） | user_id |
| 2 | `food` | 食物营养库（9 大类营养素） | food_id |
| 3 | `recipes` | 菜谱（营养总量 + 健康标签） | recipe_id |
| 4 | `recipe_ingredients` | 菜谱食材明细 | ingredient_id |
| 5 | `diet_meal` | 一餐记录 | meal_id |
| 6 | `diet_item` | 一餐内食物明细 | item_id |
| 7 | `nutrition_report` | 营养报告（BMR/宏量/微量状态） | report_id |
| 8 | `body_metrics_history` | 身体指标历史 | history_id |
| 9 | `exercise_record` | 运动记录 | id |
| 10 | `article` | 科普文章（三文稿冗余字段） | id |
| 11 | `article_analysis` | 文章质量分析 | id |
| 12 | `ai_conversation_record` | AI 咨询记录 | id |
| 13 | `post` | 社区帖子 | id |
| 14 | `comment` | 帖子评论 | id |
| 15 | `post_like` | 帖子点赞 | id |
| 16 | `saved_recipe` | 用户收藏菜谱 | id |
| 17 | `family_relation` | 亲友监护关系 | relation_id |

### 2.1 已生效的约束（自动建表保留）

- `user`：gender/height/weight/age/crowd_type/role/taste_preference/elderly_mode 的 **CHECK 约束 + 默认值**（`columnDefinition` 生效）
- `family_relation`：status CHECK（pending/confirmed/rejected）
- `food`：status/priority/show_gi/show_folic_acid/show_dha 默认值
- `post`/`comment`/`exercise_record`：status 默认 'pending'

### 2.2 自动建表的已知短板（后续优化点）

| 短板 | 表现 | 影响 |
|------|------|------|
| 无自定义索引 | 除主键外无索引（如 food.food_name、article.topic_group_id、diet_meal.user_id+eat_date） | 高频查询全表扫描，量大时变慢 |
| 无外键约束 | 实体 `@JoinColumn` 未生成物理外键 | 数据完整性依赖代码保证 |
| 唯一约束缺失 | `user.username`、`body_metrics_history(user_id,record_date)`、`family_relation(guardian_id,ward_id)` 的 unique 未落库 | 重复数据风险 |
| 类型与方言 | `created_at` 为 datetime；部分 TEXT 字段自动建表后无长度限制 | 兼容性可，但不可控 |
| 时间戳格式 | SQLite 时间戳由 Hibernate 写为 `2026-07-27 17:58:24`（空格分隔无毫秒） | 已有教训：带 T/毫秒会解析失败，须保持此格式 |

---

## 三、演进路线（分阶段）

```
阶段一（当前）  自动建表 ddl-auto: update
   ↓ 持续迭代：补索引补约束补唯一 → 通过演进脚本记录
阶段二（过渡）  生成幂等建表 SQL 基线（init-schema.sql）
   ↓ 以实测库结构为基准，逐表核对实体，补齐 2.2 短板
阶段三（冻结）  切换 ddl-auto: none + 手动 SQL + 启动校验
   ↓ 结构版本化、可审计、多环境一致
阶段四（可选）  引入 Flyway 管理迁移版本
```

### 3.1 阶段二产物（远期交付物）

预期在 `backend-health/src/main/resources/db/` 生成：
- `init-schema.sql`：17 张表完整 DDL（含索引、唯一约束、CHECK、默认值）
- `init-data.sql`：必要的基础数据（管理员账号、初始食物/菜谱等，可选）
- 启动时通过 `@PostConstruct` 或 Flyway 幂等执行，`ddl-auto` 切为 `none`

---

## 四、持续优化记录（每次改动在此登记）

> 当前阶段为「自动建表 + 演进脚本」。每完成一项优化，在下方追加一条记录。

| 日期 | 编号 | 优化内容 | 方式 | 状态 |
|------|:----:|----------|------|:----:|
| 2026-08-08 | SC-000 | 建立本演进报告，记录建表方式决策与基线 | 文档 | ✅ |
| 2026-08-09 | SC-001 | 为高频查询补索引：food(food_name)、food(food_category)、recipes(tags)、article(topic_group_id)、diet_meal(user_id,eat_date) 等 21 条 | 自动建表 + 演进脚本 | ✅ |
| 2026-08-09 | SC-002 | 补唯一约束：user(username)、body_metrics_history(user_id,record_date)、family_relation(guardian_id,ward_id) | 演进脚本 | ✅ |
| 2026-08-09 | SC-003 | 生成 init-schema.sql 基线（17 表 DDL + 索引 + 约束，幂等） | 手动 SQL | ✅ |
| 2026-08-09 | SC-004 | 切换 ddl-auto: none，启动幂等执行建表脚本 | 决策 | ⚠️ 暂缓（见评估） |
| 2026-08-09 | SC-005 | 补充外键约束评估（社区/菜谱/饮食类表） | 决策 | ✅（结论：保持逻辑外键） |

### SC-001 落地详情（2026-08-09）

- **产物**：`src/main/resources/db/index_optimizations.sql`，21 条幂等 `CREATE INDEX IF NOT EXISTS`，覆盖 food(3)、recipes(2)、recipe_ingredients(1)、article(3)、diet_meal(2)、diet_item(1)、body_metrics_history(1)、exercise_record(1)、nutrition_report(1)、ai_conversation_record(1)、family_relation(2)、comment(1)、post_like(1)、saved_recipe(1)。
- **启动执行机制**：`DataInitializer.java` 注入 `JdbcTemplate`，`run()` 首步通过 Spring `ScriptUtils.executeSqlScript` 执行 classpath 下 `db/index_optimizations.sql`；脚本幂等、失败仅告警不阻断启动。
- **验证**：`spring-boot:run` 启动日志输出 `Schema optimizations applied: db/index_optimizations.sql`；查询 `sqlite_master` 确认 21 个 `idx_%` 索引全部落库。
- **附带修复**：`AiChatServiceTest` 构造参数缺 `ExerciseRecordRepository`（既有编译错误，阻塞 `mvn spring-boot:run` 的 test-compile 阶段），已补 mock 修复。
- **后续索引规划**：随接口演进逐步补充（参考第五节第 4 条）。

### SC-002 落地详情（2026-08-09）

- **产物**：`src/main/resources/db/unique_constraints.sql`，3 条幂等 `CREATE UNIQUE INDEX IF NOT EXISTS`：
  - `uq_user_username ON user(username)`
  - `uq_bmh_user_date ON body_metrics_history(user_id, record_date)`
  - `uq_family_guardian_ward ON family_relation(guardian_id, ward_id)`
- **说明**：SQLite 不支持 `ALTER TABLE ADD CONSTRAINT`，唯一性统一用 `CREATE UNIQUE INDEX` 实现（等价于 UNIQUE 约束）。已先查库确认三组字段当前无重复数据，可安全建立。
- **启动执行机制**：`DataInitializer.applySchemaOptimizations()` 在 SC-001 脚本后追加执行本脚本，幂等、失败仅告警。
- **验证**：`scripts/verify_schema.py` 连库确认 3 个 `uq_%` 唯一索引全部落库，且 `init-schema.sql` 整体二次执行无报错。

### SC-003 落地详情（2026-08-09）

- **产物**：`src/main/resources/db/init-schema.sql`，由 `scripts/export_schema.py` 从 `health.db` 的 `sqlite_master` 自动导出并幂等化（`CREATE TABLE/INDEX/UNIQUE INDEX IF NOT EXISTS`）：
  - 17 张业务表完整 DDL（含 CHECK 约束、默认值，与 Hibernate 自动建表一致）
  - SC-001 的 21 条索引 + SC-002 的 3 条唯一索引（合并为完整基线）
- **定位**：阶段二交付物，冻结期切换 `ddl-auto: none` 后用于幂等建表；也是多环境（开发/演示/局域网）表结构一致的唯一事实来源。
- **注意**：Hibernate 后续新增字段时需同步更新本文件（切换 none 后由本文件兜底）。
- **验证**：`scripts/verify_schema.py` 对现库二次 `executescript` 无报错，表/索引/唯一约束数量全部匹配（17 表 / 21 索引 / 3 唯一）。

### SC-004 评估（2026-08-09，暂缓执行）

- **目标**：`ddl-auto: none` + 启动幂等执行 `init-schema.sql`。
- **现状**：SC-003 已产出可幂等执行的完整基线脚本，技术前提已具备。
- **暂缓原因**：当前处于**功能迭代活跃期**（AI 咨询 SSE、建表演进、测试环境均在本阶段推进），实体字段仍在频繁增改。切换 `none` 后任何新增字段都须手动同步 `init-schema.sql` 与实体两处，开发成本显著上升，且易遗漏导致启动后查询报错。
- **结论**：保持 `ddl-auto: update` 至**交付冻结期**再切换 `none`。届时切换步骤：① 更新 `init-schema.sql` 至与实体一致 → ② `application.yml` 改 `ddl-auto: none` → ③ 启动日志确认 schema 初始化成功 → ④ 全量接口冒烟验证。

### SC-005 评估（2026-08-09，保持逻辑外键）

- **背景**：Hibernate 自动建表不生成物理外键；SQLite 外键默认关闭（`PRAGMA foreign_keys=OFF`），需每次连接开启。
- **涉及关联表**：`diet_item→diet_meal`、`diet_meal→user`、`recipe_ingredients→recipes`、`comment/post_like→post`、`saved_recipe→user/recipes`、`family_relation→user`、`body_metrics_history→user`、`exercise_record→user`、`ai_conversation_record→user`、`nutrition_report→user`。
- **评估结论**：**保持逻辑外键（代码层保证完整性）**。理由：
  1. SQLite 物理外键需连接级开启 `PRAGMA foreign_keys=ON`，Spring/Hikari 需额外配置，且对已有脏数据/演示数据的兼容性风险高；
  2. 应用层已通过 Repository 级联删除 + Service 事务管理保证引用完整性（如删除用户时清理关联数据）；
  3. 竞赛演示场景数据量小，物理外键带来的约束收益有限，反而增加删除/导入脚本的摩擦。
- **可选增强**（不影响当前决策）：在 `init-schema.sql` 中保留外键定义注释，供冻结期按需启用。

---

## 五、备注与约定

1. **时间戳规范**：所有 `created_at/updated_at` 由后端统一写为 `yyyy-MM-dd HH:mm:ss`（空格分隔、无毫秒），与 SQLite + Hibernate 解析兼容（历史教训，严禁带 `T` 或毫秒）。
2. **JSON 字段**：`sources_json`、`issues_json`、`health_snapshot_json`、`nutrition_summary` 等以 TEXT 存储，属性名与 Java 字段严格一致（禁 snake_case 转换）。
3. **表字段约束**：user 表约束以 project_memory 硬约束为准（gender/age/height/weight/crowd_type/role）。
4. **索引规划**（SC-001 参考）：基于接口高频查询梳理，随优化推进逐条补充登记。
5. **回滚预案**：每次结构变更前备份 `health.db`（现有 `.bak` 机制沿用）。

---

## 六、变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-08-08 | v1.0 | 建立报告：记录「继续保持自动建表」决策、17 表基线、自动建表短板、三阶段演进路线 |
