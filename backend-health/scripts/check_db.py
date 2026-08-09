import sqlite3

conn = sqlite3.connect(r'c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db')
cursor = conn.cursor()

cursor.execute('SELECT id, title, topic, content, summary, tags, category, audience, status FROM article')
all_articles = cursor.fetchall()

for article in all_articles:
    if None in article:
        print('Null found in article:', article)

print('Total articles:', len(all_articles))

cursor.execute('SELECT COUNT(*) FROM article WHERE topic IS NULL')
print('Articles with null topic:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM article WHERE summary IS NULL')
print('Articles with null summary:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM article WHERE tags IS NULL')
print('Articles with null tags:', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM article WHERE category IS NULL')
print('Articles with null category:', cursor.fetchone()[0])

conn.close()