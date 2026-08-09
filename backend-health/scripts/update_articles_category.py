import sqlite3

conn = sqlite3.connect(r'c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, category, audience FROM article')
articles = cursor.fetchall()

for article in articles:
    id, title, category, audience = article
    if category != audience:
        cursor.execute('UPDATE article SET category = ? WHERE id = ?', (audience, id))
        print(f'Updated article {id}: {category} -> {audience}')

conn.commit()
print('Done!')

cursor.execute('SELECT DISTINCT category FROM article')
print('Categories:', [c[0] for c in cursor.fetchall()])

cursor.execute('SELECT DISTINCT audience FROM article')
print('Audiences:', [a[0] for a in cursor.fetchall()])

conn.close()