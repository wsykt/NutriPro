-- ============================================================
-- SC-002 补唯一约束（幂等，可重复执行）
-- 记录：SQL建表演进报告.md → 四、持续优化记录 → SC-002
-- 说明：SQLite 不支持 ALTER TABLE ADD CONSTRAINT，统一用
--       CREATE UNIQUE INDEX 实现唯一性（等价于 UNIQUE 约束）
-- 已确认：health.db 当前数据无重复，可直接建唯一索引
-- ============================================================

-- 1. user.username 唯一（登录名不可重复）
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_username ON user(username);

-- 2. body_metrics_history(user_id, record_date) 唯一（同一用户同一天仅一条身体指标）
CREATE UNIQUE INDEX IF NOT EXISTS uq_bmh_user_date ON body_metrics_history(user_id, record_date);

-- 3. family_relation(guardian_id, ward_id) 唯一（一对监护关系只允许一条）
CREATE UNIQUE INDEX IF NOT EXISTS uq_family_guardian_ward ON family_relation(guardian_id, ward_id);
