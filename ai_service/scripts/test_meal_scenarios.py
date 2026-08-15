#!/usr/bin/env python3
"""
三餐场景化综合测试
模拟3个不同用户×3种饮食模式，向 chat API 发送自然语言饮食描述，
记录完整输入输出，并与实际食物数据库交叉校验营养值准确性。
"""
import json, time, os, sys, re, sqlite3

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BASE = "http://localhost:8002"

# ==============================================================
# 食物数据库参照（用于交叉校验 AI 回答中的营养值）
# ==============================================================
DB_FILE = r"C:\Users\13425\Desktop\个人健康助手\health\backend-health\data\health.db"
FOOD_DB_CACHE = {}

def load_food_db():
    """从 SQLite 加载食物营养成分表到缓存"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT food_name, calorie, protein, fat, carb, diet_fiber, gi_value
        FROM food WHERE status = 'approved' AND calorie IS NOT NULL AND calorie > 0
    """)
    for row in cursor.fetchall():
        name, cal, prot, fat, carb, fiber, gi = row
        FOOD_DB_CACHE[name] = {
            "calorie": cal or 0, "protein": prot or 0,
            "fat": fat or 0, "carb": carb or 0,
            "fiber": fiber or 0, "gi": gi or 0,
        }
    conn.close()
    print(f"  食物数据库已加载: {len(FOOD_DB_CACHE)} 条记录")


def lookup_food(food_name):
    """模糊匹配食物名称，返回营养数据"""
    if not food_name:
        return None
    # 精确匹配
    if food_name in FOOD_DB_CACHE:
        return FOOD_DB_CACHE[food_name]
    # 模糊匹配
    for db_name, data in FOOD_DB_CACHE.items():
        if food_name in db_name or db_name in food_name:
            return data
    # 部分匹配
    for db_name, data in FOOD_DB_CACHE.items():
        if any(kw in db_name for kw in [food_name, food_name.replace("(", "").replace(")", "")]):
            return data
    return None


def calculate_expected_nutrition(meals_text):
    """从饮食描述中提取食物和重量，计算预期营养值"""
    expected = {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}
    food_items = []
    
    # 解析 "XXXYYYg" 或 "XXX YYYg" 或 "XXXYYY克" 模式
    patterns = [
        (r'(\D+?)\s*(\d+[\.\d]*)\s*g(?:左右|约)?', 1),     # "鸡胸肉150g"
        (r'(\D+?)\s*(\d+[\.\d]*)\s*克(?:左右|约)?', 1),     # "米饭200克"
        (r'(\D+?)\s*(\d+[\.\d]*)\s*ml', 1),                 # "可乐330ml"
        (r'(\D+?)\s*(\d+[\.\d]*)\s*毫升', 1),               # "牛奶250毫升"
        (r'(\D+?)\s*(\d+[\.\d]*)\s*个', 50),                 # "鸡蛋2个" -> 每个按50g估算
        (r'(\D+?)\s*(\d+[\.\d]*)\s*碗', 200),                # "米饭1碗" -> 每碗按200g估算
        (r'(\D+?)\s*(\d+[\.\d]*)\s*杯', 250),                # "牛奶1杯" -> 每杯按250ml估算
        (r'(\D+?)\s*(\d+[\.\d]*)\s*根', 75),                 # "油条1根" -> 每根按75g估算
    ]
    
    for line in meals_text.split("\n"):
        line = line.strip()
        # 只跳过空行和纯说明行（不含食物描述的）
        if not line or line.startswith("【") or line.startswith("你好") or line.startswith("帮我") or line.startswith("我是一名"):
            continue
        for pattern, multiplier in patterns:
            matches = re.findall(pattern, line)
            for food_name, amount_str in matches:
                try:
                    amount = float(amount_str) * multiplier
                except ValueError:
                    continue
                food_name = food_name.strip()
                # 提取食物关键词
                db_data = lookup_food(food_name)
                if not db_data:
                    # 尝试只匹配最后2-4字
                    for i in range(min(len(food_name), 6), 1, -1):
                        db_data = lookup_food(food_name[-i:])
                        if db_data:
                            break
                if db_data:
                    factor = amount / 100  # 食物数据库是每100g
                    cal = db_data["calorie"] * factor
                    prot = db_data["protein"] * factor
                    fat = db_data["fat"] * factor
                    carb = db_data["carb"] * factor
                    expected["calories"] += cal
                    expected["protein"] += prot
                    expected["fat"] += fat
                    expected["carbs"] += carb
                    food_items.append({
                        "food": food_name, "amount_g": amount,
                        "cal": round(cal, 1), "protein": round(prot, 1),
                        "fat": round(fat, 1), "carb": round(carb, 1),
                        "db_match": next((k for k in FOOD_DB_CACHE if food_name in k or k in food_name), "?")
                    })
    
    expected["calories"] = round(expected["calories"])
    expected["protein"] = round(expected["protein"], 1)
    expected["fat"] = round(expected["fat"], 1)
    expected["carbs"] = round(expected["carbs"], 1)
    return expected, food_items


# ==============================================================
# 测试场景定义
# ==============================================================

TEST_SCENARIOS = [
    # ========== 场景1: 正常成年男性 ==========
    {
        "scenario": "正常成年男性 - 标准饮食",
        "user_profile": {
            "age": 30, "gender": "男", "height_cm": 175, "weight_kg": 75,
            "crowd_type": "普通人", "activity": "每天10000步"
        },
        "full_text": """你好，帮我分析一下我今天的三餐营养。
我是一名30岁男性，身高175cm，体重75kg，每天大约走10000步。

早餐：燕麦片50g，纯牛奶250ml，水煮鸡蛋2个（约100g）

午餐：白米饭200g，鸡胸肉150g，西兰花150g

晚餐：白米饭150g，清蒸鲈鱼150g，炒青菜200g""",
        "description": "正常男性标准均衡饮食"
    },
    {
        "scenario": "正常成年男性 - 偏多饮食",
        "user_profile": {
            "age": 30, "gender": "男", "height_cm": 175, "weight_kg": 75,
            "crowd_type": "普通人", "activity": "每天10000步"
        },
        "full_text": """帮我看看我今天吃了多少营养。
我是30岁男生，175cm，75kg，每天走1万步左右。

早餐：油条2根（约150g），豆浆400ml，大肉包子3个（约300g）

午餐：大碗白米饭350g，红烧五花肉200g，可乐330ml，炒土豆丝200g

晚餐：大碗面条400g，炸鸡腿2个（约300g），炒青菜150g，啤酒500ml""",
        "description": "正常男性偏多饮食（偏高热量）"
    },
    {
        "scenario": "正常成年男性 - 偏少饮食",
        "user_profile": {
            "age": 30, "gender": "男", "height_cm": 175, "weight_kg": 75,
            "crowd_type": "普通人", "activity": "每天10000步"
        },
        "full_text": """帮我算算今天吃的营养够不够。
我30岁男，175cm，75kg，每天走1万步。

早餐：白粥200g，水煮蛋1个（50g）

午餐：小碗米饭100g，清蒸鱼100g，炒生菜150g

晚餐：小碗米饭100g，番茄炒蛋（番茄150g+鸡蛋1个50g），炒菠菜100g""",
        "description": "正常男性偏少饮食（偏低热量）"
    },

    # ========== 场景2: 健身男性 ==========
    {
        "scenario": "健身男性 - 高蛋白饮食",
        "user_profile": {
            "age": 28, "gender": "男", "height_cm": 180, "weight_kg": 80,
            "crowd_type": "健身", "activity": "每天15000步+力量训练"
        },
        "full_text": """我是健身爱好者，帮我分析一下今天的饮食。
28岁男生，180cm，80kg，每天走15000步，加1小时力量训练。

早餐：全麦面包100g，纯牛奶300ml，鸡蛋3个（150g），香蕉1根（150g）

午餐：糙米饭250g，鸡胸肉200g，西兰花200g，红薯100g

晚餐：糙米饭200g，三文鱼150g，炒菠菜200g，豆腐100g""",
        "description": "健身男性高蛋白饮食"
    },

    # ========== 场景3: 老年女性 ==========
    {
        "scenario": "老年女性 - 清淡饮食",
        "user_profile": {
            "age": 65, "gender": "女", "height_cm": 155, "weight_kg": 52,
            "crowd_type": "老年", "activity": "每天3000步"
        },
        "full_text": """帮我看一下我今天的饮食。
我65岁女性，155cm，52kg，每天走3000步左右。

早餐：小米粥200g，水煮蛋1个（50g），小馒头50g

午餐：小碗米饭100g，清蒸鲈鱼100g，炒冬瓜150g

晚餐：白粥150g，蒸蛋100g，炒菠菜100g""",
        "description": "老年女性清淡饮食"
    },
    {
        "scenario": "老年女性 - 偏多饮食",
        "user_profile": {
            "age": 65, "gender": "女", "height_cm": 155, "weight_kg": 52,
            "crowd_type": "老年", "activity": "每天3000步"
        },
        "full_text": """我65岁女的，155cm，52kg，不怎么运动。今天吃了：
早餐：油条2根（150g），豆浆300ml，粽子2个（200g）
午餐：米饭200g，红烧肉150g，炒土豆丝200g，排骨汤1碗
晚餐：米饭150g，炸带鱼150g，炒青菜100g，馒头1个（100g）""",
        "description": "老年女性偏多饮食"
    },
]


def call_chat_api(scenario):
    """调用 chat API 并发起完整会话"""
    import urllib.request
    profile = scenario["user_profile"]
    full_text = scenario["full_text"]
    
    health_snapshot = {
        "profile": {
            "username": f"测试用户",
            "gender": profile["gender"],
            "age": profile["age"],
            "height_cm": profile["height_cm"],
            "weight_kg": profile["weight_kg"],
            "crowdType": profile["crowd_type"],
            "activity": profile.get("activity", ""),
        }
    }
    
    conv_id = f"meal_test_{int(time.time())}_{scenario['scenario'][:6]}"
    
    payload = {
        "message": full_text,
        "user_id": 999,
        "conversation_id": conv_id,
        "health_snapshot": health_snapshot,
    }
    
    url = f"{BASE}/api/v1/chat"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    
    start = time.time()
    call_record = {
        "scenario": scenario["scenario"],
        "description": scenario["description"],
        "user_profile": profile,
        "request": full_text[:300] + "...",
        "response_full": None,
        "elapsed_ms": None,
        "status_code": None,
        "error": None,
    }
    
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            call_record["elapsed_ms"] = round((time.time() - start) * 1000)
            call_record["status_code"] = resp.status
            call_record["response_full"] = json.loads(body)
    except urllib.error.HTTPError as e:
        call_record["elapsed_ms"] = round((time.time() - start) * 1000)
        call_record["status_code"] = e.code
        try:
            call_record["response_full"] = json.loads(e.read().decode("utf-8"))
        except:
            call_record["response_full"] = {"raw_error": str(e)}
    except Exception as e:
        call_record["elapsed_ms"] = round((time.time() - start) * 1000)
        call_record["error"] = str(e)
    
    return call_record


def extract_nutrition_from_response(text):
    """从 AI 回答文本中提取营养数值，用于交叉校验"""
    # 匹配 "热量Xkcal" "XX千卡" "蛋白质Xg" "脂肪Xg" "碳水Xg" 等
    values = {}
    patterns = {
        "calories": [r'热量[约]*(\d+[\.\d]*)', r'(\d+[\.\d]*)\s*kcal', r'(\d+[\.\d]*)\s*千卡'],
        "protein": [r'蛋白质[约]*(\d+[\.\d]*)', r'蛋白[约]*(\d+[\.\d]*)'],
        "fat": [r'脂肪[约]*(\d+[\.\d]*)'],
        "carbs": [r'碳水[约]*(\d+[\.\d]*)', r'碳水化合物[约]*(\d+[\.\d]*)'],
    }
    
    for key, pats in patterns.items():
        for pat in pats:
            matches = re.findall(pat, text)
            if matches:
                try:
                    values[key] = float(matches[-1])  # 取最后出现的最可能是汇总值
                except ValueError:
                    pass
                break
    
    # 尝试提取总热量（最可能出现在"总计"或"总热量"附近）
    total_cal_matches = re.findall(r'(?:总量|总热量|总计|合计)[：:]*[^。]*?(\d+[\.\d]*)\s*(?:kcal|千卡|大卡)', text)
    if total_cal_matches:
        values["total_calories"] = float(total_cal_matches[0])
    
    return values


def check_accuracy(ai_values, expected_values):
    """对比 AI 回答与实际数据库计算值，给出偏差分析"""
    issues = []
    for nutrient, ai_val in ai_values.items():
        if nutrient not in expected_values:
            continue
        exp_val = expected_values[nutrient]
        if exp_val == 0:
            continue
        diff = abs(ai_val - exp_val)
        diff_pct = diff / exp_val * 100
        if diff_pct > 30:
            issues.append({
                "nutrient": nutrient,
                "ai_value": ai_val,
                "expected": exp_val,
                "diff_pct": round(diff_pct, 1),
                "severity": "严重" if diff_pct > 50 else "较大",
            })
        elif diff_pct > 15:
            issues.append({
                "nutrient": nutrient,
                "ai_value": ai_val,
                "expected": exp_val,
                "diff_pct": round(diff_pct, 1),
                "severity": "轻微",
            })
    return issues


# ==============================================================
# 主测试流程
# ==============================================================

def main():
    print("=" * 80)
    print("三餐场景化综合测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 1. 加载食物数据库
    print("\n[1/4] 加载食物数据库...")
    load_food_db()
    
    # 2. 计算每个场景的理论营养值
    print("\n[2/4] 计算各场景理论营养值...")
    for sc in TEST_SCENARIOS:
        expected, items = calculate_expected_nutrition(sc["full_text"])
        sc["expected_nutrition"] = expected
        sc["food_items"] = items
        print(f"  [{sc['scenario']}]")
        print(f"    预期: 热量{expected['calories']}kcal, 蛋白质{expected['protein']}g, 脂肪{expected['fat']}g, 碳水{expected['carbs']}g")
        if items:
            sample_items = [f"{i['food']}({i['amount_g']}g={i['cal']}kcal)" for i in items[:3]]
            print(f"    食物明细(前3): {', '.join(sample_items)}")
    
    # 3. 逐个调用 chat API
    print("\n[3/4] 调用 chat API 进行测试...")
    results = []
    for i, sc in enumerate(TEST_SCENARIOS):
        print(f"\n  === [{i+1}/{len(TEST_SCENARIOS)}] {sc['scenario']} ===")
        print(f"  类型: {sc['description']}")
        
        result = call_chat_api(sc)
        results.append(result)
        
        if result["status_code"] == 200 and result["response_full"]:
            resp_text = result["response_full"].get("response", "")
            elapsed = result["elapsed_ms"]
            print(f"  耗时: {elapsed}ms")
            print(f"  提供者: {result['response_full'].get('provider', 'N/A')}")
            
            # 提取 AI 回答中的营养值
            ai_values = extract_nutrition_from_response(resp_text)
            if ai_values:
                print(f"  AI营养值: {ai_values}")
                
                # 与数据库计算值交叉校验
                issues = check_accuracy(ai_values, sc["expected_nutrition"])
                if issues:
                    print(f"  偏差警告 ({len(issues)}项):")
                    for iss in issues:
                        print(f"    [{iss['severity']}] {iss['nutrient']}: AI={iss['ai_value']}, 数据库={iss['expected']}, 偏差{iss['diff_pct']}%")
                else:
                    print(f"  营养值偏差均在15%以内 √")
            else:
                print(f"  [注意] AI未明确给出营养数值")
            
            # 截取回答前200字（移除所有非GBK字符）
            preview = resp_text[:200].replace("\n", " ")
            preview = preview.encode('gbk', errors='replace').decode('gbk')
            print(f"  回答预览: {preview}...")
        else:
            print(f"  [FAIL] 状态码: {result['status_code']}, 错误: {result.get('error', 'N/A')}")
        
        # 间隔一下，避免并发
        time.sleep(1)
    
    # 4. 生成报告
    print("\n" + "=" * 80)
    print("[4/4] 生成综合测试报告")
    print("=" * 80)
    
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output", f"三餐场景化测试_{time.strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 三餐场景化综合测试报告\n\n")
        f.write(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**测试场景数**: {len(TEST_SCENARIOS)}\n\n")
        
        for i, (sc, result) in enumerate(zip(TEST_SCENARIOS, results)):
            f.write(f"---\n\n")
            f.write(f"## 场景{i+1}: {sc['scenario']}\n\n")
            f.write(f"**描述**: {sc['description']}\n\n")
            
            f.write("### 用户档案\n\n")
            f.write("| 字段 | 值 |\n")
            f.write("|------|----|\n")
            for k, v in sc["user_profile"].items():
                f.write(f"| {k} | {v} |\n")
            
            f.write("\n### 完整用户输入\n\n")
            f.write("```\n")
            f.write(sc["full_text"])
            f.write("\n```\n")
            
            f.write("\n### 理论营养值（基于食物数据库计算）\n\n")
            exp = sc["expected_nutrition"]
            f.write(f"| 营养项 | 数值 |\n")
            f.write(f"|--------|------|\n")
            f.write(f"| 热量 | {exp['calories']} kcal |\n")
            f.write(f"| 蛋白质 | {exp['protein']} g |\n")
            f.write(f"| 脂肪 | {exp['fat']} g |\n")
            f.write(f"| 碳水化合物 | {exp['carbs']} g |\n")
            
            if sc.get("food_items"):
                f.write("\n### 食物明细（数据库匹配）\n\n")
                f.write("| 食物 | 重量(g) | 热量(kcal) | 蛋白质(g) | 脂肪(g) | 碳水(g) | 数据库匹配 |\n")
                f.write("|------|---------|-----------|----------|--------|--------|----------|\n")
                for item in sc["food_items"]:
                    f.write(f"| {item['food']} | {item['amount_g']} | {item['cal']} | {item['protein']} | {item['fat']} | {item['carb']} | {item['db_match']} |\n")
            
            if result["status_code"] == 200 and result["response_full"]:
                resp = result["response_full"]
                f.write(f"\n### AI 返回原始 JSON\n\n")
                f.write(f"```json\n")
                f.write(json.dumps(resp, ensure_ascii=False, indent=2))
                f.write(f"\n```\n")
                
                f.write(f"\n### AI 回答文本（完整）\n\n")
                resp_text = resp.get("response", "")
                f.write(resp_text)
                f.write("\n")
                
                f.write(f"\n### 交叉校验\n\n")
                ai_values = extract_nutrition_from_response(resp_text)
                if ai_values:
                    f.write("| 营养项 | AI回答 | 数据库参考 | 偏差 | 评估 |\n")
                    f.write("|--------|--------|----------|------|------|\n")
                    for nutrient in ["calories", "protein", "fat", "carbs"]:
                        ai_val = ai_values.get(nutrient, "N/A")
                        exp_val = exp.get(nutrient, 0)
                        if ai_val != "N/A" and exp_val > 0:
                            diff = abs(ai_val - exp_val) / exp_val * 100
                            status = "严重" if diff > 50 else ("较大" if diff > 30 else ("轻微" if diff > 15 else "准确"))
                            f.write(f"| {nutrient} | {ai_val} | {exp_val} | {diff:.1f}% | {status} |\n")
                        else:
                            f.write(f"| {nutrient} | {ai_val} | {exp_val} | - | - |\n")
                else:
                    f.write("AI 回答中未提取到结构化营养数值（LLM可能未做数值计算）\n")
                
                if resp.get("retrieve_info"):
                    f.write(f"\n### 知识库检索信息\n\n")
                    for ri in resp["retrieve_info"]:
                        f.write(f"- 来源: {ri.get('source','?')}, 相似度: {ri.get('similarity',0)}, 类别: {ri.get('category','?')}\n")
                
                f.write(f"\n### 性能指标\n\n")
                f.write(f"- **响应耗时**: {result['elapsed_ms']}ms\n")
                f.write(f"- **LLM提供者**: {resp.get('provider', 'N/A')}\n")
                if resp.get("timing_breakdown"):
                    tb = resp["timing_breakdown"]
                    f.write(f"- **检索耗时**: {tb.get('retrieval_ms', 'N/A')}ms\n")
                    f.write(f"- **LLM耗时**: {tb.get('llm_ms', 'N/A')}ms\n")
                    f.write(f"- **校验耗时**: {tb.get('validation_ms', 'N/A')}ms\n")
            else:
                f.write(f"\n### 调用失败\n\n")
                f.write(f"- 状态码: {result['status_code']}\n")
                f.write(f"- 错误: {result.get('error', 'N/A')}\n")
        
        # 总体统计
        f.write(f"\n---\n\n")
        f.write(f"## 总体统计\n\n")
        f.write(f"| 指标 | 值 |\n")
        f.write(f"|------|----|\n")
        f.write(f"| 测试场景数 | {len(TEST_SCENARIOS)} |\n")
        f.write(f"| 调用成功 | {sum(1 for r in results if r['status_code']==200)} |\n")
        f.write(f"| 调用失败 | {sum(1 for r in results if r['status_code']!=200)} |\n")
        if results:
            avg_ms = sum(r['elapsed_ms'] or 0 for r in results) / len(results)
            f.write(f"| 平均耗时 | {avg_ms:.0f}ms |\n")
    
    print(f"\n报告已保存: {report_path}")
    
    # 控制台输出简要结论
    print("\n" + "=" * 80)
    print("简要结论")
    print("=" * 80)
    for sc, result in zip(TEST_SCENARIOS, results):
        status = "OK" if result["status_code"] == 200 else "FAIL"
        el = result["elapsed_ms"] or 0
        if result["response_full"]:
            ai_vals = extract_nutrition_from_response(result["response_full"].get("response", ""))
            issues = check_accuracy(ai_vals, sc["expected_nutrition"]) if ai_vals else []
            issue_count = len(issues)
        else:
            issue_count = -1
        print(f"  [{status}] {sc['scenario']}: {el}ms, 偏差项: {issue_count}")


if __name__ == "__main__":
    main()
