#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 健康助手全功能测试脚本
测试所有AI服务接口的请求/响应
"""

import requests
import json
import time
from datetime import datetime

AI_BASE_URL = "http://localhost:8002/api/v1"
BACKEND_URL = "http://localhost:8082/api"

results = []

def log_result(feature_name, endpoint, request_body, response, duration, error=None):
    result = {
        "feature": feature_name,
        "endpoint": endpoint,
        "request": request_body,
        "response": response,
        "duration_ms": round(duration * 1000, 2),
        "status": "FAILED" if error else "SUCCESS",
        "error": str(error) if error else None
    }
    results.append(result)
    
    print(f"\n{'='*80}")
    print(f"功能: {feature_name}")
    print(f"端点: {endpoint}")
    print(f"耗时: {result['duration_ms']}ms")
    print(f"状态: {result['status']}")
    if error:
        print(f"错误: {error}")
    print(f"{'='*80}")
    print(f"\n📤 请求体:")
    print(json.dumps(request_body, ensure_ascii=False, indent=2))
    print(f"\n📥 响应:")
    if response:
        print(json.dumps(response, ensure_ascii=False, indent=2)[:2000])
    else:
        print("(无响应)")

def test_chat():
    """测试1: 健康咨询 - /chat"""
    print("\n" + "="*80)
    print("【测试1】健康咨询 (Chat)")
    print("="*80)
    
    health_snapshot = {
        "date": "2026-07-27",
        "profile": {
            "username": "测试用户",
            "gender": "男",
            "age": 28,
            "height_cm": 175,
            "weight_kg": 70,
            "bmi": 22.9,
            "crowdType": "普通人群"
        },
        "today_body_metrics": {
            "height_cm": 175,
            "weight_kg": 70,
            "age": 28,
            "bmi": 22.9
        },
        "today_diet": [
            {
                "meal_type": "早餐",
                "foods": [
                    {"food_name": "牛奶", "eat_weight_g": 250, "calories_kcal": 135.0, "protein_g": 8.0, "fat_g": 8.0, "carb_g": 12.0},
                    {"food_name": "鸡蛋", "eat_weight_g": 50, "calories_kcal": 78.0, "protein_g": 6.3, "fat_g": 5.3, "carb_g": 0.6},
                    {"food_name": "全麦面包", "eat_weight_g": 50, "calories_kcal": 125.0, "protein_g": 5.0, "fat_g": 2.5, "carb_g": 22.5}
                ],
                "meal_calories_kcal": 338.0
            }
        ],
        "today_diet_total": {
            "total_calories_kcal": 338.0,
            "total_protein_g": 19.3,
            "total_fat_g": 15.8,
            "total_carb_g": 35.1
        },
        "diet_reference": {
            "general": {
                "bmi_normal_range": "18.5 - 23.9 (中国标准)",
                "water_intake": "每日饮水 1500 - 2000 ml",
                "meal_ratio": "早:午:晚 = 3:4:3"
            },
            "crowd_specific": {
                "protein_target": "1.0 - 1.2 g/kg 体重/天",
                "advice": "均衡饮食，每日蔬果谷蛋奶肉齐全"
            },
            "gi_reference": {
                "low_gi": "GI < 55：糙米、燕麦、红薯"
            }
        }
    }
    
    request_body = {
        "message": "我今天早餐吃了牛奶鸡蛋和全麦面包，这样搭配合理吗？",
        "user_id": 1,
        "health_snapshot": health_snapshot
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/chat", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("健康咨询", "/api/v1/chat", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("健康咨询", "/api/v1/chat", request_body, None, duration, e)

def test_voice_parse():
    """测试2: 语音解析 - /voice/parse"""
    print("\n" + "="*80)
    print("【测试2】语音解析 (Voice Parse)")
    print("="*80)
    
    test_sentences = [
        "我今天早上吃了一个包子和一杯豆浆",
        "中午吃了两碗米饭，一份红烧肉，一碗青菜",
        "晚上不吃饭了，减肥",
        "加餐吃了一个苹果和一杯酸奶",
        "下午三点运动完吃了两个鸡蛋和一根香蕉"
    ]
    
    for sentence in test_sentences[:2]:  # 测试前2个例子
        request_body = {"text": sentence}
        start_time = time.time()
        try:
            resp = requests.post(f"{AI_BASE_URL}/voice/parse", json=request_body, timeout=30)
            duration = time.time() - start_time
            response = resp.json() if resp.text else None
            log_result(f"语音解析: {sentence[:20]}...", "/api/v1/voice/parse", request_body, response, duration)
        except Exception as e:
            duration = time.time() - start_time
            log_result(f"语音解析: {sentence[:20]}...", "/api/v1/voice/parse", request_body, None, duration, e)

def test_nutrition_analyze():
    """测试3: 营养分析 - /nutrition/analyze"""
    print("\n" + "="*80)
    print("【测试3】营养分析 (Nutrition Analyze)")
    print("="*80)
    
    request_body = {
        "user_profile": {
            "username": "测试用户",
            "gender": "男",
            "age": 28,
            "height_cm": 175,
            "weight_kg": 70,
            "bmi": 22.9,
            "crowdType": "普通人群"
        },
        "daily_nutrition": {
            "total_calories_kcal": 1850.0,
            "total_protein_g": 75.0,
            "total_fat_g": 55.0,
            "total_carb_g": 250.0,
            "meals": [
                {
                    "meal_type": "早餐",
                    "calories_kcal": 400.0,
                    "foods": ["牛奶", "鸡蛋", "全麦面包"]
                },
                {
                    "meal_type": "午餐",
                    "calories_kcal": 750.0,
                    "foods": ["米饭", "红烧肉", "青菜", "番茄汤"]
                },
                {
                    "meal_type": "晚餐",
                    "calories_kcal": 500.0,
                    "foods": ["面条", "牛肉", "西兰花"]
                },
                {
                    "meal_type": "加餐",
                    "calories_kcal": 200.0,
                    "foods": ["苹果", "酸奶"]
                }
            ]
        },
        "daily_exercise": {
            "exercise_type": "跑步",
            "duration_minutes": 30,
            "calories_burned": 300
        }
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/nutrition/analyze", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("营养分析", "/api/v1/nutrition/analyze", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("营养分析", "/api/v1/nutrition/analyze", request_body, None, duration, e)

def test_food_audit():
    """测试4: 食物审核 - /food/audit"""
    print("\n" + "="*80)
    print("【测试4】食物审核 (Food Audit)")
    print("="*80)
    
    test_foods = [
        {"food_name": "鸡胸肉", "food_category": "肉类", "user_tags": ["健身"]},
        {"food_name": "冰淇淋", "food_category": "甜品", "user_tags": ["减肥"]},
        {"food_name": "菠菜", "food_category": "蔬菜", "user_tags": ["孕妇", "营养"]},
        {"food_name": "白酒", "food_category": "酒类", "user_tags": ["孕妇"]}
    ]
    
    for food in test_foods[:2]:
        request_body = food
        start_time = time.time()
        try:
            resp = requests.post(f"{AI_BASE_URL}/food/audit", json=request_body, timeout=30)
            duration = time.time() - start_time
            response = resp.json() if resp.text else None
            log_result(f"食物审核: {food['food_name']}", "/api/v1/food/audit", request_body, response, duration)
        except Exception as e:
            duration = time.time() - start_time
            log_result(f"食物审核: {food['food_name']}", "/api/v1/food/audit", request_body, None, duration, e)

def test_weekly_report():
    """测试5: 周报生成 - /report/weekly-summary"""
    print("\n" + "="*80)
    print("【测试5】周报生成 (Weekly Report)")
    print("="*80)
    
    request_body = {
        "user_profile": {
            "username": "测试用户",
            "gender": "男",
            "age": 28,
            "height": 175,
            "weight": 70,
            "crowd_type": "普通人群"
        },
        "weekly_stats": {
            "days": [
                {"day": "周一", "calories": 1900, "protein": 80, "exercise_minutes": 30},
                {"day": "周二", "calories": 2100, "protein": 85, "exercise_minutes": 45},
                {"day": "周三", "calories": 1800, "protein": 70, "exercise_minutes": 20},
                {"day": "周四", "calories": 2000, "protein": 78, "exercise_minutes": 60},
                {"day": "周五", "calories": 2200, "protein": 82, "exercise_minutes": 35},
                {"day": "周六", "calories": 2500, "protein": 90, "exercise_minutes": 90},
                {"day": "周日", "calories": 1950, "protein": 75, "exercise_minutes": 0}
            ],
            "avg_calories": 2050,
            "avg_protein": 80,
            "total_exercise_minutes": 280,
            "weight_change": "+0.2kg"
        }
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/report/weekly-summary", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("周报生成", "/api/v1/report/weekly-summary", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("周报生成", "/api/v1/report/weekly-summary", request_body, None, duration, e)

def test_article_generate():
    """测试6: 文章生成 - /article/generate"""
    print("\n" + "="*80)
    print("【测试6】文章生成 (Article Generate)")
    print("="*80)
    
    topics = [
        {"topic": "糖尿病患者如何科学饮食", "target_crowd": "糖尿病"},
        {"topic": "秋季养生饮食指南", "target_crowd": "普通人群"}
    ]
    
    for topic_data in topics[:1]:
        request_body = topic_data
        start_time = time.time()
        try:
            resp = requests.post(f"{AI_BASE_URL}/article/generate", json=request_body, timeout=60)
            duration = time.time() - start_time
            response = resp.json() if resp.text else None
            log_result(f"文章生成: {topic_data['topic']}", "/api/v1/article/generate", request_body, response, duration)
        except Exception as e:
            duration = time.time() - start_time
            log_result(f"文章生成: {topic_data['topic']}", "/api/v1/article/generate", request_body, None, duration, e)

def test_meal_parse():
    """测试7: 饮食解析 - /meal/parse"""
    print("\n" + "="*80)
    print("【测试7】饮食解析 (Meal Parse)")
    print("="*80)
    
    test_texts = [
        {"text": "早上吃了一碗面条，一个鸡蛋，一杯豆浆", "meal_type": "早餐"},
        {"text": "中午吃了米饭、宫保鸡丁、鱼香肉丝和一碗紫菜蛋花汤", "meal_type": "午餐"},
        {"text": "晚饭不吃了，减肥期间只吃一个苹果", "meal_type": "晚餐"},
        {"text": "运动后吃了两个鸡蛋清，一根香蕉，喝了一瓶运动饮料", "meal_type": "加餐"}
    ]
    
    for meal_data in test_texts[:3]:
        request_body = meal_data
        start_time = time.time()
        try:
            resp = requests.post(f"{AI_BASE_URL}/meal/parse", json=request_body, timeout=30)
            duration = time.time() - start_time
            response = resp.json() if resp.text else None
            log_result(f"饮食解析: {meal_data['text'][:20]}...", "/api/v1/meal/parse", request_body, response, duration)
        except Exception as e:
            duration = time.time() - start_time
            log_result(f"饮食解析: {meal_data['text'][:20]}...", "/api/v1/meal/parse", request_body, None, duration, e)

def test_diet_plan():
    """测试8: 膳食计划 - /diet/plan"""
    print("\n" + "="*80)
    print("【测试8】膳食计划 (Diet Plan)")
    print("="*80)
    
    request_body = {
        "user_profile": {
            "username": "测试用户",
            "gender": "男",
            "age": 28,
            "height": 175,
            "weight": 80,
            "crowd_type": "健身"
        },
        "goal": "增肌",
        "current_calories": 1800,
        "target_calories": 2500
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/diet/plan", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("膳食计划", "/api/v1/diet/plan", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("膳食计划", "/api/v1/diet/plan", request_body, None, duration, e)

def test_recipe_recommend():
    """测试9: 菜谱推荐 - /food/recommend"""
    print("\n" + "="*80)
    print("【测试9】菜谱推荐 (Recipe Recommend)")
    print("="*80)
    
    request_body = {
        "ingredients": ["鸡胸肉", "西兰花", "胡萝卜"],
        "crowd_type": "健身",
        "goal": "增肌"
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/food/recommend", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("菜谱推荐", "/api/v1/food/recommend", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("菜谱推荐", "/api/v1/food/recommend", request_body, None, duration, e)

def test_exercise_advice():
    """测试10: 运动建议 - /exercise/advice"""
    print("\n" + "="*80)
    print("【测试10】运动建议 (Exercise Advice)")
    print("="*80)
    
    request_body = {
        "user_profile": {
            "username": "测试用户",
            "gender": "男",
            "age": 28,
            "height": 175,
            "weight": 75,
            "crowd_type": "普通人群"
        },
        "goal": "减脂",
        "preferences": "喜欢跑步和骑行",
        "chronic_diseases": ["轻度高血压"]
    }
    
    start_time = time.time()
    try:
        resp = requests.post(f"{AI_BASE_URL}/exercise/advice", json=request_body, timeout=30)
        duration = time.time() - start_time
        response = resp.json() if resp.text else None
        log_result("运动建议", "/api/v1/exercise/advice", request_body, response, duration)
    except Exception as e:
        duration = time.time() - start_time
        log_result("运动建议", "/api/v1/exercise/advice", request_body, None, duration, e)

def test_backend_apis():
    """测试11: 后端基础API"""
    print("\n" + "="*80)
    print("【测试11】后端基础API")
    print("="*80)
    
    apis = [
        ("GET", "/articles", None, "文章列表"),
        ("GET", "/articles?audience=老年人", None, "按人群筛选文章"),
        ("GET", "/articles?audience=孕妇", None, "孕妇文章筛选"),
        ("GET", "/articles?audience=糖尿病", None, "糖尿病文章筛选"),
        ("GET", "/articles/search?keyword=营养", None, "文章搜索"),
        ("GET", "/articles/1", None, "文章详情")
    ]
    
    for method, path, body, name in apis:
        start_time = time.time()
        try:
            if method == "GET":
                resp = requests.get(f"{BACKEND_URL}{path}", timeout=10)
            duration = time.time() - start_time
            response = resp.json() if resp.text else None
            log_result(name, f"GET {path}", None, response, duration)
        except Exception as e:
            duration = time.time() - start_time
            log_result(name, f"GET {path}", None, duration, e)

def generate_report():
    """生成测试报告"""
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    total_tests = len(results)
    passed = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    avg_duration = sum(r["duration_ms"] for r in results) / total_tests if total_tests > 0 else 0
    
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════════════════════╗
║                              AI 健康助手全功能测试报告                                          ║
║                              生成时间: {report_time}                                              ║
╚══════════════════════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 测试汇总
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  总测试数: {total_tests}
  ✅ 成功: {passed}
  ❌ 失败: {failed}
  ⏱️ 平均耗时: {avg_duration:.2f}ms
  成功率: {(passed/total_tests*100) if total_tests > 0 else 0:.1f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 服务端点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  AI 服务基础URL: {AI_BASE_URL}
  后端服务基础URL: {BACKEND_URL}

  AI 功能列表 (共10个端点):
  ┌─────┬─────────────────────┬──────────────────────────────────────┬────────────┐
  │ 序号 │ 功能名称             │ AI端点                                │ 耗时(ms)    │
  ├─────┼─────────────────────┼──────────────────────────────────────┼────────────┤
"""
    
    # 添加AI功能表格
    feature_map = {}
    for r in results:
        if r["endpoint"].startswith("/api/v1/"):
            feature_name = r["feature"].split(":")[0]
            if feature_name not in feature_map:
                feature_map[feature_name] = []
            feature_map[feature_name].append(r)
    
    idx = 1
    for r in results:
        if r["endpoint"].startswith("/api/v1/"):
            feature_name = r["feature"]
            if ":" in feature_name:
                display_name = feature_name.split(":")[0]
            else:
                display_name = feature_name
            duration = r["duration_ms"]
            status_icon = "✅" if r["status"] == "SUCCESS" else "❌"
            report += f"  │ {idx:2d}  │ {display_name:<20s} │ {r['endpoint']:<38s} │ {duration:>10.2f} │\n"
            idx += 1
    
    report += f"  └─────┴─────────────────────┴──────────────────────────────────────┴────────────┘\n\n"
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 详细测试结果
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # 为每个测试结果添加详情
    for i, r in enumerate(results, 1):
        report += f"""
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 测试 #{i}: {r['feature']}
│ 端点: {r['endpoint']}
│ 状态: {r['status']} | 耗时: {r['duration_ms']}ms
└──────────────────────────────────────────────────────────────────────────────────────────────┘

📤 请求体:
{json.dumps(r['request'], ensure_ascii=False, indent=2) if r['request'] else 'N/A'}

📥 响应:
{json.dumps(r['response'], ensure_ascii=False, indent=2)[:3000] if r['response'] else (r['error'] if r['error'] else '无响应')}

"""
    
    report += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 前后端API调用流程
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  前端(Vue) → 后端(Spring Boot) → AI服务(Python)
  
  ┌──────────────┐     ┌─────────────────┐     ┌─────────────────┐
  │  前端 API     │     │  后端 Controller  │     │  AI 服务         │
  │  (api/index)  │────▶│  (AiConsultCtrl) │────▶│  (Python AI)     │
  └──────────────┘     └─────────────────┘     └─────────────────┘
  
  AI端点映射表:
  ┌──────────────────────┬────────────────────────────────────┬──────────────────────────────┐
  │ 前端方法              │ 后端端点                             │ AI端点                         │
  ├──────────────────────┼────────────────────────────────────┼──────────────────────────────┤
  │ api.ai.consult()     │ POST /api/ai/consult               │ POST /api/v1/chat             │
  │ api.ai.nutritionAnalyze() │ POST /api/ai/nutrition/analyze  │ POST /api/v1/nutrition/analyze│
  │ api.ai.foodAudit()   │ POST /api/ai/food/audit            │ POST /api/v1/food/audit       │
  │ api.ai.voiceParse()  │ POST /api/ai/voice/parse           │ POST /api/v1/voice/parse      │
  │ api.ai.weeklyReport()│ POST /api/ai/report/weekly         │ POST /api/v1/report/weekly-summary │
  │ api.ai.articleGenerate() │ POST /api/ai/article/generate    │ POST /api/v1/article/generate │
  │ api.ai.mealParse()   │ POST /api/ai/meal/parse            │ POST /api/v1/meal/parse       │
  │ api.ai.dietPlan()    │ POST /api/ai/diet/plan             │ POST /api/v1/diet/plan        │
  │ api.ai.generateRecipe() │ POST /api/ai/generate-recipe    │ POST /api/v1/chat (recipe)   │
  │ api.ai.recipeRecommend() │ POST /api/ai/recipe/recommend   │ POST /api/v1/food/recommend  │
  │ api.ai.exerciseAdvice() │ POST /api/ai/exercise/advice    │ POST /api/v1/exercise/advice │
  └──────────────────────┴────────────────────────────────────┴──────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📖 AI 服务功能说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 健康咨询 (/chat)
     - 功能: 基于用户健康数据提供个性化健康建议
     - 输入: 用户问题 + 健康快照(用户资料+身体指标+饮食记录)
     - 输出: 健康建议回复
     
  2. 语音解析 (/voice/parse)
     - 功能: 解析语音转写文本，提取食物和营养信息
     - 输入: 语音识别的文本
     - 输出: 解析出的食物列表和营养数据
     
  3. 营养分析 (/nutrition/analyze)
     - 功能: 分析用户每日营养摄入是否均衡
     - 输入: 用户资料 + 每日营养数据 + 运动数据
     - 输出: 营养评分、分项评分、建议
     
  4. 食物审核 (/food/audit)
     - 功能: 审核食物是否适合特定人群
     - 输入: 食物名称 + 类别 + 用户标签
     - 输出: 审核结果、适合人群、注意事项
     
  5. 周报生成 (/report/weekly-summary)
     - 功能: 生成用户每周健康周报
     - 输入: 用户资料 + 每周统计数据
     - 输出: 周报摘要、趋势分析、建议
     
  6. 文章生成 (/article/generate)
     - 功能: 根据主题和目标人群生成科普文章
     - 输入: 文章主题 + 目标人群
     - 输出: 文章标题、内容、摘要
     
  7. 饮食解析 (/meal/parse)
     - 功能: 解析自然语言描述的饮食内容
     - 输入: 饮食文本 + 餐次类型
     - 输出: 食物列表、营养成分、健康建议
     
  8. 膳食计划 (/diet/plan)
     - 功能: 根据用户目标生成个性化膳食计划
     - 输入: 用户资料 + 目标
     - 输出: 每日食谱、营养配比、注意事项
     
  9. 菜谱推荐 (/food/recommend)
     - 功能: 根据食材和人群推荐菜谱
     - 输入: 可用食材 + 人群类型 + 目标
     - 输出: 推荐菜谱列表
     
  10. 运动建议 (/exercise/advice)
      - 功能: 根据用户情况生成运动建议
      - 输入: 用户资料 + 运动目标 + 偏好
      - 输出: 运动方案、注意事项、禁忌

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 测试完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # 保存报告到文件
    report_file = r"c:\Users\13425\Desktop\个人健康助手\health\test_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n{'='*80}")
    print(f"📄 测试报告已保存至: {report_file}")
    print(f"{'='*80}")
    
    # 同时保存原始JSON结果
    json_file = r"c:\Users\13425\Desktop\个人健康助手\health\test_results.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump({
            "report_time": report_time,
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "avg_duration_ms": round(avg_duration, 2)
            },
            "details": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📄 测试结果JSON已保存至: {json_file}")
    print(f"\n✅ 测试完成!")

def main():
    print("="*80)
    print("🤖 AI 健康助手全功能测试")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"AI服务URL: {AI_BASE_URL}")
    print(f"后端URL: {BACKEND_URL}")
    print("="*80)
    
    # 检查服务是否可用
    print("\n🔍 检查服务可用性...")
    
    ai_available = False
    backend_available = False
    
    try:
        resp = requests.get(f"{AI_BASE_URL}/health", timeout=5)
        ai_available = True
        print(f"  ✅ AI 服务可用 (状态码: {resp.status_code})")
    except:
        try:
            resp = requests.post(f"{AI_BASE_URL}/chat", json={"message": "test"}, timeout=5)
            ai_available = True
            print(f"  ✅ AI 服务可用 (端点响应)")
        except Exception as e:
            print(f"  ❌ AI 服务不可用: {e}")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/articles", timeout=5)
        backend_available = True
        print(f"  ✅ 后端服务可用 (状态码: {resp.status_code})")
    except Exception as e:
        print(f"  ❌ 后端服务不可用: {e}")
    
    if not ai_available:
        print("\n⚠️  AI服务不可用，跳过AI功能测试")
        print("   请先启动AI服务: cd health/ai-service && python main.py")
    else:
        # 执行所有AI测试
        print("\n🚀 开始执行AI功能测试...")
        
        test_chat()
        test_voice_parse()
        test_nutrition_analyze()
        test_food_audit()
        test_weekly_report()
        test_article_generate()
        test_meal_parse()
        test_diet_plan()
        test_recipe_recommend()
        test_exercise_advice()
    
    if not backend_available:
        print("\n⚠️  后端服务不可用，跳过后端API测试")
        print("   请先启动后端服务: cd health/backend-health && java -jar target/health-backend-1.0.0.jar")
    else:
        # 执行后端API测试
        if backend_available:
            test_backend_apis()
    
    # 生成报告
    generate_report()

if __name__ == "__main__":
    main()
