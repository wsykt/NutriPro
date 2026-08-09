"""
原始数据存储（知识库独立空间）
============================
为爬虫抓取的全部原始数据开辟独立存储空间，保留：
- 原始文件格式（HTML / JSON）
- 层级结构（按数据源 + 日期分目录）
- 元数据（版本标记、时间戳、来源、校验和）
- 支持后续溯源与数据分析

存储布局：
    knowledge_base/raw_crawled/
        ├── manifest.jsonl          # 全局清单（每条一行，含版本/时间戳/校验和）
        ├── chinanutri/
        │   └── 2026-08-06/
        │       ├── <hash>.html     # 原始 HTML
        │       └── <hash>.meta.json
        ├── off/
        │   └── 2026-08-06/
        │       └── <hash>.json
        └── usda/
            └── 2026-08-06/
                └── <hash>.json

每条原始数据含：
    raw_id      : 唯一 ID（source_key + url hash）
    version     : 版本号（同 URL 重复抓取则版本递增）
    first_seen  : 首次抓取时间戳
    last_seen   : 最近抓取时间戳
    source_url  : 来源 URL
    source_key  : 数据源
    checksum    : 内容 SHA256（用于变更检测）
    raw_format  : 原始格式（html/json）
    raw_path    : 原始文件相对路径
    parsed_item : 解析后的结构化数据（RawFoodItem）
"""

from __future__ import annotations
import os
import json
import hashlib
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__) if False else __import__("logging").getLogger(__name__)

# 存储根目录（知识库独立空间）
AI_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_STORE_ROOT = os.path.join(AI_SERVICE_DIR, "knowledge_base", "raw_crawled")
MANIFEST_PATH = os.path.join(RAW_STORE_ROOT, "manifest.jsonl")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _url_id(source_key: str, url: str) -> str:
    return f"{source_key}_{_sha256(url)[:16]}"


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


class RawStore:
    """原始数据存储：留存全部原始抓取数据，含版本与时间戳"""

    def __init__(self, root: str = RAW_STORE_ROOT):
        self.root = root
        self.manifest_path = os.path.join(root, "manifest.jsonl")
        os.makedirs(root, exist_ok=True)
        self._lock = threading.Lock()
        # 加载已有 manifest 索引到内存（raw_id → record）
        self._index: Dict[str, dict] = {}
        self._load_manifest()

    def _load_manifest(self):
        if not os.path.exists(self.manifest_path):
            return
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    self._index[rec["raw_id"]] = rec
                except (json.JSONDecodeError, KeyError):
                    continue
        logger.info(f"原始库已加载 {len(self._index)} 条历史记录")

    def save(self, source_key: str, source_url: str,
             raw_text: str, parsed_item: dict,
             raw_format: str = "html") -> dict:
        """保存一条原始数据，含版本递增与时间戳

        返回该条记录的 manifest（含 version, first_seen, last_seen, checksum 等）
        """
        raw_id = _url_id(source_key, source_url)
        checksum = _sha256(raw_text)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._lock:
            existing = self._index.get(raw_id)
            if existing:
                # 版本递增：同 URL 重复抓取
                version = existing.get("version", 1) + 1
                first_seen = existing.get("first_seen", now)
                is_changed = existing.get("checksum") != checksum
            else:
                version = 1
                first_seen = now
                is_changed = True

            # 写原始文件（按 数据源/日期 分目录，保留层级结构）
            sub_dir = os.path.join(self.root, source_key, _today())
            os.makedirs(sub_dir, exist_ok=True)
            ext = "json" if raw_format == "json" else "html"
            fname = f"{raw_id}.v{version}.{ext}"
            raw_path = os.path.join(sub_dir, fname)
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(raw_text)

            # 写元数据文件
            meta_path = os.path.join(sub_dir, f"{raw_id}.v{version}.meta.json")
            meta = {
                "raw_id": raw_id,
                "version": version,
                "source_key": source_key,
                "source_url": source_url,
                "first_seen": first_seen,
                "last_seen": now,
                "checksum": checksum,
                "raw_format": raw_format,
                "raw_path": os.path.relpath(raw_path, self.root).replace("\\", "/"),
                "changed_from_prev": is_changed,
                "parsed_item": parsed_item,
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            # 追加到 manifest（jsonl，每条一行）
            with open(self.manifest_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(meta, ensure_ascii=False) + "\n")

            # 更新内存索引（保留最新版本）
            self._index[raw_id] = meta
            logger.info(f"原始数据已保存: {raw_id} v{version} ({source_key})")
            return meta

    def get_latest(self, source_key: str, source_url: str) -> Optional[dict]:
        """获取某 URL 的最新版本记录"""
        return self._index.get(_url_id(source_key, source_url))

    def list_all(self) -> List[dict]:
        """列出全部原始数据记录（最新版本）"""
        return list(self._index.values())

    def stats(self) -> dict:
        """存储统计"""
        records = list(self._index.values())
        by_source: Dict[str, int] = {}
        total_versions = 0
        for r in records:
            by_source[r["source_key"]] = by_source.get(r["source_key"], 0) + 1
            total_versions += r.get("version", 1)
        return {
            "total_records": len(records),
            "total_versions": total_versions,
            "by_source": by_source,
            "store_root": self.root,
        }


# 模块级单例
_raw_store: Optional[RawStore] = None


def get_raw_store() -> RawStore:
    global _raw_store
    if _raw_store is None:
        _raw_store = RawStore()
    return _raw_store
