"""测试后端食物搜索的优先级排序"""
import requests
import json

BASE_URL = "http://localhost:8081"

def test_search(keyword, limit=8):
    """测试搜索结果排序"""
    try:
        resp = requests.get(f"{BASE_URL}/api/food/search", params={"keyword": keyword}, timeout=10)
        data = resp.json()
        foods = data.get("data", [])
        print(f"\n=== 搜索 '{keyword}' 前{limit}条 ===")
        for i, food in enumerate(foods[:limit]):
            print(f"  {i+1}. {food.get('foodName')}: {food.get('calorie')}kcal, 蛋白{food.get('protein')}g [{food.get('foodCategory')}]")
        return foods
    except Exception as e:
        print(f"搜索 '{keyword}' 失败: {e}")
        return []

def test_category(category):
    """测试分类查询排序"""
    try:
        resp = requests.get(f"{BASE_URL}/api/food/category/{category}", timeout=10)
        data = resp.json()
        foods = data.get("data", [])
        print(f"\n=== 分类 '{category}' 前8条 ===")
        for i, food in enumerate(foods[:8]):
            print(f"  {i+1}. {food.get('foodName')}: {food.get('calorie')}kcal [{food.get('foodCategory')}]")
        return foods
    except Exception as e:
        print(f"分类查询 '{category}' 失败: {e}")
        return []

def main():
    print("=" * 50)
    print("后端食物搜索优先级排序测试")
    print("=" * 50)

    # 测试常用食物搜索
    test_search("牛奶")
    test_search("酸奶")
    test_search("苹果")
    test_search("米饭")
    test_search("鸡蛋")
    test_search("豆腐")
    test_search("猪肉")
    test_search("白菜")

    # 测试分类查询
    test_category("主食")
    test_category("水果")
    test_category("奶类")

    # 测试无关键词（全量）查询
    try:
        resp = requests.get(f"{BASE_URL}/api/food/search", timeout=10)
        data = resp.json()
        foods = data.get("data", [])
        print(f"\n=== 无关键词搜索前10条（应优先显示常用食物）===")
        for i, food in enumerate(foods[:10]):
            print(f"  {i+1}. {food.get('foodName')}: {food.get('calorie')}kcal [{food.get('foodCategory')}]")
        print(f"\n总食物数: {len(foods)}")
    except Exception as e:
        print(f"全量查询失败: {e}")

if __name__ == "__main__":
    main()
