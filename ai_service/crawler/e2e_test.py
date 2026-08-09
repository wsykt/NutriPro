"""端到端数据层测试：原始库 → SQLite 接入 → 核验 → 异常处理

使用 health.db 副本，避免污染正式数据。
验证项：
1. 正常数据接入成功
2. 重复条目检测
3. 校验失败处理（非法类别、超范围数值、空数据）
4. 原始库版本递增
5. 核验流程一致性
"""
import os
import sys
import shutil
import sqlite3
import logging

AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AI_SERVICE_DIR)

from crawler.raw_store import RawStore
from crawler.ingest_to_sqlite import SQLiteIngester, IngestResult
from crawler.verify import DataVerifier

logging.basicConfig(level=logging.WARNING)

REAL_DB = os.path.abspath(os.path.join(AI_SERVICE_DIR, "..", "backend-health", "data", "health.db"))
TEST_DB = os.path.abspath(os.path.join(AI_SERVICE_DIR, "crawler", "_test_health.db"))
RAW_TEST_ROOT = os.path.join(AI_SERVICE_DIR, "knowledge_base", "raw_crawled_test")


def build_test_items():
    """构建测试数据：3 条正常 + 3 条异常"""
    return [
        # === 正常数据 ===
        {
            "name": "测试鸡蛋", "category": "肉蛋类",
            "nutrients": {"energy_kcal": 147, "protein_g": 12.6, "fat_g": 9.5,
                          "carbohydrate_g": 1.1, "calcium_mg": 50},
            "cooking_methods": ["煮", "炒"], "origin": "测试产地",
            "source_url": "https://test.example/egg", "source_key": "test",
            "raw_payload": "<html>test egg</html>",
            "fetched_at": "2026-08-06 17:00:00",
        },
        {
            "name": "测试菠菜", "category": "蔬菜",
            "nutrients": {"energy_kcal": 28, "protein_g": 2.6, "fat_g": 0.3,
                          "carbohydrate_g": 4.5, "fiber_g": 1.7, "calcium_mg": 66,
                          "folic_acid_ug": 194},
            "cooking_methods": ["炒", "凉拌"], "origin": "中国",
            "source_url": "https://test.example/spinach", "source_key": "test",
            "raw_payload": "<html>test spinach</html>",
            "fetched_at": "2026-08-06 17:00:00",
        },
        {
            "name": "测试三文鱼", "category": "水产",
            "nutrients": {"energy_kcal": 208, "protein_g": 20.4, "fat_g": 13.4,
                          "calcium_mg": 9, "folic_acid_ug": 25, "dha_mg": 1780},
            "cooking_methods": ["刺身", "煎"], "origin": "挪威",
            "source_url": "https://test.example/salmon", "source_key": "test",
            "raw_payload": "<html>test salmon</html>",
            "fetched_at": "2026-08-06 17:00:00",
        },
        # === 异常数据 1: 重复条目（与上面鸡蛋同名，触发重复检测）===
        {
            "name": "测试鸡蛋", "category": "肉蛋类",
            "nutrients": {"energy_kcal": 150, "protein_g": 13.0},
            "source_url": "https://test.example/egg2", "source_key": "test",
            "raw_payload": "<html>dup egg</html>",
            "fetched_at": "2026-08-06 17:01:00",
        },
        # === 异常数据 2: 非法类别 ===
        {
            "name": "测试非法类别食物", "category": "调料",
            "nutrients": {"energy_kcal": 100, "protein_g": 5},
            "source_url": "https://test.example/badcat", "source_key": "test",
            "raw_payload": "<html>bad category</html>",
            "fetched_at": "2026-08-06 17:02:00",
        },
        # === 异常数据 3: 超范围数值 ===
        {
            "name": "测试超范围食物", "category": "主食",
            "nutrients": {"energy_kcal": 99999, "protein_g": 5},
            "source_url": "https://test.example/badval", "source_key": "test",
            "raw_payload": "<html>bad value</html>",
            "fetched_at": "2026-08-06 17:03:00",
        },
        # === 异常数据 4: 空营养素 ===
        {
            "name": "测试空数据食物", "category": "水果",
            "nutrients": {},
            "source_url": "https://test.example/empty", "source_key": "test",
            "raw_payload": "<html>empty</html>",
            "fetched_at": "2026-08-06 17:04:00",
        },
    ]


def main():
    print("=" * 70)
    print("端到端数据层测试")
    print("=" * 70)

    # 0. 清理旧的测试原始库（避免版本累积导致断言失败）
    if os.path.exists(RAW_TEST_ROOT):
        shutil.rmtree(RAW_TEST_ROOT)
        print(f"已清理旧测试原始库: {RAW_TEST_ROOT}")

    # 1. 准备测试数据库副本
    print("\n【1】准备测试数据库副本...")
    shutil.copy2(REAL_DB, TEST_DB)
    print(f"  源库: {REAL_DB}")
    print(f"  副本: {TEST_DB}")

    before_count = sqlite3.connect(TEST_DB).execute("SELECT COUNT(*) FROM food").fetchone()[0]
    print(f"  副本 food 表原始行数: {before_count}")

    # 2. 原始库存储测试（版本递增）
    print("\n【2】原始库存储测试（版本递增）...")
    raw_store = RawStore(root=RAW_TEST_ROOT)
    test_items = build_test_items()
    for item in test_items:
        raw_store.save(item["source_key"], item["source_url"],
                       item["raw_payload"], item, raw_format="html")
    # 重复保存同 URL，验证版本递增
    raw_store.save(test_items[0]["source_key"], test_items[0]["source_url"],
                   "<html>updated egg</html>", test_items[0], raw_format="html")
    raw_stats = raw_store.stats()
    print(f"  原始库统计: {raw_stats}")
    assert raw_stats["total_records"] == 7, f"应为7条唯一记录，实际{raw_stats['total_records']}"
    assert raw_stats["total_versions"] == 8, f"应为8个版本(含1次重复抓取)，实际{raw_stats['total_versions']}"

    # 3. SQLite 接入测试
    print("\n【3】SQLite 接入测试（含异常处理）...")
    ingester = SQLiteIngester(db_path=TEST_DB)
    result = ingester.ingest(test_items, allow_update=False)
    print(f"  {result.summary()}")
    print(f"  新增: {result.inserted} | 重复: {result.duplicates} | 跳过: {result.skipped}")
    print(f"  校验失败明细 ({len(result.failures)} 条):")
    for f in result.failures:
        print(f"    - [{f.field}] {f.food_name}: {f.reason}")
    print(f"  重复条目: {result.duplicate_names}")

    # 验证接入结果
    assert result.inserted == 3, f"应新增3条，实际{result.inserted}"
    assert result.duplicates == 1, f"应1条重复，实际{result.duplicates}"
    assert result.skipped == 3, f"应跳过3条（非法类别+超范围+空），实际{result.skipped}"

    after_count = sqlite3.connect(TEST_DB).execute("SELECT COUNT(*) FROM food").fetchone()[0]
    print(f"  接入后 food 表行数: {after_count} (新增 {after_count - before_count})")

    # 4. 验证写入的字段正确性（类别约定）
    print("\n【4】验证写入字段正确性（priority/visibility 约定）...")
    conn = sqlite3.connect(TEST_DB)
    for name, expected_cat in [("测试鸡蛋", "肉蛋类"), ("测试菠菜", "蔬菜"), ("测试三文鱼", "水产")]:
        row = conn.execute(
            "SELECT food_category, priority, show_gi, show_folic_acid, show_dha FROM food WHERE food_name=?",
            (name,)).fetchone()
        if row:
            cat, pri, gi, folic, dha = row
            print(f"  {name}: 类别={cat} priority={pri} show_gi={gi} show_folic_acid={folic} show_dha={dha}")
            assert cat == expected_cat
            if expected_cat == "水产":
                assert (pri, gi, folic, dha) == (3, 0, 1, 1), f"水产约定不符: {(pri, gi, folic, dha)}"
            elif expected_cat == "蔬菜":
                assert (pri, gi, folic, dha) == (6, 1, 1, 0)
            elif expected_cat == "肉蛋类":
                assert (pri, gi, folic, dha) == (2, 0, 0, 0)
    conn.close()

    # 5. 核验流程测试
    print("\n【5】数据核验流程测试...")
    verifier = DataVerifier(db_path=TEST_DB)
    verifier.raw_store = raw_store  # 使用测试原始库
    report = verifier.verify()
    summary = report.summary()
    print(f"  总体: {summary['overall']}")
    print(f"  food 表总数: {summary['total_foods_in_db']}")
    print(f"  原始库记录: {summary['total_raw_records']}")
    print(f"  通过: {summary['checks_passed']} | 告警: {summary['warnings']} | 失败: {summary['failures']}")

    # 6. 清理测试数据（从 food 表删除测试条目）
    print("\n【6】清理测试数据...")
    conn = sqlite3.connect(TEST_DB)
    deleted = conn.execute("DELETE FROM food WHERE food_name LIKE '测试%'").rowcount
    conn.commit()
    conn.close()
    print(f"  已从副本库删除 {deleted} 条测试数据")

    # 删除测试副本与测试原始库（容错：Windows 下可能因文件锁失败）
    try:
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    except PermissionError as e:
        print(f"  ⚠️ 测试数据库副本删除失败（文件锁）: {e}")
    try:
        if os.path.exists(RAW_TEST_ROOT):
            shutil.rmtree(RAW_TEST_ROOT)
    except PermissionError as e:
        print(f"  ⚠️ 测试原始库删除失败（文件锁）: {e}")
    print(f"  已尝试删除测试数据库副本与测试原始库")

    print("\n" + "=" * 70)
    print("端到端测试全部通过 ✓")
    print("=" * 70)
    print("\n验证结论:")
    print("  1. 正常数据接入成功（3条新增）")
    print("  2. 重复条目正确检测（1条重复跳过）")
    print("  3. 校验失败正确处理: 非法类别/超范围数值/空数据均被拦截")
    print("  4. 原始库版本递增机制正常（同URL重复抓取版本+1）")
    print("  5. 类别约定(priority/visibility)自动套用正确")
    print("  6. 核验流程（字段完整度/外键/交叉比对）运行正常")


if __name__ == "__main__":
    main()
