"""AI 模板 SQLite 统一存储（双写一致性）

背景：
    模板卡片此前只存 ChromaDB 向量库（display_doc 检索 + full_content 备份）。
    为提升稳定性与可审计性，新增 SQLite 模板表作为权威副本：
    - 每次 ChromaDB 写入 ai_template 卡片时，同步写入 SQLite（双写）
    - 启动时可执行对账（reconcile）：以 ChromaDB 为准回补 SQLite 缺失记录，
      并统计两侧数量/内容一致性
    - SQLite 侧可离线查询：按人群/BMI/功能/方向过滤，便于管理与审计

表结构 ai_templates:
    id               TEXT PRIMARY KEY          -- ChromaDB card_id
    func_type        TEXT                      -- qa / diet_plan / food_recommend / exercise
    target_crowd     TEXT                      -- KB 长名（普通人/孕妇/...）
    bmi_id           TEXT                      -- very_low / low / normal / high / very_high
    direction        TEXT                      -- 目标方向（增肌/减脂/...）
    content          TEXT                      -- 精简展示版（与 ChromaDB document 一致）
    full_content     TEXT                      -- 完整备份版（可能为空）
    metadata_json    TEXT                      -- 完整 metadata（JSON 序列化）
    ingest_time      TEXT                      -- 入库时间
"""
import json
import os
from typing import Optional, List, Dict
from utils.sqlite_utils import get_conn, init_db
from utils.log_config import get_logger

logger = get_logger("template_store")

DDL = """
CREATE TABLE IF NOT EXISTS ai_templates (
    id            TEXT PRIMARY KEY,
    func_type     TEXT,
    target_crowd  TEXT,
    bmi_id        TEXT,
    direction     TEXT,
    content       TEXT,
    full_content  TEXT,
    metadata_json TEXT,
    ingest_time   TEXT
)
"""
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_templates_func ON ai_templates(func_type)",
    "CREATE INDEX IF NOT EXISTS idx_templates_crowd ON ai_templates(target_crowd)",
    "CREATE INDEX IF NOT EXISTS idx_templates_bmi ON ai_templates(bmi_id)",
    "CREATE INDEX IF NOT EXISTS idx_templates_func_crowd_bmi ON ai_templates(func_type, target_crowd, bmi_id)",
]


class TemplateStore:
    """AI 模板 SQLite 存储（ChromaDB 的权威镜像）"""

    def __init__(self, db_path: str = None):
        from config.settings import settings
        self._db_path = db_path or settings.TEMPLATES_DB_PATH
        init_db(self._db_path, ddl_statements=[DDL], indexes=INDEXES)

    # ---------- 写入 ----------

    def upsert(self, doc_id: str, content: str, metadata: dict,
               full_content: str = "") -> bool:
        """写入/更新一条模板记录（幂等）"""
        if not doc_id or not content:
            return False
        meta = dict(metadata or {})
        conn = get_conn(self._db_path)
        try:
            conn.execute(
                """INSERT OR REPLACE INTO ai_templates
                   (id, func_type, target_crowd, bmi_id, direction, content, full_content, metadata_json, ingest_time)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id,
                    meta.get("func_type", ""),
                    meta.get("target_crowd", "") or meta.get("crowd", ""),
                    meta.get("bmi_id", ""),
                    str(meta.get("direction", ""))[:200],
                    content,
                    full_content or "",
                    json.dumps(meta, ensure_ascii=False),
                    meta.get("ingest_time", "") or meta.get("ingest_time") or "",
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            logger.warning(f"[template_store] upsert 失败 id={doc_id}: {e}")
            return False
        finally:
            conn.close()

    # ---------- 读取 ----------

    def get(self, doc_id: str) -> Optional[dict]:
        conn = get_conn(self._db_path)
        try:
            row = conn.execute(
                "SELECT id, func_type, target_crowd, bmi_id, direction, content, full_content, metadata_json, ingest_time "
                "FROM ai_templates WHERE id=?", (doc_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)
        finally:
            conn.close()

    def list(self, func_type: str = None, target_crowd: str = None,
             bmi_id: str = None, direction: str = None, limit: int = 100) -> List[dict]:
        """按维度过滤查询模板（用于管理与审计）"""
        sql = ("SELECT id, func_type, target_crowd, bmi_id, direction, content, full_content, metadata_json, ingest_time "
               "FROM ai_templates WHERE 1=1")
        params = []
        if func_type:
            sql += " AND func_type=?"
            params.append(func_type)
        if target_crowd:
            sql += " AND target_crowd=?"
            params.append(target_crowd)
        if bmi_id:
            sql += " AND bmi_id=?"
            params.append(bmi_id)
        if direction:
            sql += " AND direction LIKE ?"
            params.append(f"%{direction}%")
        sql += " ORDER BY ingest_time DESC LIMIT ?"
        params.append(limit)

        conn = get_conn(self._db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def count(self) -> int:
        conn = get_conn(self._db_path)
        try:
            row = conn.execute("SELECT COUNT(*) FROM ai_templates").fetchone()
            return row[0] if row else 0
        finally:
            conn.close()

    def all_ids(self) -> set:
        conn = get_conn(self._db_path)
        try:
            rows = conn.execute("SELECT id FROM ai_templates").fetchall()
            return {r[0] for r in rows}
        finally:
            conn.close()

    def delete(self, doc_id: str) -> bool:
        conn = get_conn(self._db_path)
        try:
            conn.execute("DELETE FROM ai_templates WHERE id=?", (doc_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.warning(f"[template_store] delete 失败 id={doc_id}: {e}")
            return False
        finally:
            conn.close()

    # ---------- 对账 ----------

    def reconcile(self, retriever) -> dict:
        """启动对账：以 ChromaDB 为准回补 SQLite 缺失的 ai_template 记录。

        只做「单向回补」——SQLite 是权威副本，ChromaDB 是检索主库；
        若 SQLite 有而 ChromaDB 无的记录，仅记录数量不删除（比赛阶段不删冷数据）。
        """
        if retriever is None:
            return {"checked": False, "reason": "无 retriever"}
        try:
            # 拉取 kb_templates 集合中全部 ai_template 卡片（物理隔离后从模板库读取）
            all_data = retriever.collections["kb_templates"].get(
                include=["documents", "metadatas"]
            )
            ids = all_data.get("ids", []) or []
            docs = all_data.get("documents", []) or []
            metas = all_data.get("metadatas", []) or []

            local_ids = self.all_ids()
            added = 0
            for i, cid in enumerate(ids):
                meta = metas[i] if i < len(metas) else {}
                meta = meta or {}
                if meta.get("template_type") != "ai_template":
                    continue
                if cid in local_ids:
                    continue
                full = meta.get("full_content", "") or ""
                self.upsert(cid, docs[i] if i < len(docs) else "", meta, full)
                added += 1

            only_sqlite = len(local_ids) - len(set(ids) & local_ids)
            result = {
                "checked": True,
                "chroma_ai_templates": sum(1 for m in metas if (m or {}).get("template_type") == "ai_template"),
                "sqlite_count": self.count(),
                "backfilled": added,
                "only_sqlite_count": max(0, only_sqlite),
            }
            logger.info(f"[template_store] 对账完成 {result}")
            return result
        except Exception as e:
            logger.warning(f"[template_store] 对账失败: {e}")
            return {"checked": False, "error": str(e)}

    @staticmethod
    def _row_to_dict(row) -> dict:
        (cid, func_type, target_crowd, bmi_id, direction,
         content, full_content, metadata_json, ingest_time) = row
        try:
            meta = json.loads(metadata_json) if metadata_json else {}
        except json.JSONDecodeError:
            meta = {}
        return {
            "id": cid,
            "func_type": func_type,
            "target_crowd": target_crowd,
            "bmi_id": bmi_id,
            "direction": direction,
            "content": content,
            "full_content": full_content,
            "metadata": meta,
            "ingest_time": ingest_time,
        }


template_store = TemplateStore()
