-- ============================================================
-- SC-003 建表 SQL 基线（init-schema.sql）
-- 记录：SQL建表演进报告.md → 四、持续优化记录 → SC-003
-- 来源：由 health.db 的 sqlite_master 自动导出（2026-08-09）
-- 定位：阶段二交付物，冻结期切换 ddl-auto: none 后用于幂等建表
-- 注意：Hibernate 后续新增字段时需同步更新本文件
-- ============================================================

-- ------------------------------------------------------------
-- INDEX : idx_ai_conv_user
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_ai_conv_user ON ai_conversation_record(user_id);

-- ------------------------------------------------------------
-- INDEX : idx_article_status_created
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_article_status_created ON article(status, created_at);

-- ------------------------------------------------------------
-- INDEX : idx_article_topic_group
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_article_topic_group ON article(topic_group_id);

-- ------------------------------------------------------------
-- INDEX : idx_article_topic_status
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_article_topic_status ON article(topic, status);

-- ------------------------------------------------------------
-- INDEX : idx_bmh_user_date
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_bmh_user_date ON body_metrics_history(user_id, record_date);

-- ------------------------------------------------------------
-- INDEX : idx_comment_post
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_comment_post ON comment(post_id);

-- ------------------------------------------------------------
-- INDEX : idx_diet_item_meal
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_diet_item_meal ON diet_item(meal_id);

-- ------------------------------------------------------------
-- INDEX : idx_diet_meal_date
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_diet_meal_date ON diet_meal(eat_date);

-- ------------------------------------------------------------
-- INDEX : idx_diet_meal_user_date
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_diet_meal_user_date ON diet_meal(user_id, eat_date);

-- ------------------------------------------------------------
-- INDEX : idx_exercise_user_date
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_exercise_user_date ON exercise_record(user_id, record_date);

-- ------------------------------------------------------------
-- INDEX : idx_family_guardian
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_family_guardian ON family_relation(guardian_id);

-- ------------------------------------------------------------
-- INDEX : idx_family_ward
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_family_ward ON family_relation(ward_id);

-- ------------------------------------------------------------
-- INDEX : idx_food_category
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_food_category ON food(food_category, status);

-- ------------------------------------------------------------
-- INDEX : idx_food_name_status
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_food_name_status ON food(food_name, status);

-- ------------------------------------------------------------
-- INDEX : idx_food_status
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_food_status ON food(status);

-- ------------------------------------------------------------
-- INDEX : idx_nutrition_user_date
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_nutrition_user_date ON nutrition_report(user_id, report_date);

-- ------------------------------------------------------------
-- INDEX : idx_post_like_post
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_post_like_post ON post_like(post_id);

-- ------------------------------------------------------------
-- INDEX : idx_recipe_ing_recipe
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_recipe_ing_recipe ON recipe_ingredients(recipe_id);

-- ------------------------------------------------------------
-- INDEX : idx_recipes_name
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(recipe_name);

-- ------------------------------------------------------------
-- INDEX : idx_recipes_tags
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes(tags);

-- ------------------------------------------------------------
-- INDEX : idx_saved_recipe_user
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_saved_recipe_user ON saved_recipe(user_id);

-- ------------------------------------------------------------
-- TABLE : ai_conversation_record
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_conversation_record (
       id  integer,
        created_at datetime,
        health_snapshot_json TEXT,
        model varchar(255),
        question TEXT,
        reply TEXT,
        user_id integer not null,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : article
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "article" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    topic TEXT,
    topic_group_id TEXT,
    length_type TEXT DEFAULT 'medium',
    content TEXT NOT NULL,
    content_short TEXT,
    content_medium TEXT,
    content_long TEXT,
    summary TEXT,
    summary_short TEXT,
    summary_medium TEXT,
    summary_long TEXT,
    tags TEXT,
    category TEXT,
    audience TEXT,
    word_count INTEGER,
    sources_json TEXT,
    created_at TEXT,
    updated_at TEXT,
    status TEXT DEFAULT 'published',
    source TEXT DEFAULT 'ai',
    quality_score INTEGER,
    has_errors_reported INTEGER DEFAULT 0
, likes_count integer, views_count integer);

-- ------------------------------------------------------------
-- TABLE : article_analysis
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS article_analysis (
       id  integer,
        article_id integer not null,
        created_at datetime,
        issues_json TEXT,
        optimized_content TEXT,
        prompt_version varchar(255),
        quality_score integer,
        status varchar(255),
        suggestions TEXT,
        updated_at datetime,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : body_metrics_history
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS body_metrics_history (
       history_id  integer,
        age integer,
        bmr double precision,
        crowd_type varchar(255),
        height double precision,
        record_date varchar(255) not null,
        user_id integer not null,
        weight double precision,
        primary key (history_id)
    );

-- ------------------------------------------------------------
-- TABLE : comment
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comment (
       id  integer,
        content TEXT not null,
        created_at datetime,
        status varchar(255),
        user_id integer not null,
        username varchar(255),
        post_id integer,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : diet_item
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diet_item (
       item_id  integer,
        eat_weight numeric(19,2) not null,
        food_id integer not null,
        meal_id integer not null,
        primary key (item_id)
    );

-- ------------------------------------------------------------
-- TABLE : diet_meal
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS diet_meal (
       meal_id  integer,
        created_at datetime,
        eat_date varchar(255) not null,
        meal_type varchar(255) not null,
        remark varchar(255),
        user_id integer not null,
        primary key (meal_id)
    );

-- ------------------------------------------------------------
-- TABLE : exercise_record
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exercise_record (
       id  integer,
        calories_burned double precision,
        created_at datetime,
        duration_min integer,
        exercise_type varchar(255) not null,
        note varchar(255),
        record_date date,
        status varchar(255),
        user_id integer not null,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : family_relation
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS family_relation (
       relation_id  integer,
        created_at datetime,
        guardian_id integer not null,
        status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'rejected')),
        ward_id integer not null,
        primary key (relation_id)
    );

-- ------------------------------------------------------------
-- TABLE : food
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food (
       food_id  integer,
        calcium numeric(19,2),
        calorie numeric(19,2),
        carb numeric(19,2),
        dha numeric(19,2),
        diet_fiber numeric(19,2),
        fat numeric(19,2),
        folic_acid numeric(19,2),
        food_category varchar(255) not null,
        food_name varchar(255) not null,
        gi_value numeric(19,2),
        priority INTEGER DEFAULT 0,
        protein numeric(19,2),
        status TEXT DEFAULT 'approved', show_gi INTEGER DEFAULT 0, show_folic_acid INTEGER DEFAULT 0, show_dha INTEGER DEFAULT 0,
        primary key (food_id)
    );

-- ------------------------------------------------------------
-- TABLE : nutrition_report
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS nutrition_report (
       report_id  integer,
        bmr double precision,
        calcium_status varchar(255),
        carb_status varchar(255),
        crowd_type varchar(255),
        dha_status varchar(255),
        diet_fiber_status varchar(255),
        fat_status varchar(255),
        folic_acid_status varchar(255),
        intake_bmr_ratio double precision,
        protein_status varchar(255),
        report_date date not null,
        total_calcium double precision,
        total_calorie double precision,
        total_carb double precision,
        total_dha double precision,
        total_diet_fiber double precision,
        total_fat double precision,
        total_folic_acid double precision,
        total_protein double precision,
        user_age integer,
        user_bmr double precision,
        user_crowd_type varchar(255),
        user_height double precision,
        user_id integer not null,
        user_weight double precision,
        primary key (report_id)
    );

-- ------------------------------------------------------------
-- TABLE : post
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS post (
       id  integer,
        comments_count integer,
        content TEXT not null,
        created_at datetime,
        image_url varchar(255),
        likes_count integer,
        status varchar(255),
        tag varchar(255),
        user_id integer not null,
        username varchar(255),
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : post_like
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS post_like (
       id  integer,
        created_at datetime,
        user_id integer not null,
        post_id integer,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : recipe_ingredients
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recipe_ingredients (
       ingredient_id  integer,
        amount numeric(19,2) not null,
        created_at datetime,
        ingredient_name varchar(255) not null,
        recipe_id integer not null,
        unit varchar(255),
        primary key (ingredient_id)
    );

-- ------------------------------------------------------------
-- TABLE : recipes
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recipes (
       recipe_id  integer,
        calories numeric(19,2),
        carbs numeric(19,2),
        cover_image_url varchar(255),
        created_at datetime,
        created_by integer,
        description varchar(255),
        fat numeric(19,2),
        fiber numeric(19,2),
        protein numeric(19,2),
        recipe_name varchar(255) not null,
        source varchar(255),
        tags varchar(255),
        primary key (recipe_id)
    );

-- ------------------------------------------------------------
-- TABLE : saved_recipe
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS saved_recipe (
       id  integer,
        created_at datetime,
        ingredients TEXT,
        nutrition_summary TEXT,
        persona_tag varchar(255),
        steps TEXT,
        title varchar(255) not null,
        user_id integer not null,
        primary key (id)
    );

-- ------------------------------------------------------------
-- TABLE : user
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user (
       user_id  integer,
        age INTEGER DEFAULT 18 CHECK(age >= 0 AND age <= 150),
        allergic_foods varchar(255),
        created_at datetime,
        crowd_type TEXT DEFAULT '普通人' CHECK(crowd_type IN ('普通人', '健身', '老年', '孕妇', '青少年', '糖尿病')),
        dietary_restrictions varchar(255),
        elderly_mode INTEGER DEFAULT 0 CHECK(elderly_mode IN (0, 1)),
        gender TEXT DEFAULT '男' CHECK(gender IN ('男', '女')),
        height REAL DEFAULT 165 CHECK(height >= 0 AND height <= 300),
        password varchar(255) not null,
        role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin')),
        taste_preference TEXT DEFAULT '清淡' CHECK(taste_preference IN ('清淡', '适中', '重口味', '微辣', '辣')),
        username varchar(255) not null,
        weight REAL DEFAULT 65 CHECK(weight >= 0 AND weight <= 300),
        primary key (user_id)
    );


-- ============================================================
-- SC-001 高频查询索引（合并自 index_optimizations.sql）
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_food_name_status ON food(food_name, status);
CREATE INDEX IF NOT EXISTS idx_food_category ON food(food_category, status);
CREATE INDEX IF NOT EXISTS idx_food_status ON food(status);
CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(recipe_name);
CREATE INDEX IF NOT EXISTS idx_recipes_tags ON recipes(tags);
CREATE INDEX IF NOT EXISTS idx_recipe_ing_recipe ON recipe_ingredients(recipe_id);
CREATE INDEX IF NOT EXISTS idx_article_status_created ON article(status, created_at);
CREATE INDEX IF NOT EXISTS idx_article_topic_group ON article(topic_group_id);
CREATE INDEX IF NOT EXISTS idx_article_topic_status ON article(topic, status);
CREATE INDEX IF NOT EXISTS idx_diet_meal_user_date ON diet_meal(user_id, eat_date);
CREATE INDEX IF NOT EXISTS idx_diet_meal_date ON diet_meal(eat_date);
CREATE INDEX IF NOT EXISTS idx_diet_item_meal ON diet_item(meal_id);
CREATE INDEX IF NOT EXISTS idx_bmh_user_date ON body_metrics_history(user_id, record_date);
CREATE INDEX IF NOT EXISTS idx_exercise_user_date ON exercise_record(user_id, record_date);
CREATE INDEX IF NOT EXISTS idx_nutrition_user_date ON nutrition_report(user_id, report_date);
CREATE INDEX IF NOT EXISTS idx_ai_conv_user ON ai_conversation_record(user_id);
CREATE INDEX IF NOT EXISTS idx_family_guardian ON family_relation(guardian_id);
CREATE INDEX IF NOT EXISTS idx_family_ward ON family_relation(ward_id);
CREATE INDEX IF NOT EXISTS idx_comment_post ON comment(post_id);
CREATE INDEX IF NOT EXISTS idx_post_like_post ON post_like(post_id);
CREATE INDEX IF NOT EXISTS idx_saved_recipe_user ON saved_recipe(user_id);

-- ============================================================
-- SC-002 唯一约束（合并自 unique_constraints.sql）
-- ============================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_username ON user(username);
CREATE UNIQUE INDEX IF NOT EXISTS uq_bmh_user_date ON body_metrics_history(user_id, record_date);
CREATE UNIQUE INDEX IF NOT EXISTS uq_family_guardian_ward ON family_relation(guardian_id, ward_id);
