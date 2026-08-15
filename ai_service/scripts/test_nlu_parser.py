#!/usr/bin/env python3
"""NLU 解析引擎测试 — 先单元测试，再通过 API 调用"""
import json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试用例
TEST_CASES = [
    {
        "name": "早餐-简单",
        "text": "早餐：牛奶250ml，全麦面包2片，鸡蛋1个",
    },
    {
        "name": "三餐完整",
        "text": """早餐：燕麦片50g，纯牛奶250ml，水煮鸡蛋2个
午餐：白米饭200g，鸡胸肉150g，西兰花150g
晚餐：白米饭150g，清蒸鲈鱼150g，炒青菜200g""",
    },
    {
        "name": "健身餐",
        "text": """健身餐：糙米饭250g，鸡胸肉200g，西兰花200g，香蕉1根，纯牛奶300ml""",
    },
    {
        "name": "口语化描述",
        "text": """今天早上我吃了2个水煮蛋，喝了一杯牛奶，中午吃了一碗米饭和一份红烧肉，晚上就吃了点水果，一个苹果和一个香蕉""",
    },
    {
        "name": "只吃零食",
        "text": "下午茶：1杯奶茶，1包薯片，2块巧克力",
    },
]

print("=" * 80)
print("NLU 解析引擎测试")
print("=" * 80)

# 1. 直接单元测试（不依赖 LLM）
print("\n[1/2] 单元测试：规则兜底引擎")
from agent.nlu_parser import _load_food_db, _fuzzy_match_food, _convert_amount, _rule_based_extract

# 测试食物匹配
print("\n  -- 食物模糊匹配 --")
test_foods = ["鸡蛋", "鸡胸肉", "番茄", "白米饭", "鲈鱼", "苹果", "三文鱼", "豆腐", "可乐", "薯片"]
for food in test_foods:
    result = _fuzzy_match_food(food)
    if result:
        print(f"    OK {food:8s} -> {result['food_name']:20s} ({result['calorie']:6.1f} kcal/100g, priority={result['priority']})")
    else:
        print(f"    FAIL {food:8s} -> 未匹配")

# 测试单位换算
print("\n  -- 单位换算 --")
test_amounts = [
    ("150g", ""), ("200克", ""), ("2个", "鸡蛋"), ("1碗", "米饭"),
    ("1杯", ""), ("3片", "全麦面包"), ("1根", "香蕉"), ("330ml", ""),
]
for amount, food in test_amounts:
    grams, desc = _convert_amount(amount, food)
    print(f"    {amount:8s} ({food:8s}) -> {grams:6.1f}g ({desc})")

# 测试规则提取
print("\n  -- 规则提取 --")
simple_text = "早餐：牛奶250ml，全麦面包2片，鸡蛋1个"
result = _rule_based_extract(simple_text)
print(f"    输入: {simple_text}")
print(f"    输出: {json.dumps(result, ensure_ascii=False)}")

# 2. 完整解析测试（通过 API）
print(f"\n[2/2] 完整解析测试（API调用）")
import urllib.request

BASE = "http://localhost:8002"
for case in TEST_CASES:
    print(f"\n  === {case['name']} ===")
    print(f"  输入: {case['text'][:80]}...")

    payload = {"text": case["text"]}
    req = urllib.request.Request(
        f"{BASE}/api/v1/meal/parse",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        start = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
            elapsed = round((time.time() - start) * 1000)

        print(f"  耗时: {elapsed}ms")
        print(f"  提供者: {result.get('provider', 'N/A')}")

        meals = result.get("meals", {})
        for meal_type, meal_data in meals.items():
            foods = meal_data.get("foods", [])
            totals = meal_data.get("totals", {})
            print(f"  {meal_type}: {len(foods)}种食物")
            for f in foods:
                print(f"    - {f['food_name_matched']:20s} {f['amount_raw']:10s} -> {f['amount_grams']:6.1f}g, "
                      f"热量:{f['calorie']:6.1f} 蛋白质:{f['protein']:5.1f} 脂肪:{f['fat']:5.1f} 碳水:{f['carb']:5.1f}")
            print(f"    小计: 热量{totals.get('calorie',0):.0f} 蛋白质{totals.get('protein',0):.0f}g "
                  f"脂肪{totals.get('fat',0):.0f}g 碳水{totals.get('carb',0):.0f}g")

        daily = result.get("daily_totals", {})
        print(f"  全日合计: {daily.get('calorie',0):.0f}kcal, 蛋白质{daily.get('protein',0):.0f}g, "
              f"脂肪{daily.get('fat',0):.0f}g, 碳水{daily.get('carb',0):.0f}g")

        warnings = result.get("warnings", [])
        if warnings:
            print(f"  警告({len(warnings)}条):")
            for w in warnings:
                print(f"    [{w['severity']}] {w['detail']}")

    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {e.read().decode()[:200]}")
    except Exception as e:
        print(f"  [ERROR] {e}")

    time.sleep(0.5)

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
