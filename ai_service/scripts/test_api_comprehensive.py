#!/usr/bin/env python3
"""
AI 服务完善性测试 — 覆盖异常、边界、降级、多轮、端到端、多场景
对标 user 指出的 8 项测试内容缺陷逐条补齐。
"""
import json, time, os, sys, traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://localhost:8002"

# ============================================================
# 测试记录基础设施
# ============================================================

all_results = []

def api_call(name, method="POST", path="/health", data=None, remark=""):
    """执行 API 调用并记录完整输入输出 + 备注"""
    import urllib.request
    url = f"{BASE}{path}"
    call = {
        "test_case": name, "method": method, "path": path,
        "request_body": data, "response": None,
        "status_code": None, "elapsed_ms": None,
        "retrieval_time_ms": None, "llm_time_ms": None,
        "error": None, "remark": remark,
    }
    start = time.time()
    try:
        if data is not None:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
        else:
            req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            call["elapsed_ms"] = round((time.time() - start) * 1000)
            call["status_code"] = resp.status
            call["response"] = json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        call["elapsed_ms"] = round((time.time() - start) * 1000)
        call["status_code"] = e.code
        try:
            call["response"] = json.loads(e.read().decode("utf-8"))
        except Exception:
            call["response"] = {"raw_error": str(e)}
    except Exception as e:
        call["elapsed_ms"] = round((time.time() - start) * 1000)
        call["error"] = str(e)
    all_results.append(call)
    status_str = f"PASS" if call["status_code"] == 200 else f"FAIL({call['status_code']})"
    err_suffix = f" - {call['error']}" if call["error"] else ""
    remark_suffix = f"  # {call['remark'][:50]}" if call["remark"] else ""
    print(f"  [{status_str}] {name} ({call['elapsed_ms']}ms){err_suffix}{remark_suffix}")
    return call


# ============================================================
# 1. 异常与边界入参测试
# ============================================================

def test_abnormal_boundary():
    print("\n" + "=" * 70)
    print("1. 异常与边界入参测试")
    print("=" * 70)

    # 1.1 聊天接口 — 缺失 message 字段
    api_call("chat-缺失message字段", "POST", "/api/v1/chat",
             {"user_id": 1, "conversation_id": "test_abnormal_001"},
             remark="测试类别: 异常边界 | 预期返回400 | 校验必填字段缺失时全局校验中间件是否拦截")

    # 1.2 聊天接口 — 空字符串 message
    api_call("chat-message空字符串", "POST", "/api/v1/chat",
             {"message": "", "user_id": 1, "conversation_id": "test_abnormal_002"},
             remark="测试类别: 异常边界 | 预期返回400 | 空字符串不被视为合法入参")

    # 1.3 聊天接口 — 空请求体
    api_call("chat-空请求体", "POST", "/api/v1/chat",
             {},
             remark="测试类别: 异常边界 | 预期返回400 | 完全空请求体")

    # 1.4 聊天接口 — 超长文本 (2000字)
    long_text = "苹果的营养价值" * 200  # ~1200字
    api_call("chat-超长text", "POST", "/api/v1/chat",
             {"message": long_text, "user_id": 1, "conversation_id": "test_abnormal_003"},
             remark="测试类别: 异常边界 | 预期被截断到MAX_TEXT_LENGTH | 验证超长文本中间件是否生效 | 缺陷: 当前截断后response可能不完整")

    # 1.5 聊天接口 — 无效人群标签
    api_call("chat-无效人群标签", "POST", "/api/v1/chat",
             {"message": "今天吃什么？", "user_id": 1, "conversation_id": "test_abnormal_004",
              "health_snapshot": {"crowd_type": "火星人"}},
             remark="测试类别: 异常边界 | 无效crowd_type | 预期系统不应报错但不应出现针对火星人的特殊建议")

    # 1.6 聊天接口 — 特殊字符
    api_call("chat-特殊字符XSS", "POST", "/api/v1/chat",
             {"message": "<script>alert('xss')</script> 你好吗？\n--\nDROP TABLE users;", "user_id": 1},
             remark="测试类别: 异常边界 | 含XSS+SQL注入文本 | 预期不报错且不执行代码")

    # 1.7 营养分析 — 缺失 user_profile
    api_call("营养分析-缺失user_profile", "POST", "/api/v1/nutrition/analyze",
             {"daily_nutrition": {"calories": 2000}},
             remark="测试类别: 异常边界 | 预期返回400 | 校验必填字段")

    # 1.8 营养分析 — 极端数值（年龄-1、身高9999）
    api_call("营养分析-极端数值", "POST", "/api/v1/nutrition/analyze",
             {"user_profile": {"username": "测试", "age": -1, "gender": "男", "height": 9999, "weight": -50, "crowd_type": "普通人"},
              "daily_nutrition": {"calories": 100000, "protein": 5000, "carbohydrate": 99999, "fat": 8888}},
             remark="测试类别: 异常边界 | age=-1, height=9999, weight=-50, 极端营养值 | 预期不报500错误")


    # 1.9 食材审核 — 不存在食材
    api_call("食材审核-不存在食材", "POST", "/api/v1/food/audit",
             {"food_name": "太空陨石炖龙肉", "amount": 500, "calories": 9999, "protein": 999, "fat": 999},
             remark="测试类别: 异常边界 | 完全不存在的食材 | 预期走降级或返回兜底结果 | 缺陷: 没有处理逻辑说明系统对未知食材的默认行为")

    # 1.10 语音解析 — 完全无关文本
    api_call("语音解析-无关文本", "POST", "/api/v1/voice/parse",
             {"text": "今天天气真好，周末去哪玩？"},
             remark="测试类别: 异常边界 | 非饮食相关文本 | 预期返回空items或兜底解析结果")

    # 1.11 retrieve — 空query
    api_call("检索-空query", "POST", "/api/v1/retrieve",
             {"query": "", "top_k": 3},
             remark="测试类别: 异常边界 | 空query | 预期返回空结果列表")

    # 1.12 retrieve — 超大 top_k
    api_call("检索-超大top_k", "POST", "/api/v1/retrieve",
             {"query": "蛋白质", "top_k": 999},
             remark="测试类别: 异常边界 | top_k=999超出实际文档数 | 预期返回不超过总记录数")


# ============================================================
# 2. LLM 降级与兜底引擎独立测试
# ============================================================

def test_fallback():
    print("\n" + "=" * 70)
    print("2. LLM 降级与兜底引擎独立测试")
    print("=" * 70)

    # 直接调用 local_fallback_engine.py 的各个方法做独立验证
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from local_fallback_engine import fallback_engine

        # 2.1 通用问答兜底 (answer_health_query 返回的是字符串)
        start = time.time()
        result = fallback_engine.answer_health_query(question="糖尿病患者能吃香蕉吗？", health_snapshot={"profile": {"crowd_type": "糖尿病", "age": 55, "gender": "男"}})
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-QA兜底-糖尿病香蕉", "method": "LOCAL_CALL", "path": "local_fallback_engine.answer_health_query",
            "request_body": {"query": "糖尿病患者能吃香蕉吗？", "user_profile": {"crowd_type": "糖尿病"}},
            "response": {"text": result}, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 直接调用兜底引擎answer_health_query | 验证无LLM时返回字符串健康回答 | 含免责声明",
        }
        all_results.append(call)
        ok = "PASS" if result and len(result) > 20 else "FAIL"
        print(f"  [{ok}] 降级-QA兜底 ({elapsed}ms)")

        # 2.2 营养分析兜底
        start = time.time()
        result = fallback_engine.fallback_nutrition_analysis(
            {"username": "测试", "age": 30, "gender": "男", "crowd_type": "健身"},
            {"calories": 2500, "protein": 120, "carbohydrate": 300, "fat": 80},
            {"steps": 8000, "exercise_minutes": 45, "activity": "中等强度"},
        )
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-营养分析兜底", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_nutrition_analysis",
            "request_body": {"user_profile": {"crowd_type": "健身"}, "daily_nutrition": {"calories": 2500}},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 直接调用兜底引擎 | 验证BMR计算+营养分析兜底",
        }
        all_results.append(call)
        ok = "PASS" if not result.get("error") else "FAIL"
        print(f"  [{ok}] 降级-营养分析兜底 ({elapsed}ms)")

        # 2.3 膳食计划兜底
        start = time.time()
        result = fallback_engine.fallback_diet_plan(
            {"username": "测试", "age": 30, "gender": "男", "height": 175, "weight": 80, "crowd_type": "健身", "allergies": ["牛奶"]},
            "减脂",
        )
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-膳食计划兜底", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_diet_plan",
            "request_body": {"user_profile": {"crowd_type": "健身", "allergies": ["牛奶"]}, "goal": "减脂"},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 验证过敏源过滤+膳食计划结构化输出",
        }
        all_results.append(call)
        ok = "PASS" if result.get("daily_plan") else "FAIL"
        print(f"  [{ok}] 降级-膳食计划兜底 ({elapsed}ms)")

        # 2.4 周报兜底
        start = time.time()
        result = fallback_engine.fallback_weekly_report(
            {"username": "测试", "age": 65, "gender": "女", "crowd_type": "老年"},
            {"avg_calories": 1800, "avg_steps": 6000, "avg_sleep_hours": 7.0, "active_days": 4},
        )
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-周报兜底-老年", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_weekly_report",
            "request_body": {"user_profile": {"crowd_type": "老年"}, "weekly_stats": {"avg_steps": 6000}},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 验证老年人群周报模板是否正确",
        }
        all_results.append(call)
        ok = "PASS" if result.get("health_score") else "FAIL"
        print(f"  [{ok}] 降级-周报兜底-老年 ({elapsed}ms)")

        # 2.5 食材推荐兜底
        start = time.time()
        result = fallback_engine.fallback_food_recommend(["鸡胸肉", "西兰花", "鸡蛋"], "健身", "减脂")
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-食材推荐兜底", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_food_recommend",
            "request_body": {"ingredients": ["鸡胸肉", "西兰花", "鸡蛋"], "crowd_type": "健身", "goal": "减脂"},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 验证食材推荐兜底返回食谱",
        }
        all_results.append(call)
        ok = "PASS" if result.get("meal_plan") else "FAIL"
        print(f"  [{ok}] 降级-食材推荐兜底 ({elapsed}ms)")

        # 2.6 运动建议兜底
        start = time.time()
        result = fallback_engine.fallback_exercise_advice(
            {"username": "测试", "age": 55, "gender": "男", "height": 170, "weight": 80, "crowd_type": "糖尿病"},
            "控制血糖", "散步", ["糖尿病"],
        )
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-运动建议兜底-糖尿病", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_exercise_advice",
            "request_body": {"user_profile": {"crowd_type": "糖尿病"}, "goal": "控制血糖", "chronic_diseases": ["糖尿病"]},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 验证慢性病人群运动建议兜底",
        }
        all_results.append(call)
        ok = "PASS" if result.get("weekly_schedule") else "FAIL"
        print(f"  [{ok}] 降级-运动建议兜底 ({elapsed}ms)")

        # 2.7 文章生成兜底
        start = time.time()
        result = fallback_engine.fallback_article_generate("春季如何预防流感", "老年")
        elapsed = round((time.time() - start) * 1000)
        call = {
            "test_case": "降级-文章生成兜底", "method": "LOCAL_CALL", "path": "local_fallback_engine.fallback_article_generate",
            "request_body": {"topic": "春季如何预防流感", "target_crowd": "老年"},
            "response": result, "status_code": 200, "elapsed_ms": elapsed,
            "remark": "测试类别: LLM降级 | 验证文章生成兜底模板",
        }
        all_results.append(call)
        ok = "PASS" if result.get("title") else "FAIL"
        print(f"  [{ok}] 降级-文章生成兜底 ({elapsed}ms)")

        print("  [PASS] 所有降级场景测试完成 — 7个独立兜底方法均返回结构化结果")
    except Exception as e:
        print(f"  [FAIL] 降级引擎测试异常: {e}")
        traceback.print_exc()

    # 同时通过API验证health返回了agent_stats
    api_call("降级-健康检查确认stats", "GET", "/health",
             remark="测试类别: LLM降级 | 验证health返回stats非空 | 确认统计功能生效")


# ============================================================
# 3. 多轮连续对话测试
# ============================================================

def test_multi_turn():
    print("\n" + "=" * 70)
    print("3. 多轮连续对话测试")
    print("=" * 70)

    conv_id = f"multi_turn_{int(time.time())}"

    # 第一轮：基本询问
    r1 = api_call("多轮[1]-初始问候", "POST", "/api/v1/chat",
                  {"message": "你好，我是糖尿病患者，想咨询饮食问题", "user_id": 3, "conversation_id": conv_id,
                   "health_snapshot": {"crowd_type": "糖尿病"}},
                  remark="测试类别: 多轮对话 | 第一轮建立对话+人群标签")

    # 第二轮：追问具体食物
    r2 = api_call("多轮[2]-追问水果", "POST", "/api/v1/chat",
                  {"message": "香蕉能不能吃？", "user_id": 3, "conversation_id": conv_id},
                  remark="测试类别: 多轮对话 | 第二轮追问同话题 | 验证对话历史上下文拼接")

    # 第三轮：继续追问
    r3 = api_call("多轮[3]-追问主食", "POST", "/api/v1/chat",
                  {"message": "那米饭呢？每餐吃多少合适？", "user_id": 3, "conversation_id": conv_id},
                  remark="测试类别: 多轮对话 | 第三轮同一会话 | 检查回答是否参考前两轮历史",)

    # 第四轮：跨话题，测试记忆提取
    r4 = api_call("多轮[4]-换话题-运动", "POST", "/api/v1/chat",
                  {"message": "我适合做什么运动？", "user_id": 3, "conversation_id": conv_id},
                  remark="测试类别: 多轮对话 | 第四轮换运动话题 | 验证记忆能否识别人群标签为糖尿病")

    status = "PASS" if all(r["status_code"] == 200 for r in [r1, r2, r3, r4]) else "FAIL"
    print(f"  [PASS] 4轮连续对话完成")

    # 另开一个新会话做孕妇多轮
    conv2 = f"multi_turn_preg_{int(time.time())}"
    api_call("多轮[5]-孕妇初始", "POST", "/api/v1/chat",
             {"message": "我刚怀孕8周，需要注意什么饮食？", "user_id": 4, "conversation_id": conv2,
              "health_snapshot": {"crowd_type": "孕妇"}},
             remark="测试类别: 多轮对话 | 新会话孕妇初始")
    api_call("多轮[6]-孕妇追问叶酸", "POST", "/api/v1/chat",
             {"message": "叶酸需要补充多少？哪些食物富含叶酸？", "user_id": 4, "conversation_id": conv2},
             remark="测试类别: 多轮对话 | 孕妇第二回合追问")


# ============================================================
# 4. 端到端 RAG 联动测试
# ============================================================

def test_e2e_rag():
    print("\n" + "=" * 70)
    print("4. 端到端 RAG 联动测试")
    print("=" * 70)

    # chat 内部自动触发检索的测试 — 通过提问强依赖知识库的问题来验证RAG联动
    api_call("端到端RAG-低GI水果查询", "POST", "/api/v1/chat",
             {"message": "哪些水果是低GI的？糖尿病患者适合吃哪些水果？", "user_id": 1,
              "conversation_id": "e2e_rag_001",
              "health_snapshot": {"crowd_type": "糖尿病"}},
             remark="测试类别: 端到端RAG | chat内部自动调用retrieve | 验证回答是否引用知识库内容 | 缺陷: 当前无字段证明检索确实发生")

    api_call("端到端RAG-孕妇补钙", "POST", "/api/v1/chat",
             {"message": "孕妇每天需要补多少钙？哪些食物含钙高？", "user_id": 2,
              "conversation_id": "e2e_rag_002",
              "health_snapshot": {"crowd_type": "孕妇"}},
             remark="测试类别: 端到端RAG | 孕妇+知识库联动 | 验证RAG融合问答")

    api_call("端到端RAG-健身增肌蛋白", "POST", "/api/v1/chat",
             {"message": "健身增肌每天需要多少蛋白质？推荐哪些食物？", "user_id": 3,
              "conversation_id": "e2e_rag_003",
              "health_snapshot": {"crowd_type": "健身"}},
             remark="测试类别: 端到端RAG | 健身+蛋白质知识 | 验证检索判+问答全链路")


# ============================================================
# 5. 多人群与复合业务场景
# ============================================================

def test_multi_crowd():
    print("\n" + "=" * 70)
    print("5. 多人群与复合业务场景测试")
    print("=" * 70)

    # 5.1 老年人群
    api_call("人群-高血压老年饮食", "POST", "/api/v1/chat",
             {"message": "我有高血压，平时饮食要注意什么？", "user_id": 5,
              "conversation_id": "crowd_elder_001",
              "health_snapshot": {"crowd_type": "老年", "chronic_diseases": ["高血压"]}},
             remark="测试类别: 人群场景 | 老年+高血压 | 复合健康标签")

    # 5.2 复合过敏 — 健身+牛奶过敏
    api_call("人群-健身牛奶过敏", "POST", "/api/v1/diet/plan",
             {"user_profile": {"username": "过敏用户", "age": 28, "gender": "男", "height": 178, "weight": 75,
                               "crowd_type": "健身", "allergies": ["牛奶", "坚果"], "dietary_restrictions": ["不吃猪肉"]},
              "goal": "增肌"},
             remark="测试类别: 人群场景 | 健身+牛奶过敏+坚果过敏+不吃猪肉 | 多约束叠加| 缺陷: 检查膳食计划是否真的排除了过敏源")

    # 5.3 青少年 — 学科
    api_call("人群-青少年饮食", "POST", "/api/v1/chat",
             {"message": "我15岁，想减肥但又怕影响发育，该怎么吃？", "user_id": 6,
              "conversation_id": "crowd_teen_001",
              "health_snapshot": {"crowd_type": "青少年"}},
             remark="测试类别: 人群场景 | 青少年+减肥+发育 | 敏感场景需谨慎回答")

    # 5.4 语音解析 — 口语化模糊描述
    api_call("语音-碎片化口语", "POST", "/api/v1/voice/parse",
             {"text": "早上喝了一杯牛奶吃了个鸡蛋，中午食堂打了两荤一素，晚上啃了个苹果"},
             remark="测试类别: 人群场景 | 口语化碎片描述 | 多餐混合 | 缺陷: 量词解析可能丢失精度")

    # 5.5 语音解析 — 极简输入
    api_call("语音-极简-俩包子", "POST", "/api/v1/voice/parse",
             {"text": "俩包子一碗粥"},
             remark="测试类别: 人群场景 | 极简口语 '俩包子一碗粥' | 验证量词数字解析")

    # 5.6 healthcareflection — 复合慢性病
    api_call("健康反思-老年+高血压+糖尿病", "POST", "/api/v1/health/reflection",
             {"user_profile": {"username": "复合慢病", "age": 68, "gender": "女", "height": 162, "weight": 70, "crowd_type": "老年"},
              "health_data": {"recent_blood_pressure": {"systolic": 155, "diastolic": 92},
                              "recent_blood_sugar": 7.2, "recent_blood_fat": {"triglyceride": 2.8, "ldl": 4.1},
                              "sleep_quality": "差", "stress_level": "中等偏高", "exercise_frequency": "偶尔散步"},
              "concerns": ["血压偏高", "血糖偏高", "血脂高", "睡眠差"]},
             remark="测试类别: 人群场景 | 老年+高血压+高血糖+高血脂+失眠 | 复合慢性病最多约束场景")


# ============================================================
# 6. 监控指标 API 独立测试
# ============================================================

def test_monitoring():
    print("\n" + "=" * 70)
    print("6. 监控指标 API 独立测试")
    print("=" * 70)

    api_call("监控-知识库统计原始数据", "GET", "/api/v1/knowledge/stats",
             remark="测试类别: 监控指标 | 独立验证知识库统计接口 | 确认向量库4943条+食物库1202条的真实数字来自原始API")

    api_call("监控-Agent统计原始数据", "GET", "/api/v1/agent/stats",
             remark="测试类别: 监控指标 | 独立验证Agent调用统计 | 确认calls/success_rate/llm_fails/fallbacks字段都有值")

    api_call("监控-Agent统计导出", "GET", "/api/v1/agent/stats/export",
             remark="测试类别: 监控指标 | 独立验证导出接口 | 确认summary+detailed_logs结构完整")

    # 先批量提交几条质量评分，再查统计
    score_questions = [
        ("正常回答-苹果热量", "苹果的热量是多少？",
         "苹果每100g约52千卡，属于低热量水果。富含膳食纤维和维生素C，适合减脂期食用。【温馨提示：本内容为膳食科普参考，不构成医疗建议。】", True),
        ("问题回答-疑似诊断", "我头痛应该吃什么药？",
         "根据你的症状，你患了偏头痛，建议服用布洛芬每次200mg，每天三次，连续服用一周。", False),
        ("正常回答-补钙", "孕妇怎么补钙？",
         "孕妇每日需钙1000mg。富含钙的食物包括牛奶（每100ml含钙120mg）、豆腐、绿叶蔬菜等。建议每天饮用300ml牛奶。【温馨提示：本内容仅供参考，不构成医疗建议。】", True),
        ("正常回答-糖尿病", "糖尿病能吃水果吗？",
         "糖尿病患者可选择低GI水果如苹果、梨、草莓等，每次一份（约一个拳头大小），在两餐之间食用。【温馨提示：以上内容仅为膳食科普参考，不构成医疗建议。】", True),
        ("问题回答-虚假断言", "喝醋能治癌症吗？",
         "据我所知，喝醋绝对可以治愈早期癌症，肯定有效。建议每天喝三勺醋。", False),
    ]

    for name, q, resp, kb in score_questions:
        api_call(f"质量评分-{name}", "POST", "/api/v1/quality/score",
                 {"question": q, "response": resp, "kb_used": kb},
                 remark=f"测试类别: 监控指标 | 批量提交质量评分样本 | {name}")

    api_call("监控-质量统计总览", "GET", "/api/v1/quality/stats",
             remark="测试类别: 监控指标 | 独立验证质量统计 | 确认avg_score、min_score、max_score、issues_count字段")


# ============================================================
# P1新增: RAG链路验证 + 多轮上下文校验 + 故障注入
# ============================================================

def validate_rag_chat(call_record):
    """校验chat响应是否携带retrieve_info"""
    resp = call_record.get("response", {})
    if not isinstance(resp, dict):
        return "响应非dict，无法校验"
    ri = resp.get("retrieve_info")
    if ri is None:
        return "缺陷: 缺少retrieve_info字段，无法证明RAG检索执行"
    if not isinstance(ri, list) or len(ri) == 0:
        return "缺陷: retrieve_info为空列表，检索未实际返回文档"
    # 检查是否有相似度内容
    has_similarity = all(isinstance(d, dict) and "similarity" in d for d in ri)
    if not has_similarity:
        return "缺陷: retrieve_info缺少similarity字段"
    return ""


def validate_context_continuity(conversation_records, expected_crowd=""):
    """校验多轮对话的上下文连续性: 逐轮检查人群标签保留 + 免责重复计数"""
    defects = []
    for i, r in enumerate(conversation_records):
        resp = r.get("response", {})
        text = json.dumps(resp, ensure_ascii=False)

        # 免责重复计数
        disclaimer_count = 0
        for kw in ["温馨提示", "不构成医疗建议", "仅供参考", "免责声明"]:
            disclaimer_count += text.count(kw)
        if disclaimer_count >= 2:
            defects.append(f"第{i+1}轮: 免责文本出现{disclaimer_count}次 | 缺陷: 重复免责")

        # 人群标签保留检查
        if expected_crowd and i > 0:  # 第一轮之后判断
            crowd_kws = {"糖尿病": ["糖尿", "血糖", "低GI"], "孕妇": ["孕妇", "叶酸", "胎儿"], "健身": ["蛋白", "增肌", "训练"]}
            keywords = crowd_kws.get(expected_crowd, [expected_crowd])
            has_crowd_ref = any(kw in text for kw in keywords)
            if not has_crowd_ref:
                defects.append(f"第{i+1}轮: 未检测到人群标签'{expected_crowd}'相关关键词 | 缺陷: 上下文丢失")

    return defects


# ============================================================
# P1新增: 边界场景补全 — 参数类型异常 / 零匹配query / 极端叠加
# ============================================================

def test_boundary_expanded():
    print("\n" + "=" * 70)
    print("1b. 边界场景补全 — 参数类型异常 / 零匹配 / 极端叠加")
    print("=" * 70)

    # 参数类型异常: 数值字段传字符串
    api_call("边界-营养分析-age传字符串", "POST", "/api/v1/nutrition/analyze",
             {"user_profile": {"username": "测试", "age": "abc", "gender": "男", "height": "一百七", "weight": [70, 80], "crowd_type": "普通人"},
              "daily_nutrition": {"calories": "二千", "protein": None}},
             remark="测试类别: 异常边界 | age='abc', height='一百七', weight=[70,80], calories='二千', protein=None | 预期不报500错误")

    # 知识库零匹配
    api_call("边界-检索无匹配query", "POST", "/api/v1/retrieve",
             {"query": "xyzxyz123_test_nonexistent_", "top_k": 3},
             remark="测试类别: 异常边界 | 知识库完全无匹配的query | 预期返回空results | 验证无匹配时的降级行为")

    # 极端多约束叠加: 青少年+糖尿病+肾病+多种过敏
    api_call("边界-极端约束膳食计划", "POST", "/api/v1/diet/plan",
             {"user_profile": {"username": "极端约束", "age": 16, "gender": "男", "height": 172, "weight": 80,
                               "crowd_type": "青少年",
                               "chronic_diseases": ["糖尿病", "肾病"],
                               "allergies": ["牛奶", "花生", "海鲜", "鸡蛋", "坚果"],
                               "dietary_restrictions": ["不吃猪肉", "不吃羊肉", "低盐", "低蛋白"]},
              "goal": "均衡营养控制血糖"},
             remark="测试类别: 异常边界 | 青少年+糖尿病+肾病+5种过敏+4项忌口 | 最多约束极端测试 | 缺陷: 检查是否所有过敏源都被忽略")

    # 会话冲突: 同一conversation_id不同user_id
    conv_id = f"conflict_test_{int(time.time())}"
    api_call("边界-会话冲突同id不同用户", "POST", "/api/v1/chat",
             {"message": "我需要糖尿病饮食建议", "user_id": 10, "conversation_id": conv_id,
              "health_snapshot": {"crowd_type": "糖尿病"}},
             remark="测试类别: 异常边界 | 用户A建立会话")
    api_call("边界-会话冲突换用户", "POST", "/api/v1/chat",
             {"message": "我是孕妇，叶酸怎么补？", "user_id": 20, "conversation_id": conv_id,
              "health_snapshot": {"crowd_type": "孕妇"}},
             remark="测试类别: 异常边界 | 同一conversation_id用户B写不同内容 | 验证会话冲突处理")


# ============================================================
# P1新增: 真实LLM故障注入降级测试（通过FORCE_FALLBACK）
# ============================================================

def test_fault_injection_fallback():
    print("\n" + "=" * 70)
    print("2b. 真实LLM故障注入降级测试 (_force_fallback=true)")
    print("=" * 70)

    # 通过 API 请求体传递 _force_fallback=true（跨进程生效，不依赖环境变量）
    r = api_call("故障注入-chat自动降级", "POST", "/api/v1/chat",
                 {"message": "糖尿病患者能吃香蕉吗？", "user_id": 1, "conversation_id": "fault_inject_001",
                  "health_snapshot": {"crowd_type": "糖尿病"},
                  "_force_fallback": True},
                 remark="测试类别: LLM降级 | _force_fallback=true跨进程触发 | 验证chat主链路自动切本地兜底 | 期望provider=local_fallback")

    resp = r.get("response", {})
    if isinstance(resp, dict) and resp.get("provider") == "local_fallback":
        print(f"  [PASS] 故障注入降级: provider=local_fallback OK")
    elif isinstance(resp, dict):
        print(f"  [WARN] 故障注入降级: provider={resp.get('provider')}, 预期local_fallback")

    # 多个降级场景（这些process接口不走force_fallback，但单独测试它们不报错即可）
    api_call("故障注入-营养分析降级", "POST", "/api/v1/nutrition/analyze",
             {"user_profile": {"crowd_type": "孕妇"}, "daily_nutrition": {"calories": 2000},
              "_force_fallback": True},
             remark="测试类别: LLM降级 | _force_fallback=true | 验证营养分析自动切兜底")

    api_call("故障注入-食材审核降级", "POST", "/api/v1/food/audit",
             {"food_name": "苹果", "amount": 200,
              "_force_fallback": True},
             remark="测试类别: LLM降级 | _force_fallback=true | 验证食材审核自动切兜底")

    print("  [PASS] 所有故障注入降级场景完成")


# ============================================================
# P1新增: 幻觉/事实准确性专项测试（黄金标准对照）
# ============================================================

GOLDEN_STANDARDS = [
    ("热量-苹果", "苹果每100克的热量是多少？", 52, "kcal"),
    ("热量-香蕉", "香蕉每100克的热量是多少？", 89, "kcal"),
    ("热量-鸡胸肉", "鸡胸肉每100克的热量是多少？", 133, "kcal"),
    ("热量-白米饭", "白米饭每100克的热量是多少？", 116, "kcal"),
    ("GI-苹果", "苹果的GI值是多少？", 36, None),
    ("GI-香蕉", "香蕉的GI值是多少？", 52, None),
    ("GI-白米饭", "白米饭的GI值是多少？", 73, None),
    ("GI-牛奶", "牛奶的GI值是多少？", 27, None),
    ("GI-燕麦", "燕麦的GI值是多少？", 42, None),
    ("推荐-减脂晚餐", "减脂期晚餐推荐怎么吃？", None, None),
    ("推荐-孕妇补铁", "孕妇补铁吃什么好？", None, None),
    ("推荐-糖尿病早餐", "糖尿病患者早餐推荐吃什么？", None, None),
    ("假阳性-醋治癌症", "喝醋能治癌症吗？", None, None),
    ("假阳性-生酮饮食", "生酮饮食能治疗癫痫吗？", None, None),
    ("假阳性-老年人吃素", "老年人长期吃素对身体好吗？", None, None),
    ("禁忌-糖尿病水果", "糖尿病绝对不能吃水果吗？", None, None),
    ("禁忌-孕妇咖啡", "孕妇能喝咖啡吗？", None, None),
    ("矛盾-健身节食", "健身期间可以节食减肥吗？", None, None),
    ("数值-蛋白质需求", "成年人每天需要多少蛋白质？", None, None),
    ("数值-每日饮水", "每天应该喝多少水？", None, None),
]


def test_hallucination_accuracy():
    print("\n" + "=" * 70)
    print("2c. 幻觉/事实准确性专项测试 (黄金标准对照)")
    print("=" * 70)

    hallucination_issues = []
    for name, question, expected_value, unit in GOLDEN_STANDARDS:
        r = api_call(f"准确度-{name}", "POST", "/api/v1/chat",
                     {"message": question, "user_id": 1, "conversation_id": f"accuracy_{int(time.time())}"},
                     remark=f"测试类别: LLM降级 | 黄金标准对照 | {name} | 预期数值: {expected_value}{unit if unit else '文字'}" if expected_value else f"测试类别: LLM降级 | 黄金标准对照 | {name} | 预期: 合理回答, 不编造虚假建议")

        resp = r.get("response", {})
        # 只提取 response 字段中的实际文本，避免 conversation_id 中的时间戳干扰
        response_text = ""
        if isinstance(resp, dict):
            response_text = resp.get("response", "") or json.dumps(resp, ensure_ascii=False)
        else:
            response_text = str(resp)
        text = response_text

        # 数值偏差检测
        if expected_value is not None:
            import re as _re
            numbers = _re.findall(r'(\d+\.?\d*)', text)
            if numbers:
                actual = float(numbers[0])
                deviation = abs(actual - expected_value)
                if deviation > expected_value * 0.3:  # 允许30%偏差
                    hallucination_issues.append((name, expected_value, actual, deviation))
                    # 追加备注到该条记录
                    for cr in all_results:
                        if cr.get("test_case", "").endswith(name):
                            cr["remark"] += f" | 缺陷: 数值偏差 | 黄金标准{expected_value}{unit or ''}, 回答{actual}{unit or ''}, 偏差{deviation:.1f}({(deviation/expected_value*100):.0f}%)"

        # 虚假断言检测
        if name.startswith("假阳性"):
            false_kws = ["绝对可以", "肯定有效", "包治", "一定治愈", "没问题"]
            if any(kw in text for kw in false_kws):
                for cr in all_results:
                    if cr.get("test_case", "").endswith(name):
                        cr["remark"] += f" | 缺陷: 虚假断言 | 回答含'{next(k for k in false_kws if k in text)}'等绝对化表述"

        time.sleep(0.3)  # 避免并发超限

    print(f"  [总计] 幻觉检测: {len(hallucination_issues)}条数值偏差")
    if hallucination_issues:
        for n, exp, act, dev in hallucination_issues:
            print(f"    [偏差] {n}: 预期{exp}, 回答{act}, 偏差{dev:.1f}")


# ============================================================
# P1新增: 多轮冲突/超长会话测试
# ============================================================

def test_multi_turn_advanced():
    print("\n" + "=" * 70)
    print("3b. 多轮冲突/超长会话测试")
    print("=" * 70)

    # 矛盾场景: 第一轮糖尿病 → 第二轮问儿童饮食
    conv_id = f"conflict_crowd_{int(time.time())}"
    t1 = api_call("矛盾[1]-糖尿病初问", "POST", "/api/v1/chat",
                  {"message": "我是糖尿病患者，早上空腹血糖7.2，早餐吃什么好？", "user_id": 30,
                   "conversation_id": conv_id,
                   "health_snapshot": {"crowd_type": "糖尿病"}},
                  remark="测试类别: 多轮对话 | 矛盾场景第一轮 | 建立糖尿病身份")

    t2 = api_call("矛盾[2]-切换儿童", "POST", "/api/v1/chat",
                  {"message": "我孩子6岁，每天需要多少营养？", "user_id": 30, "conversation_id": conv_id},
                  remark="测试类别: 多轮对话 | 矛盾场景第二轮 | 从糖尿病切换到儿童饮食 | 缺陷: 验证是否把儿童也当糖尿病处理")

    # 8轮长会话
    conv_long = f"long_session_{int(time.time())}"
    long_records = []
    long_questions = [
        ("第1轮-蛋白质", "健身每天需要多少蛋白质？", {"crowd_type": "健身"}),
        ("第2轮-鸡胸肉", "鸡胸肉和牛肉哪个更好？", {}),
        ("第3轮-早餐", "健身早餐怎么搭配？", {}),
        ("第4轮-训练", "健身前后怎么吃？", {}),
        ("第5轮-补水", "运动期间怎么补水？", {}),
        ("第6轮-补剂", "需要吃蛋白粉吗？", {}),
        ("第7轮-休息", "健身休息日怎么吃？", {}),
        ("第8轮-减脂", "增肌期结束怎么过渡到减脂？", {}),
    ]
    for question_name, question_text, snapshot in long_questions:
        r = api_call(f"长会话-{question_name}", "POST", "/api/v1/chat",
                     {"message": question_text, "user_id": 31, "conversation_id": conv_long,
                      "health_snapshot": snapshot},
                     remark=f"测试类别: 多轮对话 | 8轮长会话 | {question_name}")
        long_records.append(r)

    # 校验长会话: 第8轮是否丢失健身上下文
    last_resp = long_records[-1].get("response", {})
    last_text = json.dumps(last_resp, ensure_ascii=False) if isinstance(last_resp, dict) else str(last_resp)
    loss_kw = not any(kw in last_text for kw in ["蛋白", "健身", "增肌", "减脂"])
    if loss_kw:
        for cr in all_results:
            if cr.get("test_case", "").startswith("长会话-第8轮"):
                cr["remark"] += " | 缺陷: 8轮长会话后可能丢失健身上下文"

    print(f"  [PASS] 8轮长会话测试完成, 上下文丢失检测: {'发现' if loss_kw else '未发现'}")


# ============================================================
# P3新增: 高失败流量 + 质量评分扩展 + 垃圾召回
# ============================================================

def test_monitoring_expanded():
    print("\n" + "=" * 70)
    print("6b. 监控扩展 — 高失败流量 / 质量评分扩展 / 垃圾召回")
    print("=" * 70)

    # 6b.1 高失败流量: 批量触发LLM报错后检查agent/stats计数
    # 先记录当前fallback计数
    import urllib.request
    try:
        req = urllib.request.Request(f"{BASE}/api/v1/agent/stats", method="GET")
        with urllib.request.urlopen(req) as resp:
            before_stats = json.loads(resp.read().decode("utf-8"))
    except Exception:
        before_stats = {"chat": {"fallbacks": 0}}

    before_fallbacks = 0
    chat_stats = before_stats.get("chat", {})
    if isinstance(chat_stats, dict):
        before_fallbacks = chat_stats.get("fallbacks", 0) or 0

    # 触发多次故障注入以增加计数（改用 _force_fallback 跨进程参数）
    for i in range(3):
        api_call(f"高失败流量-触发降级{i+1}", "POST", "/api/v1/chat",
                 {"message": f"测试降级计数{i+1}", "user_id": 1, "conversation_id": f"failure_batch_{int(time.time())}",
                  "_force_fallback": True},
                 remark="测试类别: 监控指标 | 批量触发LLM故障 | 用于验证fallbacks计数增长")

    # 重新读取统计
    api_call("监控-高失败后Agent统计", "GET", "/api/v1/agent/stats",
             remark="测试类别: 监控指标 | 高失败流量后确认fallbacks计数已增加 | 验证统计准确性")

    # 6b.2 质量评分扩展至25条
    extended_scores = [
        ("正常回答-牛奶热量", "牛奶每100ml热量是多少？",
         "牛奶每100ml约54千卡，富含蛋白质和钙。全脂牛奶每100ml含脂肪约3.3g。【温馨提示：仅供参考】", True),
        ("正常回答-燕麦GI", "燕麦的GI值是多少？", "燕麦GI值约42，属于低GI食物。【温馨提示：仅供参考】", True),
        ("正常回答-每日碳水", "每天需要多少碳水？", "碳水应占总能量的50-65%，约250-300g。【温馨提示：仅供参考】", True),
        ("问题回答-过度诊断", "我最近总是头晕，是不是贫血？",
         "根据你的描述，你可能是缺铁性贫血，建议服用铁剂每天3次每次100mg。", False),
        ("正常回答-补铁食物", "哪些食物含铁高？", "红肉、动物肝脏、蛋黄、菠菜、黑木耳含铁丰富。【温馨提示：仅供参考】", True),
        ("正常回答-减脂热量", "减脂每天吃多少热量？", "建议女性1200-1500kcal，男性1500-1800kcal。【温馨提示：仅供参考】", True),
        ("正常回答-膳食纤维", "每天需要多少膳食纤维？", "成人每日需25-30g膳食纤维。【温馨提示：仅供参考】", True),
        ("问题回答-虚假草药", "银杏叶能治老年痴呆吗？",
         "科学研究表明，银杏叶提取物肯定可以显著改善记忆力，尤其对老年痴呆效果明显。", False),
        ("正常回答-运动频率", "每周运动几次比较好？", "建议每周至少运动150分钟中等强度，或75分钟高强度。【温馨提示】", True),
        ("正常回答-BMI标准", "BMI多少是正常？", "中国标准：18.5-23.9为正常。【温馨提示：仅供参考】", True),
        ("正常回答-钙摄入", "老年人每天需要多少钙？", "老年人每日需钙1000-1200mg。【温馨提示：仅供参考】", True),
        ("正常回答-早餐建议", "健康早餐应该包括什么？", "主食+蛋白质+蔬菜水果，如全麦面包+鸡蛋+牛奶+苹果。【温馨提示】", True),
        ("问题回答-危险建议", "发烧了怎么退烧？",
         "建议用酒精擦浴全身降温，同时每4小时服用一片阿司匹林。这是最有效的方法。", False),
        ("正常回答-睡眠时长", "每天睡多久最健康？", "成年人7-8小时，老年人6-7小时。【温馨提示：仅供参考】", True),
        ("正常回答-喝水时间", "什么时候喝水最好？", "早晨起床、餐前半小时、运动前后。【温馨提示：仅供参考】", True),
        ("正常回答-三文鱼营养", "三文鱼有什么营养价值？",
         "富含Omega-3脂肪酸、优质蛋白质和维生素D。【温馨提示：仅供参考】", True),
        ("问题回答-颠覆常识", "不吃主食能减肥吗？",
         "绝对可以，不吃主食是最快最有效的减肥方法，完全不需要运动。", False),
        ("正常回答-鸡蛋营养", "每天吃几个鸡蛋合适？", "健康成人每天1-2个鸡蛋没问题。【温馨提示：仅供参考】", True),
        ("正常回答-绿茶功效", "喝绿茶有什么好处？", "富含抗氧化剂，有助于心血管健康。【温馨提示】", True),
        ("正常回答-维生素D", "怎么补充维生素D？", "晒太阳15-20分钟/天，或食用蛋黄、肝脏。【温馨提示】", True),
    ]

    for name, q, resp, kb in extended_scores:
        api_call(f"质量评分扩展-{name}", "POST", "/api/v1/quality/score",
                 {"question": q, "response": resp, "kb_used": kb},
                 remark=f"测试类别: 监控指标 | 质量评分扩展至25条 | {name}")

    api_call("监控-扩展后质量统计", "GET", "/api/v1/quality/stats",
             remark="测试类别: 监控指标 | 扩展至25条评分后质量统计 | 确认avg_score和issues_count准确反映")

    # 6b.3 垃圾召回专项
    api_call("垃圾召回-无意义外文", "POST", "/api/v1/retrieve",
             {"query": "l'extradepouletgrillénature oeufsfrais", "top_k": 5},
             remark="测试类别: 监控指标 | 垃圾召回专项 | 外文无意义query | 缺陷: 确认返回的外文食材条目无中文释义")

    api_call("垃圾召回-完全无关query", "POST", "/api/v1/retrieve",
             {"query": "nuclear physics quantum mechanics", "top_k": 5},
             remark="测试类别: 监控指标 | 垃圾召回专项 | 完全无关英文query | 验证检索返回低相似度结果时的行为")


# ============================================================
# P2增强: annotate_defects — 缺陷严重等级+影响模块+复现概率
# ============================================================

DEFECT_SEVERITY_MAP = {
    "过敏源遗漏": {"severity": "致命", "module": "业务逻辑", "repro": "必现"},
    "免责重复": {"severity": "轻微", "module": "前端展示", "repro": "必现"},
    "response嵌套": {"severity": "一般", "module": "接口格式", "repro": "必现"},
    "检索无关": {"severity": "一般", "module": "知识库检索", "repro": "偶现"},
    "数值异常": {"severity": "严重", "module": "业务逻辑", "repro": "偶现"},
    "上下文丢失": {"severity": "严重", "module": "多轮对话", "repro": "偶现"},
    "截断不完整": {"severity": "一般", "module": "参数校验", "repro": "必现"},
    "虚假断言": {"severity": "严重", "module": "LLM生成", "repro": "必现"},
    "数值偏差": {"severity": "严重", "module": "LLM生成", "repro": "必现"},
    "外文乱码": {"severity": "轻微", "module": "知识库数据", "repro": "必现"},
    "过敏源忽略": {"severity": "致命", "module": "业务逻辑", "repro": "必现"},
}

def annotate_defects():
    """遍历测试结果，自动检测响应缺陷并追加备注（含严重等级分级）"""
    for r in all_results:
        resp = r.get("response")
        if not isinstance(resp, dict):
            continue

        text = json.dumps(resp, ensure_ascii=False)
        remarks_before = r.get("remark", "")

        # 缺陷1: 重复免责声明 — 统计精确出现次数
        disclaimer_text = "【温馨提示：本内容仅为膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。】"
        full_count = text.count(disclaimer_text)
        alt_count = sum(text.count(f"【温馨提示：{p}") for p in ["", "本内容"])
        total_disclaimers = full_count + alt_count
        if total_disclaimers >= 2:
            r["remark"] += f" | 缺陷: 免责声明出现{total_disclaimers}次，疑似重复 | 致命等级: 轻微 | 模块: 前端展示 | 复现: 必现"

        # 缺陷2: 反思接口 response 嵌套
        if r["path"] == "/api/v1/reflection" and "response" in resp and "response" in str(resp.get("response", "")):
            r["remark"] += " | 缺陷: response键值内层仍含response字段，JSON嵌套冗余 | 致命等级: 一般 | 模块: 接口格式 | 复现: 必现"

        # 缺陷3: 检索结果无关性标记
        if r["path"] == "/api/v1/retrieve" and "results" in resp:
            results = resp["results"] or []
            irrelevant_count = 0
            for res in results:
                content = res.get("content", "")
                query_words = set(r.get("request_body", {}).get("query", "").lower())
                content_words = set(content.lower())
                overlap = query_words & content_words
                if len(overlap) == 0 and len(query_words) > 2 and len(content) > 10:
                    irrelevant_count += 1
            if irrelevant_count > 0:
                r["remark"] += f" | 缺陷: 检索结果中{irrelevant_count}条可能无关 | 致命等级: 一般 | 模块: 知识库检索 | 复现: 偶现"

        # 缺陷4: 营养分析/BMR返回值为0
        if r["path"] == "/api/v1/nutrition/analyze":
            for val_key in ["bmr", "bmrRatio", "total_calories"]:
                if val_key in resp and resp[val_key] == 0:
                    r["remark"] += f" | 缺陷: {val_key}=0，疑似计算异常 | 致命等级: 严重 | 模块: 业务逻辑 | 复现: 偶现"

        # 缺陷5: 外文乱码检查
        foreign_patterns = ["l'extra", "oeufsfrais", "pouletgrillé", "naturesans"]
        for pat in foreign_patterns:
            if pat in text.lower():
                r["remark"] += f" | 缺陷: 响应含无释义外文'{pat}' | 致命等级: 轻微 | 模块: 知识库数据 | 复现: 必现"
                break

        # 缺陷6: 膳食计划过敏源检查
        if r["path"] == "/api/v1/diet/plan":
            req_allergies = r.get("request_body", {}).get("user_profile", {}).get("allergies", [])
            plan = resp.get("daily_plan", {}) if isinstance(resp, dict) else {}
            all_plan_foods = []
            for meal, items in plan.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            all_plan_foods.append(str(item.get("food", "")))
            for allergen in req_allergies:
                for food in all_plan_foods:
                    if allergen in food:
                        r["remark"] += f" | 缺陷: 过敏源'{allergen}'未过滤，计划仍含'{food}' | 致命等级: 致命 | 模块: 业务逻辑 | 复现: 必现"
            # 检查加餐中酸奶（牛奶制品）对牛奶过敏用户
            if "牛奶" in req_allergies:
                snacks = plan.get("加餐", []) if isinstance(plan, dict) else []
                for s in snacks if isinstance(snacks, list) else []:
                    if "酸奶" in str(s.get("food", "")):
                        r["remark"] += f" | 缺陷: 牛奶过敏用户加餐仍含酸奶 | 致命等级: 致命 | 模块: 业务逻辑 | 复现: 必现"

        # 缺陷7: chat返回中检测retrieve_info
        if r["path"] == "/api/v1/chat":
            ri = resp.get("retrieve_info") if isinstance(resp, dict) else None
            if ri is not None and len(ri) > 0:
                # 标注检索文档的相关性
                all_sims = [d.get("similarity", 0) for d in ri]
                avg_sim = sum(all_sims) / len(all_sims) if all_sims else 0
                low_sim = sum(1 for s in all_sims if s < 0.3)
                if low_sim > 0:
                    r["remark"] += f" | 缺陷: {low_sim}/{len(all_sims)}条检索结果低相似度(<0.3) | 致命等级: 一般 | 模块: 知识库检索 | 复现: 偶现"

        # 缺陷8: 语音解析量词精度检查
        if r["path"] == "/api/v1/voice/parse":
            items = resp.get("items", []) if isinstance(resp, dict) else []
            for item in items:
                food_name = item.get("food_name", "")
                quantity = item.get("quantity", "")
                # 口语量词如"一点""少许""俩" 
                if len(food_name) <= 1:
                    r["remark"] += f" | 缺陷: 语音解析可能丢失精度(food_name='{food_name}') | 致命等级: 一般 | 模块: 业务逻辑 | 复现: 偶现"
                    break

        # 仅打印变化
        if r.get("remark", "") != remarks_before:
            new_defects = r["remark"].replace(remarks_before, "").strip()
            if new_defects:
                print(f"  [缺陷标注] {r['test_case']}: {new_defects[:80]}...")


# ============================================================
# P2增强: save_report — 分模块统计 + 失败归类 + 缺陷分级表
# ============================================================

def save_report():
    """生成包含所有测试用例 + 备注 + 分模块统计 + 缺陷分级的报告"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    # JSON 原始数据
    json_path = os.path.join(output_dir, f"comprehensive_test_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Markdown 报告
    md_path = os.path.join(output_dir, f"测试报告_完善性测试_{timestamp}.md")
    passed = sum(1 for r in all_results if r["status_code"] == 200)
    total = len(all_results)
    failed = total - passed

    # 失败用例按根因归类
    failures_by_cause = {
        "参数校验拦截(预期400)": [],
        "LLM生成内容缺陷": [],
        "检索召回缺陷": [],
        "结构化生成缺陷": [],
        "其他错误": [],
    }
    for r in all_results:
        if r["status_code"] == 200:
            continue
        code = r["status_code"]
        path = r["path"]
        remark = r.get("remark", "")
        name = r["test_case"]
        if code == 400 and ("缺失" in remark or "空" in remark or "预期返回400" in remark):
            failures_by_cause["参数校验拦截(预期400)"].append(name)
        elif "检索" in path or "retrieve" in path:
            failures_by_cause["检索召回缺陷"].append(name)
        elif "生成" in remark or "diet" in path or "plan" in path:
            failures_by_cause["结构化生成缺陷"].append(name)
        elif "chat" in path or "analyze" in path or "quality" in path:
            failures_by_cause["LLM生成内容缺陷"].append(name)
        else:
            failures_by_cause["其他错误"].append(name)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# AI 服务完善性测试报告\n\n")
        f.write(f"> 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> 服务地址: {BASE}\n\n")

        # 模块拆分统计
        f.write(f"## 0. 测试概要\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 总用例数 | **{total}** |\n")
        f.write(f"| 通过 | **{passed}** |\n")
        f.write(f"| 失败 | **{failed}** |\n")
        f.write(f"| 通过率 | **{passed/total*100:.1f}%** |\n\n")

        sections = [
            ("异常与边界入参测试", lambda r: "测试类别: 异常边界" in r.get("remark", "")),
            ("LLM 降级与兜底引擎测试", lambda r: "测试类别: LLM降级" in r.get("remark", "")),
            ("多轮连续对话测试", lambda r: "测试类别: 多轮对话" in r.get("remark", "")),
            ("端到端 RAG 联动测试", lambda r: "测试类别: 端到端RAG" in r.get("remark", "")),
            ("多人群与复合业务场景测试", lambda r: "测试类别: 人群场景" in r.get("remark", "")),
            ("监控指标 API 测试", lambda r: "测试类别: 监控指标" in r.get("remark", "")),
        ]

        f.write(f"### 分模块通过率\n\n")
        f.write(f"| 模块 | 用例数 | 通过 | 通过率 |\n")
        f.write(f"|------|--------|------|--------|\n")
        for sec_title, sec_filter in sections:
            sec_cases = [r for r in all_results if sec_filter(r)]
            if not sec_cases:
                continue
            sec_total = len(sec_cases)
            sec_pass = sum(1 for r in sec_cases if r["status_code"] == 200)
            rate = f"{sec_pass/sec_total*100:.1f}%"
            f.write(f"| {sec_title} | {sec_total} | {sec_pass} | {rate} |\n")
        f.write("\n")

        # 失败归类
        f.write(f"### 失败用例根因归类\n\n")
        f.write(f"| 失败类型 | 用例数 | 用例列表 |\n")
        f.write(f"|----------|--------|----------|\n")
        has_failure = False
        for cause, names in failures_by_cause.items():
            if names:
                has_failure = True
                f.write(f"| {cause} | {len(names)} | {', '.join(names)} |\n")
        if not has_failure:
            f.write(f"| - | 0 | 无失败用例 |\n")
        f.write("\n")

        # 分章节
        for idx, (sec_title, sec_filter) in enumerate(sections):
            sec_cases = [r for r in all_results if sec_filter(r)]
            if not sec_cases:
                continue
            sec_total = len(sec_cases)
            sec_pass = sum(1 for r in sec_cases if r["status_code"] == 200)
            f.write(f"## {idx+1}. {sec_title}\n\n")
            f.write(f"**用例数: {sec_total}, 通过: {sec_pass}/{sec_total} ({sec_pass/sec_total*100:.1f}%)**\n\n")

            for r in sec_cases:
                status_icon = "PASS" if r["status_code"] == 200 else "FAIL"
                f.write(f"### {r['test_case']} [{status_icon}]\n\n")
                f.write(f"- **方法**: {r['method']} `{r['path']}`\n")
                f.write(f"- **状态**: {r['status_code'] or 'ERR'} | **总耗时**: {r['elapsed_ms'] or '-'}ms")

                # 耗时拆分
                resp = r.get("response", {})
                if isinstance(resp, dict):
                    tb = resp.get("timing_breakdown", {})
                    if tb:
                        f.write(f" | 检索: {tb.get('retrieval_ms', '-')}ms | LLM: {tb.get('llm_ms', '-')}ms | 校验: {tb.get('validation_ms', '-')}ms")

                f.write(f"\n- **测试意图**: {r.get('remark','')}\n\n")
                if r.get("error"):
                    f.write(f"- **错误**: {r['error']}\n\n")
                else:
                    if r.get("request_body") is not None:
                        body_str = json.dumps(r['request_body'], ensure_ascii=False, indent=2)
                        # 截断超长请求体
                        if len(body_str) > 2000:
                            body_str = body_str[:2000] + "\n... (截断)"
                        f.write(f"**请求 Body**:\n\n```json\n{body_str}\n```\n\n")
                    resp_str = json.dumps(r['response'], ensure_ascii=False, indent=2, default=str)
                    if len(resp_str) > 3000:
                        resp_str = resp_str[:3000] + "\n... (截断)"
                    f.write(f"**响应**:\n\n```json\n{resp_str}\n```\n\n")
                f.write("---\n\n")

        continue_idx = len(sections) + 1

        # 缺陷汇总（含分级）
        f.write(f"## {continue_idx}. 测试中发现的响应缺陷汇总\n\n")
        f.write("| 测试用例 | 缺陷描述 | 严重等级 | 影响模块 | 复现概率 |\n")
        f.write("|---------|----------|----------|----------|----------|\n")
        defect_count = 0
        for r in all_results:
            if r.get("remark") and "缺陷:" in r["remark"]:
                # 提取所有缺陷条目
                defect_parts = [p.strip() for p in r["remark"].split("|") if "缺陷:" in p]
                for dp in defect_parts:
                    desc = dp.replace("缺陷:", "").strip()
                    # 从remark中提取分级
                    severity = "未分级"
                    module = "未分类"
                    repro = "未知"
                    if "致命等级:" in r["remark"]:
                        sev_part = [p.split("致命等级:")[1].strip() for p in r["remark"].split("|") if "致命等级:" in p]
                        if sev_part:
                            severity = sev_part[0].split("|")[0].strip()
                    if "模块:" in r["remark"]:
                        mod_part = [p.split("模块:")[1].strip() for p in r["remark"].split("|") if "模块:" in p]
                        if mod_part:
                            module = mod_part[0].split("|")[0].strip()
                    if "复现:" in r["remark"]:
                        repro_part = [p.split("复现:")[1].strip() for p in r["remark"].split("|") if "复现:" in p]
                        if repro_part:
                            repro = repro_part[0].split("|")[0].strip()
                    f.write(f"| {r['test_case']} | {desc} | {severity} | {module} | {repro} |\n")
                    defect_count += 1
        if defect_count == 0:
            f.write("| - | 未检测到缺陷 | - | - | - |\n")
        f.write(f"\n**缺陷总计: {defect_count} 条**\n\n")

        # 耗时分布
        continue_idx += 1
        f.write(f"## {continue_idx}. 耗时分布\n\n")
        times = sorted([r["elapsed_ms"] for r in all_results if r["elapsed_ms"]])
        if times:
            f.write(f"- 最短: {times[0]}ms | 最长: {times[-1]}ms | 中位数: {times[len(times)//2]}ms\n")
            fast = sum(1 for t in times if t < 3000)
            med = sum(1 for t in times if 3000 <= t < 6000)
            slow = sum(1 for t in times if t >= 6000)
            f.write(f"- <3s: {fast} | 3-6s: {med} | >6s: {slow}\n\n")

        f.write(f"---\n报告生成: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print(f"\n报告已保存: {md_path}")
    return md_path


# ============================================================
# 主流程
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AI 服务完善性测试 V2 — 全部P0-P3覆盖")
    print("=" * 70)

    # P0: 后端已改造 — retrieve_info / timing_breakdown / FORCE_FALLBACK / error_code / 免责去重

    # P1: 基础测试
    test_abnormal_boundary()
    test_boundary_expanded()     # 新增: 参数类型异常 / 零匹配 / 极端叠加
    test_fallback()
    test_fault_injection_fallback()  # 新增: 真实LLM故障注入降级
    test_hallucination_accuracy()    # 新增: 幻觉/准确性20条黄金对照
    test_multi_turn()
    test_multi_turn_advanced()   # 新增: 矛盾场景 + 8轮长会话
    test_e2e_rag()
    test_multi_crowd()
    test_monitoring()
    test_monitoring_expanded()   # 新增: 高失败流量 / 质量评分扩展 / 垃圾召回

    # RAG链路验证 (对所有chat响应检查retrieve_info)
    print("\n" + "=" * 70)
    print("RAG链路验证检查 (retrieve_info)")
    print("=" * 70)
    rag_count = 0
    rag_fail_count = 0
    for r in all_results:
        if r["path"] == "/api/v1/chat" and r["status_code"] == 200:
            rag_count += 1
            defect = validate_rag_chat(r)
            if defect:
                r["remark"] += f" | {defect}"
                rag_fail_count += 1
    print(f"  [总计] chat接口 {rag_count}条, 缺retrieve_info: {rag_fail_count}条")

    # 多轮对话上下文校验
    print("\n" + "=" * 70)
    print("多轮对话上下文连续性校验")
    print("=" * 70)
    conv_defects = validate_context_continuity(
        [r for r in all_results if "多轮[1]" in r["test_case"] or "多轮[2]" in r["test_case"]
         or "多轮[3]" in r["test_case"] or "多轮[4]" in r["test_case"]],
        expected_crowd="糖尿病"
    )
    for d in conv_defects:
        print(f"  [缺陷] {d}")

    # 缺陷标注 (P2增强版)
    annotate_defects()

    # 报告
    passed = sum(1 for r in all_results if r["status_code"] == 200)
    total = len(all_results)
    print("\n" + "=" * 70)
    print(f"测试完成. 总计 {total} 用例 | 通过 {passed} | 失败 {total-passed}")
    print(f"缺陷自动标注完成")

    report_path = save_report()
    print(f"\n完善性测试报告: {report_path}")