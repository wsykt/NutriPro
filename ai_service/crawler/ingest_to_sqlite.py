"""
数据接入模块：清洗 → 格式转换 → 写入 SQLite food 表
==================================================
严格沿用原有 food 表结构、字段规则、数据类型和关联约束。
- 仅写入 food 表允许的 9 项营养素（多余营养素已在原始库留存）
- 类别 → priority/visibility 约定自动套用
- 名称含生/熟标注（按既有规则）
- 异常处理：数据校验失败、重复条目、外键完整性

food 表结构（实测）:
    food_id (PK auto), food_name, food_category, calorie, protein, fat,
    carb, diet_fiber, calcium, folic_acid, dha, gi_value,
    priority, status, show_gi, show_folic_acid, show_dha
"""

from __future__ import annotations
import os
import re
import sqlite3
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from crawler.config import (
    FOOD_TABLE_NUTRIENTS, VALID_CATEGORIES, CATEGORY_CONVENTION,
    NUTRIENT_BOUNDS, RAW_TO_TABLE_MAP,
)
from utils.sqlite_utils import get_conn

logger = logging.getLogger(__name__)

# SQLite 数据库路径
AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(AI_SERVICE_DIR, "..", "backend-health", "data", "health.db")
DB_PATH = os.path.abspath(DB_PATH)


# ============================================================
# 校验结果
# ============================================================

@dataclass
class ValidationFailure:
    """数据校验失败记录"""
    food_name: str
    reason: str
    field: str = ""
    value: object = None


@dataclass
class IngestResult:
    """接入结果汇总"""
    total: int = 0
    inserted: int = 0
    duplicates: int = 0
    skipped: int = 0
    failures: List[ValidationFailure] = field(default_factory=list)
    duplicate_names: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.inserted + self.duplicates) / self.total

    def summary(self) -> str:
        return (f"接入完成: 共 {self.total} 条 | 新增 {self.inserted} | "
                f"重复 {self.duplicates} | 失败 {len(self.failures)} | 成功率 {self.success_rate:.1%}")


# ============================================================
# 数据清洗
# ============================================================

# 生/熟标注规则：烹饪后水分变化大的食物需标注
COOKED_ANNOTATIONS = {
    # 主食类：米饭/面条煮熟后与生重差异大
    "大米": "米饭(熟)", "稻米": "米饭(熟)",
    "面条": "面条(熟)", "挂面": "面条(熟)",
    "小米": "小米粥(熟)",
    # 肉蛋类
    "鸡蛋": "鸡蛋(生)",
    "猪肉": "猪肉(生)", "牛肉": "牛肉(生)", "鸡肉": "鸡肉(生)",
}


def _normalize_nutrients(raw_nutrients: Dict[str, float]) -> Dict[str, Optional[float]]:
    """将多源原始营养素字段映射到 food 表字段名，仅保留 9 项允许字段"""
    table_nutrients: Dict[str, Optional[float]] = {k: None for k in FOOD_TABLE_NUTRIENTS}
    for raw_key, val in raw_nutrients.items():
        table_key = RAW_TO_TABLE_MAP.get(raw_key)
        if table_key and table_key in table_nutrients:
            # 首次出现的值优先（多源字段冲突时保留首个非空）
            if table_nutrients[table_key] is None:
                num = _to_float(val)
                if num is not None:
                    table_nutrients[table_key] = num
    return table_nutrients


def _to_float(val) -> Optional[float]:
    """安全转 float，None/空/非数返回 None"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if val != val:  # NaN
            return None
        return float(val)
    s = str(val).strip()
    if s in ("", "-", "—", "微量", "Tr", "tr", "ND", "未检出", "N/A"):
        return None
    m = re.search(r"[-+]?\d*\.?\d+", s)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return None
    return None


def _annotate_name(name: str, category: str) -> str:
    """按既有规则为名称添加生/熟标注"""
    if not name:
        return name
    # 已含标注则跳过
    if re.search(r"[\(（](生|熟)[\)）]", name):
        return name
    if category in COOKED_ANNOTATIONS:
        # 仅当名称完全匹配基础名时才标注
        base = COOKED_ANNOTATIONS[category]
        # 反查：若 name 等于某基础名
        for orig, annotated in COOKED_ANNOTATIONS.items():
            if name == orig:
                return annotated
    return name


# ============================================================
# 校验逻辑
# ============================================================

def validate_item(name: str, category: str,
                  nutrients: Dict[str, Optional[float]]) -> Tuple[bool, Optional[ValidationFailure]]:
    """校验单条数据：名称、类别、数值范围

    返回 (是否通过, 失败原因或None)
    """
    # 1. 名称非空
    if not name or not name.strip():
        return False, ValidationFailure(name or "(空)", "名称为空", "food_name", name)

    # 2. 类别合法
    if category not in VALID_CATEGORIES:
        return False, ValidationFailure(name, f"非法类别: {category}", "food_category", category)

    # 3. 至少有 1 项营养素非空（避免空记录入库）
    non_null = {k: v for k, v in nutrients.items() if v is not None}
    if not non_null:
        return False, ValidationFailure(name, "所有营养素均为空", "nutrients", None)

    # 4. 数值范围校验
    for field_name, val in non_null.items():
        if field_name in NUTRIENT_BOUNDS:
            lo, hi = NUTRIENT_BOUNDS[field_name]
            if val < lo or val > hi:
                return False, ValidationFailure(
                    name, f"{field_name}={val} 超出合理范围 [{lo}, {hi}]",
                    field_name, val)

    return True, None


# ============================================================
# SQLite 写入
# ============================================================

class SQLiteIngester:
    """将清洗后的食材数据写入 SQLite food 表"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"数据库不存在: {db_path}")

    def _existing_names(self, conn: sqlite3.Connection) -> set:
        """加载现有 food_name 集合（去重判定）"""
        rows = conn.execute("SELECT food_name FROM food").fetchall()
        return {r[0] for r in rows}

    def ingest(self, raw_items: List[dict], allow_update: bool = False) -> IngestResult:
        """批量接入原始数据

        参数:
            raw_items: RawFoodItem.to_dict() 列表
            allow_update: 是否允许更新已存在条目（默认 False，重复则跳过）
        """
        result = IngestResult(total=len(raw_items))

        # 备份策略：接入前先备份（人道原则，可回滚）
        conn = get_conn(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        existing_names = self._existing_names(conn)

        try:
            for item in raw_items:
                result.total += 0  # 已在初始化时设置
                name_raw = (item.get("name") or "").strip()
                category = item.get("category")
                raw_nutrients = item.get("nutrients", {}) or {}

                # 1. 类别缺失则尝试推断
                if not category:
                    from crawler.parsers import guess_category
                    category = guess_category(name_raw)

                # 2. 营养素标准化
                table_nutrients = _normalize_nutrients(raw_nutrients)

                # 3. 名称生/熟标注
                if category:
                    name = _annotate_name(name_raw, category)
                else:
                    name = name_raw

                # 4. 重复检测（按 food_name）
                if name in existing_names:
                    result.duplicates += 1
                    result.duplicate_names.append(name)
                    if allow_update:
                        # 更新逻辑：仅更新营养素，保留原 priority/status
                        self._update_food(conn, name, category, table_nutrients)
                        existing_names.add(name)
                    continue

                # 5. 校验
                if not category or category not in VALID_CATEGORIES:
                    result.failures.append(ValidationFailure(
                        name, f"类别无法判定或非法: {category}", "food_category", category))
                    result.skipped += 1
                    continue

                ok, fail = validate_item(name, category, table_nutrients)
                if not ok:
                    result.failures.append(fail)
                    result.skipped += 1
                    continue

                # 6. 套用类别约定 priority/visibility
                priority, show_gi, show_folic, show_dha = CATEGORY_CONVENTION[category]

                # 7. 写入（status 默认 approved，沿用既有约定）
                try:
                    conn.execute("""
                        INSERT INTO food (
                            food_name, food_category, calorie, protein, fat, carb,
                            diet_fiber, calcium, folic_acid, dha, gi_value,
                            priority, status, show_gi, show_folic_acid, show_dha
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, ?)
                    """, (
                        name, category,
                        table_nutrients["calorie"], table_nutrients["protein"],
                        table_nutrients["fat"], table_nutrients["carb"],
                        table_nutrients["diet_fiber"], table_nutrients["calcium"],
                        table_nutrients["folic_acid"], table_nutrients["dha"],
                        table_nutrients["gi_value"],
                        priority, show_gi, show_folic, show_dha,
                    ))
                    result.inserted += 1
                    existing_names.add(name)
                except sqlite3.IntegrityError as e:
                    result.failures.append(ValidationFailure(name, f"完整性约束失败: {e}"))
                    result.skipped += 1
                except sqlite3.Error as e:
                    result.failures.append(ValidationFailure(name, f"数据库错误: {e}"))
                    result.skipped += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"接入失败，已回滚: {e}")
            raise
        finally:
            conn.close()

        logger.info(result.summary())
        return result

    def _update_food(self, conn: sqlite3.Connection, name: str,
                     category: str, nutrients: Dict[str, Optional[float]]):
        """更新已存在食物的营养素（保留 priority/status）"""
        try:
            conn.execute("""
                UPDATE food SET
                    calorie=?, protein=?, fat=?, carb=?, diet_fiber=?,
                    calcium=?, folic_acid=?, dha=?, gi_value=?
                WHERE food_name=?
            """, (
                nutrients["calorie"], nutrients["protein"], nutrients["fat"],
                nutrients["carb"], nutrients["diet_fiber"], nutrients["calcium"],
                nutrients["folic_acid"], nutrients["dha"], nutrients["gi_value"],
                name,
            ))
        except sqlite3.Error as e:
            logger.warning(f"更新失败 {name}: {e}")


def ingest_items(raw_items: List[dict], allow_update: bool = False) -> IngestResult:
    """便捷入口"""
    return SQLiteIngester().ingest(raw_items, allow_update=allow_update)
