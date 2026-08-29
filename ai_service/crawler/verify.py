"""
数据核验流程
============
保证存入 SQLite 的数据与知识库原始资料完整、一致。
自动化校验内容：
1. 字段完整度：food 表必填字段非空、类别合法、数值范围
2. 外键引用完整性：recipes/recipe_ingredients 等关联表引用一致性
3. 交叉比对：处理后 SQLite 条目 vs 原始知识库资料的一致性

输出核验报告，含通过/告警/失败明细。
"""

from __future__ import annotations
import os
import sqlite3
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from crawler.config import VALID_CATEGORIES, CATEGORY_CONVENTION, NUTRIENT_BOUNDS, FOOD_TABLE_NUTRIENTS
from crawler.raw_store import get_raw_store
from utils.sqlite_utils import get_conn

logger = logging.getLogger(__name__)

AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.abspath(os.path.join(AI_SERVICE_DIR, "..", "backend-health", "data", "health.db"))


@dataclass
class CheckIssue:
    level: str  # "PASS" / "WARN" / "FAIL"
    category: str
    detail: str
    food_name: str = ""
    food_id: Optional[int] = None


@dataclass
class VerifyReport:
    total_foods: int = 0
    total_raw: int = 0
    passed: int = 0
    warnings: int = 0
    failures: int = 0
    issues: List[CheckIssue] = field(default_factory=list)

    def add(self, issue: CheckIssue):
        self.issues.append(issue)
        if issue.level == "PASS":
            self.passed += 1
        elif issue.level == "WARN":
            self.warnings += 1
        else:
            self.failures += 1

    def summary(self) -> dict:
        return {
            "total_foods_in_db": self.total_foods,
            "total_raw_records": self.total_raw,
            "checks_passed": self.passed,
            "warnings": self.warnings,
            "failures": self.failures,
            "overall": "通过" if self.failures == 0 else "失败",
        }


class DataVerifier:
    """数据核验器"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.raw_store = get_raw_store()

    # ------------------------------------------------------------
    # 1. 字段完整度校验
    # ------------------------------------------------------------
    def check_field_completeness(self, conn: sqlite3.Connection, report: VerifyReport):
        """校验 food 表字段完整度：必填、类别合法、数值范围、visibility 约定"""
        rows = conn.execute("""
            SELECT food_id, food_name, food_category, calorie, protein, fat, carb,
                   diet_fiber, calcium, folic_acid, dha, gi_value,
                   priority, show_gi, show_folic_acid, show_dha
            FROM food
        """).fetchall()

        for r in rows:
            (fid, fname, fcat, calorie, protein, fat, carb, diet_fiber,
             calcium, folic_acid, dha, gi_value,
             priority, show_gi, show_folic, show_dha) = r

            # 必填字段
            if not fname:
                report.add(CheckIssue("FAIL", "字段完整度", "food_name 为空", fname, fid))
            if not fcat:
                report.add(CheckIssue("FAIL", "字段完整度", "food_category 为空", fname, fid))

            # 类别合法
            if fcat and fcat not in VALID_CATEGORIES:
                report.add(CheckIssue("FAIL", "字段完整度",
                                      f"非法类别: {fcat}", fname, fid))

            # 数值范围
            nutrient_vals = {
                "calorie": calorie, "protein": protein, "fat": fat, "carb": carb,
                "diet_fiber": diet_fiber, "calcium": calcium, "folic_acid": folic_acid,
                "dha": dha, "gi_value": gi_value,
            }
            for k, v in nutrient_vals.items():
                if v is not None and k in NUTRIENT_BOUNDS:
                    lo, hi = NUTRIENT_BOUNDS[k]
                    if v < lo or v > hi:
                        report.add(CheckIssue("FAIL", "字段完整度",
                                              f"{k}={v} 超出范围 [{lo},{hi}]", fname, fid))

            # visibility 约定一致性
            if fcat in CATEGORY_CONVENTION:
                exp_p, exp_gi, exp_folic, exp_dha = CATEGORY_CONVENTION[fcat]
                if priority != exp_p:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"priority={priority} 期望={exp_p}", fname, fid))
                if show_gi != exp_gi:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"show_gi={show_gi} 期望={exp_gi}", fname, fid))
                if show_folic != exp_folic:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"show_folic_acid={show_folic} 期望={exp_folic}", fname, fid))
                if show_dha != exp_dha:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"show_dha={show_dha} 期望={exp_dha}", fname, fid))

                # 不该有值的字段应为 None（如肉蛋类不应有 gi_value）
                if exp_gi == 0 and gi_value is not None:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"该类别不应有 gi_value={gi_value}", fname, fid))
                if exp_dha == 0 and dha is not None:
                    report.add(CheckIssue("WARN", "字段完整度",
                                          f"该类别不应有 dha={dha}", fname, fid))

        # 通过项汇总
        report.passed += 1

    # ------------------------------------------------------------
    # 2. 外键引用完整性
    # ------------------------------------------------------------
    def check_referential_integrity(self, conn: sqlite3.Connection, report: VerifyReport):
        """校验关联表外键引用完整性"""
        # recipe_ingredients 引用 recipes.recipe_id
        orphans = conn.execute("""
            SELECT ri.ingredient_id, ri.recipe_id, ri.ingredient_name
            FROM recipe_ingredients ri
            LEFT JOIN recipes r ON ri.recipe_id = r.recipe_id
            WHERE r.recipe_id IS NULL
        """).fetchall()
        for oid, rid, iname in orphans:
            report.add(CheckIssue("FAIL", "外键完整性",
                                  f"recipe_ingredients.{oid} 引用不存在的 recipe_id={rid}", iname))

        # created_by 引用 user
        try:
            orphan_users = conn.execute("""
                SELECT r.recipe_id, r.recipe_name, r.created_by
                FROM recipes r
                LEFT JOIN user u ON r.created_by = u.id
                WHERE r.created_by IS NOT NULL AND u.id IS NULL
            """).fetchall()
            for rid, rname, cb in orphan_users:
                report.add(CheckIssue("WARN", "外键完整性",
                                      f"recipes.{rid} created_by={cb} 无对应用户", rname))
        except sqlite3.Error:
            pass  # user 表结构可能不同

        if not orphans:
            report.passed += 1

    # ------------------------------------------------------------
    # 3. 交叉比对：SQLite 条目 vs 原始知识库
    # ------------------------------------------------------------
    def check_cross_consistency(self, conn: sqlite3.Connection, report: VerifyReport):
        """SQLite food 表 vs 原始库（raw_crawled）交叉比对"""
        raw_records = self.raw_store.list_all()
        report.total_raw = len(raw_records)

        if not raw_records:
            report.add(CheckIssue("WARN", "交叉比对", "原始库无记录，跳过交叉比对"))
            return

        # 加载 SQLite 食物名集合
        db_names = {r[0] for r in conn.execute("SELECT food_name FROM food").fetchall()}

        matched = 0
        mismatched = 0
        for raw in raw_records:
            parsed = raw.get("parsed_item", {}) or {}
            raw_name = parsed.get("name", "")
            if not raw_name:
                continue
            # 在 SQLite 中查找对应条目（允许生/熟标注差异）
            found = any(raw_name in n or n in raw_name for n in db_names)
            if found:
                matched += 1
            else:
                mismatched += 1
                report.add(CheckIssue("WARN", "交叉比对",
                                      f"原始库条目未在 SQLite 中找到: {raw_name}", raw_name))

        consistency = matched / (matched + mismatched) if (matched + mismatched) > 0 else 1.0
        report.add(CheckIssue(
            "PASS" if consistency >= 0.95 else ("WARN" if consistency >= 0.8 else "FAIL"),
            "交叉比对",
            f"原始库 {len(raw_records)} 条，匹配 {matched} 条，"
            f"不一致 {mismatched} 条，一致率 {consistency:.1%}"
        ))

    # ------------------------------------------------------------
    # 总入口
    # ------------------------------------------------------------
    def verify(self) -> VerifyReport:
        report = VerifyReport()
        if not os.path.exists(self.db_path):
            report.add(CheckIssue("FAIL", "环境", f"数据库不存在: {self.db_path}"))
            return report

        conn = get_conn(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            report.total_foods = conn.execute("SELECT COUNT(*) FROM food").fetchone()[0]

            print("【1/3】字段完整度校验...")
            self.check_field_completeness(conn, report)

            print("【2/3】外键引用完整性校验...")
            self.check_referential_integrity(conn, report)

            print("【3/3】SQLite ↔ 原始库交叉比对...")
            self.check_cross_consistency(conn, report)
        finally:
            conn.close()

        return report


def verify_all() -> VerifyReport:
    """核验入口"""
    return DataVerifier().verify()
