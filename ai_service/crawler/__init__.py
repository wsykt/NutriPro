"""食材数据网页爬虫系统

三档速度 · 合规人道采集 · 多源 · 原始库留存 · SQLite 接入 · 数据核验

模块:
    config            三档速度配置 / 合规配置 / 数据源 / food 表字段规则
    compliance        robots / UA 轮换 / 限速器 / HTTP 抓取器
    parsers           多源数据解析器（chinanutri / off / usda）
    raw_store         原始数据存储（知识库独立空间，版本+时间戳）
    ingest_to_sqlite  数据接入模块（清洗→格式化→写 SQLite food 表）
    verify            数据核验流程（字段/外键/交叉比对）
    benchmark         三档速度系统化测试与对比报告
    food_crawler      主调度器 & CLI 入口
"""
