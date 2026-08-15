#!/usr/bin/env python3
"""AI Service 全量 API 测试脚本 — 保存完整输入输出"""

import json, time, os, sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

BASE = "http://localhost:8002"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

results = []

def api_call(name, method="POST", path="/health", data=None):
    """执行一次 API 调用并记录完整输入输出"""
    url = f"{BASE}{path}"
    call_record = {
        "name": name,
        "method": method,
        "url": url,
        "request_body": data,
        "response": None,
        "status_code": None,
        "elapsed_ms": None,
        "error": None,
    }
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, timeout=60)
        else:
            resp = requests.post(url, json=data, timeout=60)
        call_record["elapsed_ms"] = round((time.time() - start) * 1000)
        call_record["status_code"] = resp.status_code
        call_record["response"] = resp.json() if resp.text else {}
    except Exception as e:
        call_record["elapsed_ms"] = round((time.time() - start) * 1000)
        call_record["error"] = str(e)
    
    results.append(call_record)
    
    # 打印简洁结果
    status = call_record["status_code"] or "ERR"
    elapsed = call_record["elapsed_ms"] or "?"
    err = f" - {call_record['error']}" if call_record['error'] else ""
    print(f"  [{status}] {name} ({elapsed}ms){err}")
    
    return call_record


def save_results():
    """将所有结果保存为 JSON 和 Markdown 文件"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # JSON 原始数据
    json_path = os.path.join(OUTPUT_DIR, f"api_test_results_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nJSON 结果已保存: {json_path}")
    
    # Markdown 可读报告
    md_path = os.path.join(OUTPUT_DIR, f"api_test_results_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# AI 服务全量 API 测试报告\n\n")
        f.write(f"> 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> 服务地址: {BASE}\n\n")
        
        # 汇总表
        total = len(results)
        passed = sum(1 for r in results if r["status_code"] in (200, 201))
        failed = total - passed
        f.write("## 测试汇总\n\n")
        f.write(f"- **总计**: {total} 个 API\n")
        f.write(f"- **通过**: {passed} 个\n")
        f.write(f"- **失败**: {failed} 个\n\n")
        
        f.write("| # | 名称 | 方法 | 路径 | 状态码 | 耗时(ms) |\n")
        f.write("|---|------|------|------|--------|----------|\n")
        for i, r in enumerate(results, 1):
            status = f"✅ {r['status_code']}" if r["status_code"] == 200 else f"❌ {r['status_code']}"
            err_text = f" - {r['error']}" if r['error'] else ""
            f.write(f"| {i} | {r['name']} | {r['method']} | `{r['url'].replace(BASE, '')}` | {status} | {r['elapsed_ms'] or 'ERR'} {err_text}|\n")
        
        f.write("\n---\n\n")
        
        # 详细输入输出
        f.write("## 详细输入输出\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"### {i}. {r['name']}\n\n")
            f.write(f"- **方法**: {r['method']}\n")
            f.write(f"- **路径**: `{r['url'].replace(BASE, '')}`\n")
            f.write(f"- **状态码**: {r['status_code'] or 'ERROR'}\n")
            f.write(f"- **耗时**: {r['elapsed_ms'] or 'N/A'} ms\n")
            
            if r.get("error"):
                f.write(f"- **错误**: {r['error']}\n\n")
            else:
                if r["request_body"] is not None:
                    f.write(f"#### 请求 Body\n\n```json\n{json.dumps(r['request_body'], ensure_ascii=False, indent=2)}\n```\n\n")
                f.write("#### 响应\n\n```json\n")
                if isinstance(r["response"], dict):
                    f.write(f"{json.dumps(r['response'], ensure_ascii=False, indent=2)}\n")
                else:
                    f.write(f"{r['response']}\n")
                f.write("```\n\n")
            f.write("---\n\n")
    
    print(f"Markdown 报告已保存: {md_path}")
    return md_path


# ============================================================
# 开始测试
# ============================================================

print("=" * 70)
print("AI 服务全量 API 测试")
print(f"服务地址: {BASE}")
print("=" * 70)

# 1. 健康检查
print("\n[1/15] 健康检查")
api_call("健康检查", "GET", "/health")

# 2. 聊天接口
print("\n[2/15] 聊天接口")
api_call("聊天-苹果热量", "POST", "/api/v1/chat", {
    "message": "苹果的热量是多少？100克苹果有多少卡路里？",
    "user_id": 1,
    "conversation_id": "test_001",
})

# 3. 聊天-糖尿病
print("\n[3/15] 聊天-糖尿病")
api_call("聊天-糖尿病饮食", "POST", "/api/v1/chat", {
    "message": "糖尿病患者能吃香蕉吗？有什么需要注意的？",
    "user_id": 1,
    "conversation_id": "test_002",
    "health_snapshot": {"crowd_type": "糖尿病"}
})

# 4. 聊天-孕妇
print("\n[4/15] 聊天-孕妇")
api_call("聊天-孕妇叶酸", "POST", "/api/v1/chat", {
    "message": "孕妇需要补充多少叶酸？哪些食物富含叶酸？",
    "user_id": 2,
    "conversation_id": "test_003",
    "health_snapshot": {"crowd_type": "孕妇"}
})

# 5. 知识库检索
print("\n[5/15] 知识库检索")
api_call("知识库检索-低GI食物", "POST", "/api/v1/retrieve", {
    "query": "低GI食物有哪些",
    "top_k": 3,
    "target_crowd": "糖尿病"
})

# 6. 营养分析
print("\n[6/15] 营养分析")
api_call("营养分析", "POST", "/api/v1/nutrition/analyze", {
    "user_profile": {
        "username": "测试用户",
        "age": 30, "gender": "男",
        "height": 175, "weight": 80,
        "crowd_type": "健身"
    },
    "daily_nutrition": {
        "calories": 2500, "protein": 120, "carbohydrate": 300, "fat": 80,
        "diet_fiber": 20, "calcium": 500, "folic_acid": 200, "dha": 0.5
    },
    "daily_exercise": {
        "steps": 8000, "exercise_minutes": 45,
        "activity": "中等强度"
    }
})

# 7. 食材审核
print("\n[7/15] 食材审核")
api_call("食材审核-鸡胸肉", "POST", "/api/v1/food/audit", {
    "food_name": "鸡胸肉",
    "amount": 150,
    "meal_type": "午餐",
    "calories": 200,
    "protein": 30,
    "carbohydrate": 0,
    "fat": 3
})

# 8. 语音解析
print("\n[8/15] 语音解析")
api_call("语音解析", "POST", "/api/v1/voice/parse", {
    "text": "今天中午吃了一份鸡胸肉沙拉和一个苹果"
})

# 9. 周报生成
print("\n[9/15] 周报生成")
api_call("周报生成", "POST", "/api/v1/report/weekly-summary", {
    "user_profile": {
        "username": "测试用户", "age": 30, "gender": "男",
        "crowd_type": "健身"
    },
    "weekly_stats": {
        "health_score": 85, "avg_calories": 2200,
        "avg_steps": 9000, "avg_sleep_hours": 7.5,
        "active_days": 5, "exercise_minutes": 210
    }
})

# 10. 文章生成
print("\n[10/15] 文章生成")
api_call("文章生成-夏季补水", "POST", "/api/v1/article/generate", {
    "topic": "夏季如何科学补水",
    "target_crowd": "普通人"
})

# 11. 膳食计划
print("\n[11/15] 膳食计划")
api_call("膳食计划", "POST", "/api/v1/diet/plan", {
    "user_profile": {
        "username": "测试用户", "age": 30, "gender": "男",
        "height": 175, "weight": 80,
        "crowd_type": "健身",
        "allergies": ["牛奶"],
        "dietary_restrictions": ["不吃牛肉"]
    },
    "goal": "减脂增肌"
})

# 12. AI回答反思
print("\n[12/15] AI回答反思")
api_call("AI回答反思", "POST", "/api/v1/reflection", {
    "question": "糖尿病患者能吃香蕉吗？",
    "response": "香蕉GI值52，属于中GI水果，糖尿病患者可以适量食用，建议每次半根。",
    "rating": 3,
    "reason": "回答不够明确"
})

# 13. 健康反思
print("\n[13/15] 健康反思")
api_call("健康反思", "POST", "/api/v1/health/reflection", {
    "user_profile": {
        "username": "测试用户", "age": 65, "gender": "男",
        "height": 170, "weight": 75,
        "crowd_type": "老年"
    },
    "health_data": {
        "recent_blood_pressure": {"systolic": 145, "diastolic": 90},
        "recent_blood_sugar": 6.5,
        "sleep_quality": "一般",
        "stress_level": "正常",
        "exercise_frequency": "每周2次散步"
    },
    "concerns": ["血压偏高", "血糖偏高"]
})

# 14. 食材菜谱推荐
print("\n[14/15] 食材菜谱推荐")
api_call("食材菜谱推荐", "POST", "/api/v1/food/recommend", {
    "ingredients": ["鸡胸肉", "鸡蛋", "西兰花", "糙米"],
    "crowd_type": "健身",
    "goal": "减脂"
})

# 15. 运动建议
print("\n[15/15] 运动建议")
api_call("运动建议-减脂", "POST", "/api/v1/exercise/advice", {
    "user_profile": {
        "username": "测试用户", "age": 30, "gender": "男",
        "height": 175, "weight": 80,
        "crowd_type": "健身",
        "bmi": 26.1
    },
    "goal": "减脂",
    "preferences": "喜欢跑步和游泳",
    "chronic_diseases": []
})

# 保存结果
print("\n" + "=" * 70)
print("所有测试完成，正在保存结果...")
md_path = save_results()

print(f"\n✅ 测试完成！共 {len(results)} 个 API")
passed = sum(1 for r in results if r["status_code"] == 200)
failed = len(results) - passed
print(f"   通过: {passed}  |  失败: {failed}")
print(f"   报告: {md_path}")
