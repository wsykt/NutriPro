# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect(r'c:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def schema(tbl):
    print('  schema %s:' % tbl)
    for r in cur.execute('PRAGMA table_info(%s)' % tbl).fetchall():
        print('   ', r['name'], r['type'])

print('--- schemas ---')
schema('exercise_record')
schema('body_metrics_history')
print('--- exercise_record (uid=9) sample ---')
for r in cur.execute('SELECT * FROM exercise_record WHERE user_id=9 ORDER BY record_date LIMIT 6').fetchall():
    print(' ', dict(r))
print('--- body_metrics_history (uid=9) sample ---')
for r in cur.execute('SELECT * FROM body_metrics_history WHERE user_id=9 ORDER BY record_date LIMIT 4').fetchall():
    print(' ', dict(r))
print('--- count ---')
print('ex uid9:', cur.execute('SELECT COUNT(*) FROM exercise_record WHERE user_id=9').fetchone()[0])
print('range check:', cur.execute("SELECT COUNT(*) FROM exercise_record WHERE user_id=9 AND record_date BETWEEN '2026-08-12' AND '2026-08-18'").fetchone()[0])
conn.close()
