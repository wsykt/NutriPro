import sqlite3

DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"

CATEGORY_MAPPING = {
    "肉类": "肉蛋类",
    "蛋类": "肉蛋类",
    "肉蛋类": "肉蛋类",
    "主食": "主食",
    "蔬菜": "蔬菜",
    "水果": "水果",
    "豆制品": "豆制品",
    "奶类": "奶类",
    "油脂类": "油脂类",
    "水产": "水产",
    "零食": "零食",
    "饮料": "饮料",
    "其他": "其他",
}

TARGET_CATEGORIES = ['主食', '肉蛋类', '水产', '蔬菜', '水果', '豆制品', '奶类', '油脂类']

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=" * 60)
print("修复食物分类")
print("=" * 60)

cursor.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
print("\n修复前分类分布:")
for cat, cnt in cursor.fetchall():
    print(f"  {cat}: {cnt}")

for old_cat, new_cat in CATEGORY_MAPPING.items():
    if old_cat != new_cat:
        cursor.execute("UPDATE food SET food_category = ? WHERE food_category = ?", (new_cat, old_cat))
        print(f"\n将 '{old_cat}' 转换为 '{new_cat}', 影响 {cursor.rowcount} 条记录")

cursor.execute("DELETE FROM food WHERE food_category NOT IN ('主食', '肉蛋类', '水产', '蔬菜', '水果', '豆制品', '奶类', '油脂类')")
deleted = cursor.rowcount
print(f"\n删除非目标分类记录: {deleted} 条")

conn.commit()

cursor.execute("SELECT food_category, COUNT(*) FROM food GROUP BY food_category ORDER BY COUNT(*) DESC")
print("\n修复后分类分布:")
for cat, cnt in cursor.fetchall():
    print(f"  {cat}: {cnt}")

cursor.execute("SELECT COUNT(*) FROM food")
total = cursor.fetchone()[0]
print(f"\n修复后总记录数: {total}")

conn.close()