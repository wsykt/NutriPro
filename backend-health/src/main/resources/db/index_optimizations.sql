-- ============================================================
-- SC-001 高频查询补索引（幂等，可重复执行）
-- 记录：SQL建表演进报告.md → 四、持续优化记录 → SC-001
-- 原则：索引名统一前缀 idx_，配合 Hibernate 自动建表（ddl-auto: update）
--       自动建表不生成索引，故用独立脚本维护
-- ============================================================

-- 1. food：食物搜索（searchByName 按名称模糊 + status 过滤）
CREATE INDEX IF NOT EXISTS idx_food_name_status ON food(food_name, status);
-- 2. food：按分类查询（findByCategory）
CREATE INDEX IF NOT EXISTS idx_food_category ON food(food_category, status);
-- 3. food：管理员按状态查询（findByStatus / findAllApproved）
CREATE INDEX IF NOT EXISTS idx_food_status ON food(status);

-- 4. recipes：菜谱名称/标签搜索
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(recipe_name);
CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes(tags);

-- 5. recipe_ingredients：按菜谱查食材
CREATE INDEX IF NOT EXISTS idx_recipe_ing_recipe ON recipe_ingredients(recipe_id);

-- 6. article：科普文章（状态 + 主题分组 + 篇幅 + 创建时间排序）
CREATE INDEX IF NOT EXISTS idx_article_status_created ON article(status, created_at);
CREATE INDEX IF NOT EXISTS idx_article_topic_group ON article(topic_group_id);
CREATE INDEX IF NOT EXISTS idx_article_topic_status ON article(topic, status);

-- 7. diet_meal：用户按日期查餐
CREATE INDEX IF NOT EXISTS idx_diet_meal_user_date ON diet_meal(user_id, eat_date);
CREATE INDEX IF NOT EXISTS idx_diet_meal_date ON diet_meal(eat_date);

-- 8. diet_item：按一餐查明细
CREATE INDEX IF NOT EXISTS idx_diet_item_meal ON diet_item(meal_id);

-- 9. body_metrics_history：用户按日期查历史
CREATE INDEX IF NOT EXISTS idx_bmh_user_date ON body_metrics_history(user_id, record_date);

-- 10. exercise_record：用户按日期查运动
CREATE INDEX IF NOT EXISTS idx_exercise_user_date ON exercise_record(user_id, record_date);

-- 11. nutrition_report：用户按日期查报告
CREATE INDEX IF NOT EXISTS idx_nutrition_user_date ON nutrition_report(user_id, report_date);

-- 12. ai_conversation_record：用户对话记录
CREATE INDEX IF NOT EXISTS idx_ai_conv_user ON ai_conversation_record(user_id);

-- 13. family_relation：监护人/被监护人查询
CREATE INDEX IF NOT EXISTS idx_family_guardian ON family_relation(guardian_id);
CREATE INDEX IF NOT EXISTS idx_family_ward ON family_relation(ward_id);

-- 14. comment：按帖子查评论
CREATE INDEX IF NOT EXISTS idx_comment_post ON comment(post_id);

-- 15. post_like：按帖子查点赞
CREATE INDEX IF NOT EXISTS idx_post_like_post ON post_like(post_id);

-- 16. saved_recipe：用户收藏菜谱
CREATE INDEX IF NOT EXISTS idx_saved_recipe_user ON saved_recipe(user_id);
