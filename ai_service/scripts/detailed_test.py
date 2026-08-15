import requests
import json

BASE_URL = "http://localhost:8002/api/v1"


def test_chat_full():
    print("=" * 70)
    print("测试 1: 聊天 API - 完整回复（带健康数据快照）")
    print("=" * 70)
    
    health_snapshot = {
        "profile": {
            "username": "张先生",
            "gender": "男",
            "age": 35,
            "height_cm": 175,
            "weight_kg": 70,
            "bmi": 22.9,
            "bmr": 1665,
            "crowd_type": "普通成年人"
        },
        "today_body_metrics": {
            "height_cm": 175,
            "weight_kg": 70,
            "age": 35,
            "bmi": 22.9,
            "bmr": 1665
        },
        "today_diet": [
            {
                "meal_type": "早餐",
                "foods": [
                    {"food_name": "全麦面包", "category": "主食", "eat_weight_g": 100, "calories_kcal": 260, "protein_g": 9, "fat_g": 3, "carb_g": 48},
                    {"food_name": "鸡蛋", "category": "肉蛋类", "eat_weight_g": 50, "calories_kcal": 72, "protein_g": 6, "fat_g": 5, "carb_g": 0.5},
                    {"food_name": "牛奶", "category": "奶类", "eat_weight_g": 250, "calories_kcal": 135, "protein_g": 7.5, "fat_g": 7.5, "carb_g": 8.75}
                ],
                "food_items_count": 3,
                "meal_calories_kcal": 467
            },
            {
                "meal_type": "午餐",
                "foods": [
                    {"food_name": "糙米饭", "category": "主食", "eat_weight_g": 150, "calories_kcal": 174, "protein_g": 4, "fat_g": 0.8, "carb_g": 38},
                    {"food_name": "鸡胸肉", "category": "肉蛋类", "eat_weight_g": 150, "calories_kcal": 200, "protein_g": 34, "fat_g": 2, "carb_g": 0},
                    {"food_name": "西兰花", "category": "蔬菜", "eat_weight_g": 200, "calories_kcal": 68, "protein_g": 4.4, "fat_g": 0.6, "carb_g": 10},
                    {"food_name": "橄榄油", "category": "油脂类", "eat_weight_g": 10, "calories_kcal": 90, "protein_g": 0, "fat_g": 10, "carb_g": 0}
                ],
                "food_items_count": 4,
                "meal_calories_kcal": 532
            },
            {
                "meal_type": "晚餐",
                "foods": [
                    {"food_name": "红薯", "category": "主食", "eat_weight_g": 200, "calories_kcal": 180, "protein_g": 2.6, "fat_g": 0.2, "carb_g": 42},
                    {"food_name": "清蒸鱼", "category": "水产", "eat_weight_g": 150, "calories_kcal": 150, "protein_g": 30, "fat_g": 3, "carb_g": 0},
                    {"food_name": "凉拌黄瓜", "category": "蔬菜", "eat_weight_g": 100, "calories_kcal": 16, "protein_g": 0.8, "fat_g": 0.2, "carb_g": 3}
                ],
                "food_items_count": 3,
                "meal_calories_kcal": 346
            }
        ],
        "today_diet_total": {
            "total_calories_kcal": 1345,
            "total_protein_g": 88.3,
            "total_fat_g": 28.3,
            "total_carb_g": 102.25,
            "total_food_items": 10,
            "total_meals": 3
        },
        "diet_reference": {
            "general": {
                "bmi_normal_range": "18.5 - 23.9",
                "water_intake": "男性1700ml，女性1500ml",
                "meal_ratio": "早餐20-30%，午餐40-50%，晚餐20-30%"
            },
            "crowd_specific": {
                "protein_target": "1.0 - 1.2 g/kg 体重/天",
                "advice": "均衡饮食，每日蔬果谷蛋奶肉齐全，规律运动，充足睡眠。"
            },
            "gi_reference": {
                "low_gi": "GI < 55：糙米、燕麦、荞麦、红薯、苹果、梨、酸奶、大多数蔬菜",
                "medium_gi": "GI 55-70：全麦面包、糙米、香蕉、玉米、葡萄",
                "high_gi": "GI > 70：白米饭、白面包、糯米、含糖饮料、西瓜、麦芽糖"
            }
        }
    }
    
    data = {
        "message": "根据我的情况，今天吃得怎么样？",
        "user_id": 1,
        "health_snapshot": health_snapshot
    }
    
    print("【用户健康数据】")
    print(f"  姓名: {health_snapshot['profile']['username']}")
    print(f"  性别: {health_snapshot['profile']['gender']}")
    print(f"  年龄: {health_snapshot['profile']['age']}岁")
    print(f"  身高: {health_snapshot['profile']['height_cm']}cm")
    print(f"  体重: {health_snapshot['profile']['weight_kg']}kg")
    print(f"  BMI: {health_snapshot['profile']['bmi']}")
    print(f"  BMR: {health_snapshot['profile']['bmr']} kcal")
    print(f"  人群类型: {health_snapshot['profile']['crowd_type']}")
    
    print("\n【今日饮食记录】")
    for meal in health_snapshot['today_diet']:
        print(f"  {meal['meal_type']}（{meal['meal_calories_kcal']} kcal）:")
        for food in meal['foods']:
            print(f"    - {food['food_name']} {food['eat_weight_g']}g: {food['calories_kcal']}kcal (蛋白质{food['protein_g']}g, 脂肪{food['fat_g']}g, 碳水{food['carb_g']}g)")
    
    print(f"\n【今日营养合计】")
    total = health_snapshot['today_diet_total']
    print(f"  总热量: {total['total_calories_kcal']} kcal")
    print(f"  蛋白质: {total['total_protein_g']}g")
    print(f"  脂肪: {total['total_fat_g']}g")
    print(f"  碳水: {total['total_carb_g']}g")
    
    print(f"\n【用户问题】: {data['message']}")
    print("\n" + "-" * 70)
    
    r = requests.post(f"{BASE_URL}/chat", json=data)
    result = r.json()
    print(f"对话ID: {result.get('conversation_id')}")
    print(f"模型: {result.get('provider')}")
    print(f"难度: {result.get('difficulty')}")
    print(f"\nAI完整回复:\n{result.get('response', '')}")
    return result


def test_nutrition_full():
    print("\n" + "=" * 70)
    print("测试 2: 营养分析 API - 完整结果")
    print("=" * 70)
    data = {
        "user_profile": {"username": "张先生", "gender": "男", "age": 35, "height": 175, "weight": 70, "activity_level": "中等", "crowd_type": "普通成年人"},
        "daily_nutrition": {"calories": 2200, "protein": 75, "carbohydrate": 280, "fat": 70, "fiber": 20, "sodium": 4500, "calcium": 800},
        "daily_exercise": {"type": "跑步", "duration": 30, "intensity": "中等"}
    }
    r = requests.post(f"{BASE_URL}/nutrition/analyze", json=data)
    result = r.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def test_voice_full():
    print("\n" + "=" * 70)
    print("测试 3: 语音解析 API - 完整结果")
    print("=" * 70)
    data = {"text": "我今天早上吃了一碗小米粥，一个鸡蛋，还有一杯牛奶，中午吃了米饭和红烧肉，晚上吃了面条"}
    r = requests.post(f"{BASE_URL}/voice/parse", json=data)
    result = r.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    total_calories = 0
    for item in result.get("items", []):
        food_name = item.get("food_name", "")
        weight = item.get("weight", 0)
        calorie_map = {"小米粥": 46, "鸡蛋": 144, "牛奶": 54, "米饭": 116, "红烧肉": 350, "面条": 110}
        calorie_per_100g = calorie_map.get(food_name, 150)
        calories = int(calorie_per_100g * weight / 100) if weight else 0
        total_calories += calories
        print(f"  {food_name}: {weight}g = {calories}kcal")
    print(f"\n  总计: {total_calories}kcal")
    return result


def test_food_audit_full():
    print("\n" + "=" * 70)
    print("测试 4: 食物审核 API - 完整分析")
    print("=" * 70)
    
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
        print(f"\n--- {food['food_name']} ({food['portion']}) ---")
        print(f"审核状态: {result.get('status')}")
        print(f"热量: {result.get('calories', 0)} kcal")
        print(f"蛋白质: {result.get('protein', 0)} g")
        print(f"脂肪: {result.get('fat', 0)} g")
        print(f"碳水: {result.get('carbohydrate', 0)} g")
        print(f"营养标签: {result.get('nutrition_tags', [])}")
        print(f"建议: {result.get('advice', '')}")
        
        if "西兰花炒虾仁" in food['food_name']:
            print("\n【详细分析】西兰花炒虾仁为混合菜肴:")
            print("  - 建议拆分比例: 西兰花约150g + 虾仁约50g")
            print("  - 西兰花: 150g × 34kcal/100g = 51kcal")
            print("  - 虾仁: 50g × 48kcal/100g = 24kcal")
            print("  - 油(假设10g): 90kcal")
            print("  - 总计: 约165kcal")
        
        if "奶茶" in food['food_name']:
            print("\n【详细分析】奶茶热量构成:")
            print("  - 标准奶茶(500ml):")
            print("    * 奶: 300ml × 54kcal/100ml = 162kcal")
            print("    * 茶: 200ml × 0kcal = 0kcal")
            print("    * 糖(约40g): 160kcal")
            print("    * 总计: 约322kcal")
            print("  - 不同类型奶茶差异:")
            print("    * 无糖奶茶: 约200-250kcal")
            print("    * 低糖奶茶: 约250-300kcal")
            print("    * 标准奶茶: 约300-400kcal")
            print("    * 加料奶茶(珍珠/椰果): 约400-500kcal")
            print("    * 奶盖奶茶: 约450-600kcal")
    
    return result


def test_weekly_report_full():
    print("\n" + "=" * 70)
    print("测试 5: 周报生成 API - 完整报告")
    print("=" * 70)
    data = {
        "user_profile": {"username": "李女士", "gender": "女", "age": 42, "height": 165, "weight": 58, "crowd_type": "普通成年人"},
        "weekly_stats": {
            "total_days": 7, "active_days": 5, "avg_sleep_hours": 7.2, "avg_steps": 8500,
            "avg_calories": 1800, "avg_water": 1500, "exercise_minutes": 180,
            "mood_score": 75, "diet_score": 80, "health_score": 78,
            "sleep_quality": "良好", "exercise_types": ["快走", "瑜伽", "游泳"],
            "daily_data": [
                {"date": "周一", "steps": 8000, "calories": 1750, "water": 1400, "sleep": 7.0, "exercise": "快走30分钟"},
                {"date": "周二", "steps": 9000, "calories": 1800, "water": 1500, "sleep": 7.5, "exercise": "瑜伽45分钟"},
                {"date": "周三", "steps": 7000, "calories": 1700, "water": 1300, "sleep": 7.0, "exercise": "无"},
                {"date": "周四", "steps": 10000, "calories": 1900, "water": 1600, "sleep": 7.5, "exercise": "游泳60分钟"},
                {"date": "周五", "steps": 8500, "calories": 1850, "water": 1500, "sleep": 7.0, "exercise": "快走30分钟"},
                {"date": "周六", "steps": 9500, "calories": 1800, "water": 1700, "sleep": 8.0, "exercise": "瑜伽45分钟"},
                {"date": "周日", "steps": 7500, "calories": 1700, "water": 1500, "sleep": 7.0, "exercise": "无"},
            ]
        }
    }
    r = requests.post(f"{BASE_URL}/report/weekly-summary", json=data)
    result = r.json()
    print(f"报告类型: {result.get('report_type')}")
    print(f"健康评分: {result.get('health_score')}")
    print(f"\n完整周报摘要:\n{result.get('summary', '')}")
    print(f"\n本周亮点:")
    for i, highlight in enumerate(result.get('highlights', [])):
        print(f"  {i+1}. {highlight}")
    print(f"\n健康小贴士:")
    for i, tip in enumerate(result.get('tips', [])):
        print(f"  {i+1}. {tip}")
    print(f"\n改进建议:")
    for i, suggestion in enumerate(result.get('suggestions', [])):
        print(f"  {i+1}. {suggestion}")
    
    print("\n【输入数据详情】每日数据:")
    for day in data["weekly_stats"].get("daily_data", []):
        print(f"  {day['date']}: 步数={day['steps']} | 热量={day['calories']}kcal | 饮水={day['water']}ml | 睡眠={day['sleep']}h | 运动={day['exercise']}")
    
    return result


def test_article_full():
    print("\n" + "=" * 70)
    print("测试 6: 文章生成 API - 完整文章")
    print("=" * 70)
    data = {"topic": "夏季如何科学补水", "target_crowd": "普通成年人"}
    r = requests.post(f"{BASE_URL}/article/generate", json=data)
    result = r.json()
    print(f"文章标题: {result.get('title')}")
    print(f"目标人群: {result.get('target_crowd')}")
    print(f"作者: {result.get('author')}")
    print(f"文章类型: {result.get('article_type')}")
    print(f"关键词: {result.get('keywords', [])}")
    print(f"摘要: {result.get('summary', '')}")
    print(f"\n完整文章内容:\n{result.get('content', '')}")
    return result


def test_diet_plan_full():
    print("\n" + "=" * 70)
    print("测试 7: 膳食计划 API - 完整方案")
    print("=" * 70)
    data = {
        "user_profile": {"username": "王先生", "gender": "男", "age": 28, "height": 180, "weight": 75, "activity_level": "较高", "crowd_type": "健身人群"},
        "goal": "增肌减脂"
    }
    r = requests.post(f"{BASE_URL}/diet/plan", json=data)
    result = r.json()
    print(f"目标: {result.get('goal')}")
    print(f"总热量: {result.get('total_calories')} kcal")
    
    daily_plan = result.get("daily_plan", {})
    for meal, foods in daily_plan.items():
        print(f"\n{meal}:")
        for food in foods:
            print(f"  - {food.get('food', '')}: {food.get('portion', '')}")
    
    nutrition = result.get("nutrition_breakdown", {})
    print(f"\n营养分配:")
    print(f"  蛋白质: {nutrition.get('protein', 0)}g ({nutrition.get('protein', 0)/result.get('total_calories', 1)*4*100:.1f}%)")
    print(f"  碳水化合物: {nutrition.get('carbohydrate', 0)}g ({nutrition.get('carbohydrate', 0)/result.get('total_calories', 1)*4*100:.1f}%)")
    print(f"  脂肪: {nutrition.get('fat', 0)}g ({nutrition.get('fat', 0)/result.get('total_calories', 1)*9*100:.1f}%)")
    
    if "tips" in result:
        print(f"\n膳食提示:")
        for tip in result["tips"]:
            print(f"  - {tip}")
    
    return result


def test_health_reflection_full():
    print("\n" + "=" * 70)
    print("测试 8: 健康反思 API - 完整分析")
    print("=" * 70)
    data = {
        "user_profile": {"username": "赵女士", "gender": "女", "age": 55, "height": 160, "weight": 65, "crowd_type": "老年人"},
        "health_data": {
            "recent_blood_pressure": {"systolic": 145, "diastolic": 92},
            "recent_blood_sugar": 6.8,
            "sleep_quality": "一般",
            "exercise_frequency": "每周3次",
            "stress_level": "较高",
            "BMI": 25.4,
            "waist_circumference": 85
        },
        "concerns": ["血压偏高", "睡眠不好"]
    }
    r = requests.post(f"{BASE_URL}/health/reflection", json=data)
    result = r.json()
    print(f"反思类型: {result.get('reflection_type')}")
    print(f"风险等级: {result.get('risk_level')}")
    print(f"\n完整健康反思:\n{result.get('reflection', '')}")
    print(f"\n关键发现:")
    for i, finding in enumerate(result.get('key_findings', [])):
        print(f"  {i+1}. {finding}")
    print(f"\n行动计划:")
    for i, plan in enumerate(result.get('action_plan', [])):
        print(f"  {i+1}. {plan}")
    print(f"\n健康提示:")
    for i, tip in enumerate(result.get('tips', [])):
        print(f"  {i+1}. {tip}")
    
    return result


def test_retrieve_full():
    print("\n" + "=" * 70)
    print("测试 9: 向量检索 API - 完整结果")
    print("=" * 70)
    data = {"query": "糖尿病患者应该吃什么", "top_k": 3}
    r = requests.post(f"{BASE_URL}/retrieve", json=data)
    result = r.json()
    print(f"查询词: {result.get('query')}")
    print(f"结果数: {result.get('total')}")
    for i, item in enumerate(result.get('results', [])):
        print(f"\n结果 {i+1}:")
        print(f"  相似度: {item.get('similarity', 0):.4f}")
        print(f"  来源: {item.get('metadata', {}).get('source', '')}")
        print(f"  类别: {item.get('metadata', {}).get('category', '')}")
        print(f"  完整内容:\n{item.get('content', '')}")
    return result


if __name__ == "__main__":
    print("AI 服务详细测试报告\n")
    test_retrieve_full()
    test_chat_full()
    test_voice_full()
    test_nutrition_full()
    test_food_audit_full()
    test_weekly_report_full()
    test_article_full()
    test_diet_plan_full()
    test_health_reflection_full()
    print("\n" + "=" * 70)
    print("所有测试完成！")
    print("=" * 70)
