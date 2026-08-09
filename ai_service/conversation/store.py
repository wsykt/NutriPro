import uuid
import os
from utils.sqlite_utils import get_conn, init_db
from config.settings import settings


class ConversationStore:

    def __init__(self):
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        self.db_path = os.path.join(settings.DATA_DIR, "conversations.db")
        self.ensure_table()

    def ensure_table(self):
        init_db(
            self.db_path,
            ddl_statements=["""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    user_id INTEGER,
                    message_role TEXT NOT NULL,
                    message_content TEXT NOT NULL,
                    health_snapshot TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """],
            indexes=[
                "CREATE INDEX IF NOT EXISTS idx_conversations_conv_id ON conversations(conversation_id)",
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
            ],
        )

    def create_conversation(self, user_id: int = 0, conv_id: str = None) -> str:
        if conv_id is None:
            conv_id = str(uuid.uuid4())
        conn = get_conn(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (conversation_id, user_id, message_role, message_content) VALUES (?, ?, ?, ?)",
            (conv_id, user_id, "system", "对话开始")
        )
        conn.commit()
        conn.close()
        return conv_id

    def add_message(self, conversation_id: str, role: str, content: str, health_snapshot: str = ""):
        conn = get_conn(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (conversation_id, user_id, message_role, message_content, health_snapshot) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, 0, role, content, health_snapshot)
        )
        conn.commit()
        conn.close()

    def get_context(self, conversation_id: str, max_messages: int = 6) -> list:
        conn = get_conn(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT message_role, message_content FROM conversations WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
            (conversation_id, max_messages)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"role": row[0], "content": row[1]} for row in reversed(rows)]

    def close_conversation(self, conversation_id: str, status: str = "resolved"):
        conn = get_conn(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (conversation_id, user_id, message_role, message_content) VALUES (?, ?, ?, ?)",
            (conversation_id, 0, "system", f"对话结束，状态：{status}")
        )
        conn.commit()
        conn.close()


store = ConversationStore()