import requests
from urllib.parse import quote

# 测试分类查询
for cat in ["主食", "水果", "奶类", "蔬菜"]:
    r = requests.get(f"http://localhost:8081/api/food/category/{quote(cat)}", timeout=10)
    if r.status_code == 200:
        d = r.json()
        foods = d.get("data", [])
        print(f"\n=== 分类 '{cat}' 前5条 ===")
        for i, f in enumerate(foods[:5]):
            print(f"  {i+1}. {f['foodName']}: {f['calorie']}kcal")
    else:
        print(f"分类 '{cat}' 查询失败: {r.status_code}")
