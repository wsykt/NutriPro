import sqlite3, os

# Check backend health.db
paths = [
    os.path.join("..", "backend-health", "data", "health.db"),
    os.path.join("..", "..", "backend-health", "data", "health.db"),
]
for p in paths:
    full = os.path.abspath(p)
    print("Checking:", full)
    print("Exists:", os.path.exists(full))
    if os.path.exists(full):
        print("Size:", os.path.getsize(full))
        conn = sqlite3.connect(full)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", tables)
        if "food" in tables:
            cur.execute("SELECT COUNT(*) FROM food")
            print("Food rows:", cur.fetchone()[0])
        conn.close()
        break
