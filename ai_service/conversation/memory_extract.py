"""对话记忆提取工具

自动解析对话文本，提取用户健康特征并持久化存储。
解决长期记忆丢失问题：不受 6 条上下文窗口限制，重启后仍保留用户特征。

提取特征：
- 慢病标签：糖尿病、高血压、高血脂等
- 过敏/禁忌：海鲜过敏、乳糖不耐等
- 人群标签：健身、老年、孕妇
- 体重变化记录
- 饮食偏好
"""

import json
import re
import os
import threading
import time
from typing import Optional, List, Dict
from utils.sqlite_utils import get_conn, init_db
from config.settings import settings


# 慢性病关键词表
CHRONIC_DISEASE_KEYWORDS = [
    "糖尿病", "高血压", "高血脂", "高血糖", "脂肪肝", "痛风",
    "甲状腺", "冠心病", "胃炎", "胃溃疡", "肾病", "贫血",
]

# 过敏关键词表
ALLERGY_KEYWORDS = [
    "海鲜过敏", "花生过敏", "牛奶过敏", "乳糖不耐", "鸡蛋过敏",
    "小麦过敏", "大豆过敏", "坚果过敏", "芒果过敏", "花粉过敏",
    "过敏", "不耐受",
]

# 人群标签关键词
CROWD_KEYWORDS = {
    "健身": ["健身", "增肌", "减脂", "撸铁", "力量训练", "有氧"],
    "老年": ["老年", "年纪大", "退休", "六十", "七十", "八十"],
    "孕妇": ["怀孕", "孕期", "孕", "胎", "哺乳", "产妇"],
    "青少年": ["青少年", "学生", "初中", "高中", "青春期"],
    "糖尿病": ["糖尿病", "血糖高", "糖耐量"],
}

# 体重关键词
WEIGHT_KEYWORDS = ["体重", "增重", "减重", "减肥", "长胖", "瘦了"]


class MemoryExtractor:
    """用户长期记忆提取与存储"""

    def __init__(self, db_path: str = None):
        self._db_path = db_path or settings.MEMORY_DB_PATH
        self._init_db()
        self._cache: Dict[int, dict] = {}

    def _init_db(self):
        init_db(
            self._db_path,
            ddl_statements=["""
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id INTEGER PRIMARY KEY,
                    features TEXT NOT NULL DEFAULT '{}',
                    updated_at REAL NOT NULL
                )
            """],
            indexes=[],
        )

    def _load(self, user_id: int) -> dict:
        """从数据库加载用户记忆"""
        if user_id in self._cache:
            return self._cache[user_id]

        conn = get_conn(self._db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT features FROM user_memory WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                features = json.loads(row[0])
            except json.JSONDecodeError:
                features = {}
        else:
            features = {}

        self._cache[user_id] = features
        return features

    def _save(self, user_id: int, features: dict):
        """保存到数据库和缓存"""
        self._cache[user_id] = features
        conn = get_conn(self._db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO user_memory (user_id, features, updated_at) VALUES (?, ?, ?)",
            (user_id, json.dumps(features, ensure_ascii=False), time.time())
        )
        conn.commit()
        conn.close()

    def extract_from_dialogue(self, user_id: int, messages: List[dict]) -> dict:
        """从对话历史中提取用户特征并持久化存储"""
        # 加载已有记忆
        features = self._load(user_id)
        changed = False

        # 遍历对话提取
        for msg in messages:
            content = msg.get("content", "") if isinstance(msg, dict) else str(msg)

            # 慢病检测
            if "features" in content.lower() or any(c in content for c in CHRONIC_DISEASE_KEYWORDS):
                for disease in CHRONIC_DISEASE_KEYWORDS:
                    if disease in content and disease not in features.get("chronic_diseases", []):
                        features.setdefault("chronic_diseases", []).append(disease)
                        changed = True

            # 过敏检测
            for allergy in ALLERGY_KEYWORDS:
                if allergy in content and allergy not in features.get("allergies", []):
                    features.setdefault("allergies", []).append(allergy)
                    changed = True

            # 人群标签检测
            for crowd, keywords in CROWD_KEYWORDS.items():
                if any(kw in content for kw in keywords):
                    existing_crowd = features.get("crowd_type", "")
                    if crowd != existing_crowd and (not existing_crowd or crowd == "糖尿病"):
                        features["crowd_type"] = crowd
                        changed = True

            # 体重记录
            bmi_match = re.search(r'BMI[是为:：]\s*(\d+\.?\d*)', content)
            if bmi_match:
                try:
                    features["last_bmi"] = float(bmi_match.group(1))
                    changed = True
                except ValueError:
                    pass

            weight_match = re.search(r'体重[是为:：]?\s*(\d+\.?\d*)\s*kg', content, re.IGNORECASE)
            if weight_match:
                try:
                    features["last_weight"] = float(weight_match.group(1))
                    changed = True
                except ValueError:
                    pass

        if changed:
            self._save(user_id, features)

        return features

    def get_features(self, user_id: int) -> dict:
        """获取用户记忆特征"""
        return self._load(user_id)

    def add_feature(self, user_id: int, key: str, value):
        """手动添加/更新单条特征"""
        features = self._load(user_id)
        features[key] = value
        self._save(user_id, features)

    def to_context_string(self, user_id: int) -> str:
        """将用户记忆转为上下文文本（给 LLM 使用）"""
        features = self._load(user_id)
        if not features:
            return ""

        parts = ["【用户长期健康记录】"]
        if features.get("chronic_diseases"):
            parts.append(f"慢病：{'、'.join(features['chronic_diseases'])}")
        if features.get("allergies"):
            parts.append(f"过敏/禁忌：{'、'.join(features['allergies'])}")
        if features.get("crowd_type"):
            parts.append(f"人群标签：{features['crowd_type']}")
        if features.get("last_bmi"):
            parts.append(f"最近BMI：{features['last_bmi']}")
        if features.get("last_weight"):
            parts.append(f"最近体重：{features['last_weight']}kg")
        if features.get("dietary_preference"):
            parts.append(f"饮食偏好：{features['dietary_preference']}")

        return "\n".join(parts) if len(parts) > 1 else ""

    def delete_user(self, user_id: int):
        """用户注销时删除全部相关数据"""
        if user_id in self._cache:
            del self._cache[user_id]
        conn = get_conn(self._db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_memory WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()


memory_extractor = MemoryExtractor()
