import requests
import json

BASE_URL = "http://localhost:8002/api/v1"


def verify_nutrition():
    print("=" * 60)
    print("验证 1: 营养分析 API（之前失败，现在应通过）")
    print("=" * 60)
    data = {
        "user_profile": {"username": "张先生", "gender": "男", "age": 35, "height": 175, "weight": 70, "activity_level": "中等", "crowd_type": "普通成年人"},
        "daily_nutrition": {"calories": 2200, "protein": 75, "carbohydrate": 280, "fat": 70, "fiber": 20, "sodium": 4500, "calcium": 800},
        "daily_exercise": {"type": "跑步", "duration": 30, "intensity": "中等"}
    }
    r = requests.post(f"{BASE_URL}/nutrition/analyze", json=data)
    result = r.json()
    print("分析类型:", result.get("analysis_type"))
    print("营养评分:", result.get("nutrition_score"))
    print("能量评分:", result.get("energy_score"))
    print("蛋白质评分:", result.get("protein_score"))
    print("脂肪评分:", result.get("fat_score"))
    print("碳水评分:", result.get("carbs_score"))
    print("风险项:", result.get("risk_items"))
    print("提示:", result.get("tips"))
    summary = result.get("summary", "")
    print("摘要:", summary[:200] if summary else "")


def verify_voice_parse():
    print("\n" + "=" * 60)
    print("验证 2: 语音解析 API（之前鸡蛋牛奶weight=null）")
    print("=" * 60)
    data = {"text": "我今天早上吃了一碗小米粥，一个鸡蛋，还有一杯牛奶，中午吃了米饭和红烧肉，晚上吃了面条"}
    r = requests.post(f"{BASE_URL}/voice/parse", json=data)
    result = r.json()
    print("解析结果:")
    for item in result.get("items", []):
        print(f"  {item.get('food_name')}: {item.get('weight')}g")

    null_weights = [i for i in result.get("items", []) if i.get("weight") is None]
    if null_weights:
        print("\n[警告] 仍有 weight 为 null 的食物:", [i.get("food_name") for i in null_weights])
    else:
        print("\n[通过] 所有食物均有重量估算")


def verify_food_audit():
    print("\n" + "=" * 60)
    print("验证 3: 食物审核 API（之前奶茶1750kcal偏高）")
    print("=" * 60)
    test_foods = [
        {"food_name": "红烧肉", "portion": "100克"},
        {"food_name": "西兰花炒虾仁", "portion": "200克"},
        {"food_name": "奶茶", "portion": "500毫升"},
        {"food_name": "鸡胸肉", "portion": "150克"},
        {"food_name": "米饭", "portion": "200克"},
    ]
    for food in test_foods:
        r = requests.post(f"{BASE_URL}/food/audit", json=food)
        result = r.json()
        print(f"\n{food['food_name']} ({food['portion']}):")
        print(f"  热量: {result.get('calories', 0)} kcal")
        print(f"  标签: {result.get('nutrition_tags', [])}")
        advice = result.get("advice", "")
        print(f"  建议: {advice[:80] if advice else ''}")


def verify_article():
    print("\n" + "=" * 60)
    print("验证 4: 文章生成 API（之前target_crowd为None）")
    print("=" * 60)
    data = {"topic": "秋季养生饮食", "target_crowd": "中老年人"}
    r = requests.post(f"{BASE_URL}/article/generate", json=data)
    result = r.json()
    print("文章标题:", result.get("title"))
    print("目标人群:", result.get("target_crowd"))
    print("作者:", result.get("author"))
    print("文章类型:", result.get("article_type"))
    if result.get("target_crowd"):
        print("[通过] target_crowd 字段已正确回传")
    else:
        print("[失败] target_crowd 仍为空")


if __name__ == "__main__":
    print("开始验证优化效果...\n")
    verify_nutrition()
    verify_voice_parse()
    verify_food_audit()
    verify_article()
    print("\n" + "=" * 60)
    print("验证完成！")
    print("=" * 60)
