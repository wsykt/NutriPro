"""单用户脚本测试：全量 12 用例（4功能 × 2模式 × 2场景），直接调用 ModeRouter.route

场景划分：
  A方向 = 模板库内已有主诉（增肌/减脂/控糖/保持健康）
  B方向 = 模板库外新主诉（降血压/提升睾酮/缓解水肿/补脑冲刺）
  高性能 = high_performance=True（直接 C 方案云端直出）

运行：
  cd health/ai_service
  python run_single_user_script_test.py
  # 输出：test_output/single_user_test/script_test/run_<时间戳>.json
"""
import sys, os, json, time, traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from llm.router import llm
from vector.retriever import retriever
try:
    retriever.ensure_initial_data()
except Exception as e:
    print(f"[WARN] 向量库初始化跳过: {e}")
from local_fallback_engine import fallback_engine
from services.mode_router import mode_router

mode_router.init(
    llm=llm, retriever=retriever, local_engine=fallback_engine,
    auto_ingest=False,  # 测试避免真实写入知识库
)
if hasattr(settings, "KB_DUP_SIMILARITY_THRESHOLD") and settings.KB_DUP_SIMILARITY_THRESHOLD > 0:
    mode_router.DUP_SIMILARITY_THRESHOLD = settings.KB_DUP_SIMILARITY_THRESHOLD
print(f"[init] llm_mode={settings.LLM_MODE}  向量库={retriever.count() if retriever else 0}条  auto_ingest={mode_router._auto_ingest}")

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "single_user_test", "script_test")
os.makedirs(OUT_DIR, exist_ok=True)

# ==================== 12 用例 ====================
CASES = [
    # ---------- ① 健康问答 qa ----------
    dict(
        case_id="01_qa_高血压_减脂_模板内", label="模板内-减脂", func_type="qa", mode="normal",
        high_performance=False,
        kwargs=dict(
            question="我血压偏高体重也超标，想减脂，日常饮食要注意什么？",
            user_profile=dict(age=45, gender="男", height=172, weight=82, bmi=27.7, crowd_type="高血压",
                              chronic_diseases=["高血压"], allergies=[], dietary_restrictions=[]),
        ),
    ),
    dict(
        case_id="02_qa_老人_降血压_模板外", label="模板外-降血压", func_type="qa", mode="normal",
        high_performance=False,
        kwargs=dict(
            question="70岁女士高血压10年，最近上压150多，日常饮食和生活怎么调？",
            user_profile=dict(age=70, gender="女", height=160, weight=68, bmi=26.6, crowd_type="老年人",
                              chronic_diseases=["高血压"], allergies=[], dietary_restrictions=[]),
        ),
    ),
    dict(
        case_id="03_qa_糖尿病_控糖_高性能", label="高性能-控糖", func_type="qa", mode="high_performance",
        high_performance=True,
        kwargs=dict(
            question="我血糖偏高，一日三餐怎么吃能帮助控糖？",
            user_profile=dict(age=52, gender="女", height=158, weight=62, bmi=24.8, crowd_type="糖尿病",
                              chronic_diseases=["糖尿病"], allergies=[], dietary_restrictions=[]),
        ),
    ),
    # ---------- ② 一日饮食方案 diet_plan ----------
    dict(
        case_id="04_diet_糖尿病_控糖_模板内", label="模板内-控糖", func_type="diet_plan", mode="normal",
        high_performance=False,
        kwargs=dict(
            user_profile=dict(age=38, gender="女", height=160, weight=64, bmi=25.0, crowd_type="糖尿病",
                              chronic_diseases=["糖尿病"], allergies=[], dietary_restrictions=[]),
            goal="控制餐后血糖，减重2公斤",
        ),
    ),
    dict(
        case_id="05_diet_健身_升睾酮_模板外", label="模板外-提升睾酮", func_type="diet_plan", mode="normal",
        high_performance=False,
        kwargs=dict(
            user_profile=dict(age=35, gender="男", height=178, weight=78, bmi=24.6, crowd_type="健身",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="提升睾酮水平，增加男性活力，不升高血糖",
        ),
    ),
    dict(
        case_id="06_diet_青少年_补脑_高性能", label="高性能-高考补脑冲刺", func_type="diet_plan", mode="high_performance",
        high_performance=True,
        kwargs=dict(
            user_profile=dict(age=17, gender="男", height=172, weight=68, bmi=23.0, crowd_type="青少年",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="高三备考，补脑+抗疲劳，控制体重不继续增长",
        ),
    ),
    # ---------- ③ 食材菜谱推荐 food_recommend ----------
    dict(
        case_id="07_food_健身_增肌_模板内", label="模板内-增肌", func_type="food_recommend", mode="normal",
        high_performance=False,
        kwargs=dict(
            ingredients=["鸡胸肉", "西兰花", "糙米", "鸡蛋"],
            crowd_type="健身", goal="增肌减脂",
        ),
    ),
    dict(
        case_id="08_food_健身_备赛脱水_模板外", label="模板外-赛前控盐脱水", func_type="food_recommend", mode="normal",
        high_performance=False,
        kwargs=dict(
            ingredients=["鸡胸肉", "黄瓜", "燕麦", "蛋白粉"],
            crowd_type="健身", goal="赛前一周控盐脱水备赛",
        ),
    ),
    dict(
        case_id="09_food_孕妇_营养_高性能", label="高性能-孕期营养", func_type="food_recommend", mode="high_performance",
        high_performance=True,
        kwargs=dict(
            ingredients=["鸡蛋", "豆腐", "青菜", "小米"],
            crowd_type="孕妇", goal="孕中期均衡营养",
        ),
    ),
    # ---------- ④ 个性化运动方案 exercise ----------
    dict(
        case_id="10_exercise_孕妇_保持健康_模板内", label="模板内-保持健康", func_type="exercise", mode="normal",
        high_performance=False,
        kwargs=dict(
            user_profile=dict(age=29, gender="女", height=162, weight=54, bmi=20.6, crowd_type="孕妇",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="孕期保持健康，控制体重增长",
            preferences="散步、孕妇瑜伽", chronic_diseases=[],
        ),
    ),
    dict(
        case_id="11_exercise_孕妇_缓解水肿_模板外", label="模板外-缓解孕期水肿", func_type="exercise", mode="normal",
        high_performance=False,
        kwargs=dict(
            user_profile=dict(age=31, gender="女", height=165, weight=60, bmi=22.0, crowd_type="孕妇",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="缓解孕晚期下肢水肿", preferences="水中运动", chronic_diseases=[],
        ),
    ),
    dict(
        case_id="12_exercise_老年人_慢病_高性能", label="高性能-高血压中老年减脂", func_type="exercise", mode="high_performance",
        high_performance=True,
        kwargs=dict(
            user_profile=dict(age=62, gender="男", height=170, weight=76, bmi=26.3, crowd_type="老年人",
                              chronic_diseases=["高血压"], allergies=[], dietary_restrictions=[]),
            goal="减脂并控制血压", preferences="快走、太极拳", chronic_diseases=["高血压"],
        ),
    ),
]


def extract_key_fields(func_type, result):
    if func_type == "qa":
        txt = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        return {"len": len(txt), "has_温馨提示": "温馨提示" in txt}
    if not isinstance(result, dict):
        return {"type": type(result).__name__}
    if func_type == "diet_plan":
        return {
            "goal": result.get("goal"),
            "total_calories": result.get("total_calories"),
            "has_daily_plan": isinstance(result.get("daily_plan"), dict) and bool(result["daily_plan"]),
            "has_nutrition": isinstance(result.get("nutrition_breakdown"), dict) and bool(result["nutrition_breakdown"]),
            "tips_len": len(result.get("tips") or []),
            "avoided_len": len(result.get("avoided_foods") or []),
        }
    if func_type == "food_recommend":
        meals = result.get("meal_plan") or []
        return {
            "meals": len(meals),
            "each_ingredients_ok": all(bool(m.get("ingredients")) for m in meals) if meals else False,
            "each_calories_ok": all(m.get("calories_estimate") for m in meals) if meals else False,
        }
    if func_type == "exercise":
        sched = result.get("weekly_schedule") or []
        return {
            "days": len(sched),
            "total_minutes": result.get("weekly_total_minutes"),
            "has_warm/cool": bool(result.get("warm_up")) and bool(result.get("cool_down")),
            "precautions_len": len(result.get("precautions") or []),
            "has_progression": bool(result.get("progression_plan")),
        }
    return {}


def main():
    print("==== 预查：模板库召回 top-1 ====")
    recall_res = {}
    for c in CASES:
        kw = c["kwargs"]
        if c["func_type"] == "qa":
            q = kw["question"]
        elif c["func_type"] == "food_recommend":
            q = f"{kw['crowd_type']} {' '.join(kw['ingredients'][:3])} {kw['goal']}"
        else:
            up = kw.get("user_profile") or {}
            q = f"{up.get('crowd_type','')} {kw.get('goal','')}"
        try:
            hits = mode_router._retriever.search(q, top_k=1) if mode_router._retriever else []
            if hits:
                h = hits[0]
                sim = h.get("similarity", 0)
                meta = h.get("metadata", {})
                print(f"  {c['case_id']:32s} sim={sim:.3f}  hit={meta.get('target_crowd','?')}-{meta.get('bmi_cn','?')}-{meta.get('direction','?')}")
                recall_res[c["case_id"]] = sim
            else:
                print(f"  {c['case_id']:32s} 无召回")
                recall_res[c["case_id"]] = 0.0
        except Exception as e:
            recall_res[c["case_id"]] = 0.0
            print(f"  {c['case_id']:32s} 预查失败: {e}")

    print(f"\n==== 执行 ModeRouter.route 全量 {len(CASES)} 用例 ====")
    results = []
    for i, c in enumerate(CASES, 1):
        t0 = time.time()
        try:
            resp = mode_router.route(c["func_type"], high_performance=c["high_performance"], **c["kwargs"])
        except Exception as e:
            resp = {"mode": "ERROR", "route": "EXCEPTION", "error": f"{type(e).__name__}: {e}",
                    "trace": traceback.format_exc(limit=1)}
        elapsed = time.time() - t0
        route = resp.get("route")
        validation = resp.get("validation", {})
        passed = validation.get("passed")
        result = resp.get("result", {})
        key_fields = extract_key_fields(c["func_type"], result)
        row = {
            "case_id": c["case_id"],
            "label": c["label"],
            "func": c["func_type"],
            "mode": c["mode"],
            "high_performance": c["high_performance"],
            "route": route,
            "valid_passed": passed,
            "valid_issues": validation.get("issues") or validation.get("c_issues") or validation.get("a_issues") or [],
            "recall_sim": recall_res.get(c["case_id"]),
            "elapsed_sec": round(elapsed, 1),
            "timing_ms": resp.get("timing_ms"),
            "request": c["kwargs"],
            "response": result,
            "key_fields": key_fields,
            "error": resp.get("error"),
        }
        results.append(row)
        print(f"[{i:02d}/{len(CASES)}] {c['case_id']:32s} mode={c['mode']:15s} route={route:16s} valid={passed}  {round(elapsed,1)}s  {json.dumps(key_fields, ensure_ascii=False)}")

    # 汇总
    print("\n==== 汇总 ====")
    total = len(results)
    a_pass = sum(1 for r in results if r["route"] in ("A_template_local",) and r["valid_passed"])
    c_pass = sum(1 for r in results if r["route"] in ("C_fallback", "C_direct") and r["valid_passed"])
    exc_cnt = sum(1 for r in results if r["mode"] == "ERROR")
    hp_cnt = sum(1 for r in results if r["mode"] == "high_performance")
    hp_c = sum(1 for r in results if r["mode"] == "high_performance" and r["route"] in ("C_direct", "C_direct_fallback_local"))
    normal_a = sum(1 for r in results if r["mode"] == "normal" and r["route"] == "A_template_local")
    normal_c = sum(1 for r in results if r["mode"] == "normal" and r["route"] == "C_fallback")
    print(f"  用例: {total}  高性能: {hp_cnt}(C直出 {hp_c})  正常模式: A改写 {normal_a}  C回退 {normal_c}  异常: {exc_cnt}")
    print(f"  校验通过率: {sum(1 for r in results if r['valid_passed'])}/{total}")

    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUT_DIR, f"run_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详情已写入: {out_path}")


if __name__ == "__main__":
    main()
