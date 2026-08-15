import requests
import json

BASE_URL = "http://localhost:8002/api/v1"

def test_retrieve():
    print("=" * 60)
    print("测试 1: 向量检索 API")
    print("=" * 60)
    data = {"query": "糖尿病患者应该吃什么", "top_k": 3}
    try:
        resp = requests.post(f"{BASE_URL}/retrieve", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"查询: {result.get('query')}")
        print(f"结果数: {result.get('total')}")
        for i, item in enumerate(result.get('results', [])):
            print(f"\n结果 {i+1}:")
            print(f"  相似度: {item.get('similarity', 0):.4f}")
            print(f"  来源: {item.get('metadata', {}).get('source', '')}")
            print(f"  内容: {item.get('content', '')[:150]}...")
    except Exception as e:
        print(f"测试失败: {e}")

def test_chat():
    print("\n" + "=" * 60)
    print("测试 2: 聊天 API")
    print("=" * 60)
    data = {
        "message": "我今年35岁，身高175cm，体重70kg，男性，最近血糖有点高，应该怎么调整饮食？",
        "user_id": 1
    }
    try:
        resp = requests.post(f"{BASE_URL}/chat", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"对话ID: {result.get('conversation_id')}")
        print(f"模型: {result.get('provider')}")
        print(f"难度: {result.get('difficulty')}")
        print(f"\n回复内容:\n{result.get('response', '')[:500]}...")
    except Exception as e:
        print(f"测试失败: {e}")

def test_voice_parse():
    print("\n" + "=" * 60)
    print("测试 3: 语音解析 API")
    print("=" * 60)
    data = {"text": "我今天早上吃了一碗小米粥，一个鸡蛋，还有一杯牛奶，中午吃了米饭和红烧肉，晚上吃了面条"}
    try:
        resp = requests.post(f"{BASE_URL}/voice/parse", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"测试失败: {e}")

def test_nutrition_analysis():
    print("\n" + "=" * 60)
    print("测试 4: 营养分析 API")
    print("=" * 60)
    data = {
        "user_profile": {
            "username": "张先生",
            "gender": "男",
            "age": 35,
            "height": 175,
            "weight": 70,
            "activity_level": "中等",
            "crowd_type": "普通成年人"
        },
        "daily_nutrition": {
            "calories": 2200,
            "protein": 75,
            "carbohydrate": 280,
            "fat": 70,
            "fiber": 20,
            "sodium": 4500,
            "calcium": 800
        },
        "daily_exercise": {
            "type": "跑步",
            "duration": 30,
            "intensity": "中等"
        }
    }
    try:
        resp = requests.post(f"{BASE_URL}/nutrition/analyze", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"分析结果类型: {result.get('analysis_type')}")
        print(f"\n营养评分: {result.get('nutrition_score')}")
        if 'summary' in result:
            print(f"\n分析摘要:\n{result['summary'][:300]}...")
        if 'recommendations' in result:
            print(f"\n建议条数: {len(result['recommendations'])}")
            for rec in result['recommendations'][:3]:
                print(f"  - {rec.get('suggestion', '')[:80]}")
    except Exception as e:
        print(f"测试失败: {e}")

def test_food_audit():
    print("\n" + "=" * 60)
    print("测试 5: 食物审核 API")
    print("=" * 60)
    test_foods = [
        {"food_name": "红烧肉", "portion": "100克"},
        {"food_name": "西兰花炒虾仁", "portion": "200克"},
        {"food_name": "奶茶", "portion": "500毫升"}
    ]
    for food in test_foods:
        try:
            resp = requests.post(f"{BASE_URL}/food/audit", json=food)
            print(f"\n食物: {food['food_name']} ({food['portion']})")
            print(f"状态码: {resp.status_code}")
            result = resp.json()
            print(f"审核状态: {result.get('status')}")
            print(f"热量: {result.get('calories', 0)} kcal")
            print(f"营养标签: {result.get('nutrition_tags', [])}")
            if 'advice' in result:
                print(f"建议: {result['advice'][:100]}")
        except Exception as e:
            print(f"  测试失败: {e}")

def test_weekly_report():
    print("\n" + "=" * 60)
    print("测试 6: 周报生成 API")
    print("=" * 60)
    data = {
        "user_profile": {
            "username": "李女士",
            "gender": "女",
            "age": 42,
            "height": 165,
            "weight": 58,
            "crowd_type": "普通成年人"
        },
        "weekly_stats": {
            "total_days": 7,
            "active_days": 5,
            "avg_sleep_hours": 7.2,
            "avg_steps": 8500,
            "avg_calories": 1800,
            "avg_water": 1500,
            "exercise_minutes": 180,
            "mood_score": 75,
            "diet_score": 80,
            "health_score": 78,
            "sleep_quality": "良好",
            "exercise_types": ["快走", "瑜伽", "游泳"]
        }
    }
    try:
        resp = requests.post(f"{BASE_URL}/report/weekly-summary", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"报告类型: {result.get('report_type')}")
        print(f"\n健康评分: {result.get('health_score')}")
        if 'summary' in result:
            print(f"\n周报摘要:\n{result['summary'][:400]}...")
        if 'highlights' in result:
            print(f"\n本周亮点: {', '.join(result['highlights'])}")
    except Exception as e:
        print(f"测试失败: {e}")

def test_article_generate():
    print("\n" + "=" * 60)
    print("测试 7: 文章生成 API")
    print("=" * 60)
    data = {
        "topic": "夏季如何科学补水",
        "target_crowd": "普通成年人"
    }
    try:
        resp = requests.post(f"{BASE_URL}/article/generate", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"文章标题: {result.get('title')}")
        print(f"目标人群: {result.get('target_crowd')}")
        print(f"\n文章内容:\n{result.get('content', '')[:500]}...")
    except Exception as e:
        print(f"测试失败: {e}")

def test_diet_plan():
    print("\n" + "=" * 60)
    print("测试 8: 膳食计划 API")
    print("=" * 60)
    data = {
        "user_profile": {
            "username": "王先生",
            "gender": "男",
            "age": 28,
            "height": 180,
            "weight": 75,
            "activity_level": "较高",
            "crowd_type": "健身人群"
        },
        "goal": "增肌减脂"
    }
    try:
        resp = requests.post(f"{BASE_URL}/diet/plan", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"目标: {result.get('goal')}")
        print(f"总热量: {result.get('total_calories')} kcal")
        if 'daily_plan' in result:
            for meal, foods in result['daily_plan'].items():
                print(f"\n{meal}:")
                for food in foods[:3]:
                    print(f"  - {food.get('food', '')}: {food.get('portion', '')}")
        if 'nutrition_breakdown' in result:
            nb = result['nutrition_breakdown']
            print(f"\n营养分配: 蛋白质{nb.get('protein', 0)}g / 碳水{nb.get('carbohydrate', 0)}g / 脂肪{nb.get('fat', 0)}g")
    except Exception as e:
        print(f"测试失败: {e}")

def test_health_reflection():
    print("\n" + "=" * 60)
    print("测试 9: 健康反思 API")
    print("=" * 60)
    data = {
        "user_profile": {
            "username": "赵女士",
            "gender": "女",
            "age": 55,
            "height": 160,
            "weight": 65,
            "crowd_type": "老年人"
        },
        "health_data": {
            "recent_blood_pressure": {"systolic": 145, "diastolic": 92},
            "recent_blood_sugar": 6.8,
            "sleep_quality": "一般",
            "exercise_frequency": "每周3次",
            "stress_level": "较高"
        },
        "concerns": ["血压偏高", "睡眠不好"]
    }
    try:
        resp = requests.post(f"{BASE_URL}/health/reflection", json=data)
        print(f"状态码: {resp.status_code}")
        result = resp.json()
        print(f"反思类型: {result.get('reflection_type')}")
        if 'reflection' in result:
            print(f"\n健康反思:\n{result['reflection'][:400]}...")
        if 'action_plan' in result:
            print(f"\n行动计划:")
            for plan in result['action_plan'][:5]:
                print(f"  - {plan}")
    except Exception as e:
        print(f"测试失败: {e}")

def main():
    print("开始测试所有 AI Agent API...")
    print("=" * 60)
    
    test_retrieve()
    test_chat()
    test_voice_parse()
    test_nutrition_analysis()
    test_food_audit()
    test_weekly_report()
    test_article_generate()
    test_diet_plan()
    test_health_reflection()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()