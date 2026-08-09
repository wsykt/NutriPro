"""单用户真实环境测试：通过 HTTP API 调用 4 个 AI 功能（每功能 2 个代表用例，共 8 次调用）

用例矩阵：
  qa          - 模板内减脂(normal) + 高性能控糖(high_performance)
  diet_plan   - 模板内控糖(normal) + 高性能补脑(high_performance)
  food_recommend - 模板内增肌(normal) + 高性能孕期营养(high_performance)
  exercise    - 模板内保持健康(normal) + 高性能慢病减脂(high_performance)

接口契约：
  POST /api/v1/chat           body={message, health_snapshot:{profile:{...camelCase}}, high_performance}
  POST /api/v1/diet/plan      body={user_profile:{...}, goal, high_performance}
  POST /api/v1/food/recommend body={ingredients, crowd_type, goal, high_performance}
  POST /api/v1/exercise/advice body={user_profile:{...}, goal, preferences, chronic_diseases, high_performance}
  响应均为 success_response 包装：{"success":true,"data":{...}}；JSON 功能的 route/mode/validation 在 data._meta 中

前提：AI 服务已启动（http://localhost:8002）
运行：
  cd health/ai_service
  python run_single_user_real_test.py
  # 输出：test_output/single_user_test/real_env_test/run_<时间戳>.json
"""
import sys, os, json, time, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8002")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "single_user_test", "real_env_test")
os.makedirs(OUT_DIR, exist_ok=True)

CASES = [
    dict(case_id="R01_qa_高血压_减脂_normal", label="模板内-减脂", func="qa", endpoint="/api/v1/chat",
         payload=dict(
             message="我血压偏高体重也超标，想减脂，日常饮食要注意什么？",
             health_snapshot={"profile": {"age": 45, "gender": "男", "height": 172, "weight": 82, "bmi": 27.7,
                                          "crowdType": "高血压", "chronic_diseases": ["高血压"]}},
             high_performance=False)),
    dict(case_id="R02_qa_糖尿病_控糖_highperf", label="高性能-控糖", func="qa", endpoint="/api/v1/chat",
         payload=dict(
             message="我血糖偏高，一日三餐怎么吃能帮助控糖？",
             health_snapshot={"profile": {"age": 52, "gender": "女", "height": 158, "weight": 62, "bmi": 24.8,
                                          "crowdType": "糖尿病", "chronic_diseases": ["糖尿病"]}},
             high_performance=True)),
    dict(case_id="R03_diet_糖尿病_控糖_normal", label="模板内-控糖", func="diet_plan", endpoint="/api/v1/diet/plan",
         payload=dict(
             user_profile={"age": 38, "gender": "女", "height": 160, "weight": 64, "bmi": 25.0,
                           "crowd_type": "糖尿病", "chronic_diseases": ["糖尿病"]},
             goal="控制餐后血糖，减重2公斤",
             high_performance=False)),
    dict(case_id="R04_diet_青少年_补脑_highperf", label="高性能-高考补脑", func="diet_plan", endpoint="/api/v1/diet/plan",
         payload=dict(
             user_profile={"age": 17, "gender": "男", "height": 172, "weight": 68, "bmi": 23.0, "crowd_type": "青少年"},
             goal="高三备考，补脑+抗疲劳，控制体重不继续增长",
             high_performance=True)),
    dict(case_id="R05_food_健身_增肌_normal", label="模板内-增肌", func="food_recommend", endpoint="/api/v1/food/recommend",
         payload=dict(
             ingredients=["鸡胸肉", "西兰花", "糙米", "鸡蛋"],
             crowd_type="健身", goal="增肌减脂",
             high_performance=False)),
    dict(case_id="R06_food_孕妇_营养_highperf", label="高性能-孕期营养", func="food_recommend", endpoint="/api/v1/food/recommend",
         payload=dict(
             ingredients=["鸡蛋", "豆腐", "青菜", "小米"],
             crowd_type="孕妇", goal="孕中期均衡营养",
             high_performance=True)),
    dict(case_id="R07_exercise_孕妇_保持健康_normal", label="模板内-保持健康", func="exercise", endpoint="/api/v1/exercise/advice",
         payload=dict(
             user_profile={"age": 29, "gender": "女", "height": 162, "weight": 54, "bmi": 20.6, "crowd_type": "孕妇"},
             goal="孕期保持健康，控制体重增长", preferences="散步、孕妇瑜伽", chronic_diseases=[],
             high_performance=False)),
    dict(case_id="R08_exercise_老年人_慢病_highperf", label="高性能-高血压中老年减脂", func="exercise", endpoint="/api/v1/exercise/advice",
         payload=dict(
             user_profile={"age": 62, "gender": "男", "height": 170, "weight": 76, "bmi": 26.3,
                           "crowd_type": "老年人", "chronic_diseases": ["高血压"]},
             goal="减脂并控制血压", preferences="快走、太极拳", chronic_diseases=["高血压"],
             high_performance=True)),
]


def extract_key_fields(func, result):
    if func == "qa":
        txt = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        return {"len": len(txt), "has_温馨提示": "温馨提示" in txt}
    if not isinstance(result, dict):
        return {"type": type(result).__name__}
    if func == "diet_plan":
        return {
            "goal": result.get("goal"),
            "total_calories": result.get("total_calories"),
            "has_daily_plan": isinstance(result.get("daily_plan"), dict) and bool(result["daily_plan"]),
            "has_nutrition": isinstance(result.get("nutrition_breakdown"), dict) and bool(result["nutrition_breakdown"]),
            "tips_len": len(result.get("tips") or []),
        }
    if func == "food_recommend":
        meals = result.get("meal_plan") or []
        return {
            "meals": len(meals),
            "each_ingredients_ok": all(bool(m.get("ingredients")) for m in meals) if meals else False,
        }
    if func == "exercise":
        sched = result.get("weekly_schedule") or []
        return {
            "days": len(sched),
            "total_minutes": result.get("weekly_total_minutes"),
            "has_warm/cool": bool(result.get("warm_up")) and bool(result.get("cool_down")),
            "precautions_len": len(result.get("precautions") or []),
        }
    return {}


def call_api(endpoint, payload, timeout=180):
    url = BASE_URL + endpoint
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
        elapsed = time.time() - t0
        return json.loads(raw), elapsed, None
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        return None, elapsed, f"HTTP {e.code}: {e.read().decode('utf-8')[:300]}"
    except Exception as e:
        elapsed = time.time() - t0
        return None, elapsed, f"{type(e).__name__}: {e}"


def parse_data(data, func):
    """从 success_response.data 中提取 route/mode/validation/result。
    qa 返回 orchestrator.chat 结构（response/route/mode/validation 平铺）。
    JSON 功能返回 process 结果，route/mode 在 result._meta 中。"""
    if not isinstance(data, dict):
        return data, None, None, {}, data
    meta = data.get("_meta") if isinstance(data.get("_meta"), dict) else {}
    if func == "qa":
        result = data.get("response", data)
        route = data.get("route")
        mode = data.get("mode")
        validation = data.get("validation") or {}
        return result, route, mode, validation, data
    # JSON 功能
    result = {k: v for k, v in data.items() if k != "_meta"}
    route = meta.get("route")
    mode = meta.get("mode")
    validation = meta.get("validation") or {}
    return result, route, mode, validation, data


def main():
    # 健康检查
    try:
        with urllib.request.urlopen(BASE_URL + "/health", timeout=5) as r:
            health = json.loads(r.read().decode("utf-8"))
        print(f"[health] {BASE_URL} -> {health.get('status')}")
    except Exception as e:
        print(f"[FATAL] AI 服务不可用（{e}）。请先启动 AI 服务再运行本脚本。")
        sys.exit(1)

    print(f"\n==== 真实环境 HTTP 测试：{len(CASES)} 个用例 ====")
    results = []
    for i, c in enumerate(CASES, 1):
        print(f"\n[{i:02d}/{len(CASES)}] {c['case_id']}  POST {c['endpoint']}  high_performance={c['payload'].get('high_performance', False)}")
        resp, elapsed, err = call_api(c["endpoint"], c["payload"])
        if err:
            row = dict(case_id=c["case_id"], label=c["label"], func=c["func"], endpoint=c["endpoint"],
                       request=c["payload"], mode=c["payload"].get("high_performance") and "high_performance" or "normal",
                       route="ERROR", valid_passed=False, valid_issues=[], elapsed_sec=round(elapsed, 1),
                       timing_ms={}, response=None, key_fields={}, error=err)
            print(f"  ✗ 错误: {err}")
            results.append(row)
            continue
        if not resp.get("success", True):
            detail = resp.get("detail") or resp.get("message")
            row = dict(case_id=c["case_id"], label=c["label"], func=c["func"], endpoint=c["endpoint"],
                       request=c["payload"], mode=c["payload"].get("high_performance") and "high_performance" or "normal",
                       route="ERROR", valid_passed=False, valid_issues=[], elapsed_sec=round(elapsed, 1),
                       timing_ms={}, response=resp, key_fields={}, error=json.dumps(resp, ensure_ascii=False)[:300])
            print(f"  ✗ 业务失败: {detail}")
            results.append(row)
            continue
        # chat 返回 success_response 包装（数据在 data）；diet/food/exercise 直接返回结果对象（顶层即结果，含 _meta）
        if isinstance(resp, dict) and "data" in resp:
            data = resp["data"]
            raw = data
        else:
            data = resp
            raw = resp
        result, route, mode, validation, _ = parse_data(data, c["func"])
        passed = validation.get("passed") if isinstance(validation, dict) else None
        if passed is None:
            passed = result is not None
        key_fields = extract_key_fields(c["func"], result)
        timing_ms = raw.get("timing_breakdown") if isinstance(raw, dict) and "timing_breakdown" in raw else \
            (validation.get("timing_ms") if isinstance(validation, dict) else {})
        row = dict(case_id=c["case_id"], label=c["label"], func=c["func"], endpoint=c["endpoint"],
                   request=c["payload"], mode=mode or ("high_performance" if c["payload"].get("high_performance") else "normal"),
                   route=route or "HTTP_200", valid_passed=passed,
                   valid_issues=validation.get("issues") or validation.get("c_issues") or validation.get("a_issues") or [],
                   elapsed_sec=round(elapsed, 1),
                   timing_ms=timing_ms or {},
                   response=result, key_fields=key_fields, error=err)
        results.append(row)
        print(f"  route={route}  mode={mode}  valid={passed}  {round(elapsed,1)}s  {json.dumps(key_fields, ensure_ascii=False)}")

    # 汇总
    print("\n==== 汇总 ====")
    total = len(results)
    ok = sum(1 for r in results if r["valid_passed"])
    err_cnt = sum(1 for r in results if r["route"] == "ERROR")
    hp = [r for r in results if r["mode"] == "high_performance"]
    nm = [r for r in results if r["mode"] == "normal"]
    print(f"  用例: {total}  成功: {ok}  失败: {err_cnt}  校验通过: {ok - err_cnt}/{total}")
    if hp:
        print(f"  高性能: {len(hp)} 个（平均 {sum(r['elapsed_sec'] for r in hp)/len(hp):.1f}s/个）")
    if nm:
        print(f"  正常模式: {len(nm)} 个（平均 {sum(r['elapsed_sec'] for r in nm)/len(nm):.1f}s/个）")

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUT_DIR, f"run_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详情已写入: {out_path}")


if __name__ == "__main__":
    main()
