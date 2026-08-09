"""本地模式测试：从35类（7人群×5BMI）挑7样例组合，
每样例×2个方向=14用例：
  A方向=模板库内已有主诉（如增肌/减脂/保持健康）
  B方向=模板库内未明确覆盖的新主诉（如降血压/提升睾酮/缓解孕期水肿/高考冲刺营养...）

统一调用 ModeRouter.route(high_performance=False)
记录：检索命中相似度/是否走A方案/校验是否通过/输出关键字段

运行：
  cd health/ai_service
  python _run_local_mode_14cases.py
  # 输出：_local_mode_14cases_report.json
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings

# 1. 初始化 LLM（强制本地模式，用于A方案改写；C方案若触发也只做一次回退）
from llm.router import llm
# 2. 初始化向量检索器（模板召回用）
from vector.retriever import retriever
try:
    retriever.ensure_initial_data()
except Exception as e:
    print(f"[WARN] 向量库初始化跳过: {e}")
# 3. 初始化本地兜底规则引擎（A方案无模板时走本地规则）
from local_fallback_engine import fallback_engine
# 4. 注入 mode_router：自动入库关闭（测试避免真实写入）
from services.mode_router import mode_router
mode_router.init(
    llm=llm, retriever=retriever, local_engine=fallback_engine,
    auto_ingest=False,
)
if hasattr(settings, "KB_DUP_SIMILARITY_THRESHOLD") and settings.KB_DUP_SIMILARITY_THRESHOLD > 0:
    mode_router.DUP_SIMILARITY_THRESHOLD = settings.KB_DUP_SIMILARITY_THRESHOLD
print(f"[init] llm_mode={settings.LLM_MODE}  向量库={retriever.count() if retriever else 0}条  auto_ingest={mode_router._auto_ingest}")

# 7 样例（7人群各占1档BMI，保证多样性）
CASES = [
    # ---------- 1. qa：老年人×BMI超高 ----------------------------
    dict(
        case_id="01_qa_老人_超高_减脂",
        label_in="模板内-减脂",
        func_type="qa",
        kwargs=dict(
            question="我70岁，身高165体重82，BMI=30.1，关节不好想减肥，怎么做？",
            user_profile=dict(age=70, gender="女", height=165, weight=82, bmi=30.1, crowd_type="老年人",
                              chronic_diseases=["高血压"], allergies=[], dietary_restrictions=[]),
            health_snapshot=dict(blood_pressure="145/90")
        )
    ),
    dict(
        case_id="02_qa_老人_超高_降血压",
        label_in="新方向-降血压",
        func_type="qa",
        kwargs=dict(
            question="70岁女士高血压10年，最近上压150多，日常饮食和生活怎么调？",
            user_profile=dict(age=70, gender="女", height=165, weight=82, bmi=30.1, crowd_type="老年人",
                              chronic_diseases=["高血压"], allergies=[], dietary_restrictions=[]),
            health_snapshot=dict(blood_pressure="152/94")
        )
    ),

    # ---------- 2. diet_plan：糖尿病患者×BMI正常 --------------------
    dict(
        case_id="03_diet_糖尿病_正常_控糖",
        label_in="模板内-控糖",
        func_type="diet_plan",
        kwargs=dict(
            user_profile=dict(age=55, gender="男", height=175, weight=70, bmi=22.9, crowd_type="糖尿病患者",
                              chronic_diseases=["2型糖尿病"], allergies=["海鲜"], dietary_restrictions=["低糖少油"]),
            goal="控制餐后血糖"
        )
    ),
    dict(
        case_id="04_diet_糖尿病_正常_升睾酮",
        label_in="新方向-提升睾酮",
        func_type="diet_plan",
        kwargs=dict(
            user_profile=dict(age=55, gender="男", height=175, weight=70, bmi=22.9, crowd_type="糖尿病患者",
                              chronic_diseases=["2型糖尿病"], allergies=["海鲜"], dietary_restrictions=["低糖少油"]),
            goal="提升睾酮水平，增加男性活力，不升高血糖"
        )
    ),

    # ---------- 3. food_recommend：健身人群×BMI偏低 -----------------
    dict(
        case_id="05_food_健身_偏低_增肌",
        label_in="模板内-增肌",
        func_type="food_recommend",
        kwargs=dict(
            ingredients=["鸡胸肉", "鸡蛋", "西蓝花", "燕麦", "香蕉"],
            crowd_type="健身人群",
            goal="增肌期摄入1.8g蛋白质/kg体重"
        )
    ),
    dict(
        case_id="06_food_健身_偏低_备赛脱水",
        label_in="新方向-赛前控盐脱水",
        func_type="food_recommend",
        kwargs=dict(
            ingredients=["鸡胸肉", "糙米", "芦笋", "黄瓜", "金枪鱼"],
            crowd_type="健身人群",
            goal="健身比赛前一周控盐脱水+维持肌肉线条（3天菜单）"
        )
    ),

    # ---------- 4. exercise：孕妇×BMI偏低 ---------------------------
    dict(
        case_id="07_exercise_孕妇_偏低_保持健康",
        label_in="模板内-保持健康",
        func_type="exercise",
        kwargs=dict(
            user_profile=dict(age=28, gender="女", height=162, weight=52, bmi=19.8, crowd_type="孕妇",
                              chronic_diseases=[], pregnancy_week=20, allergies=[], dietary_restrictions=[]),
            goal="孕中期保持健康体重",
            preferences="室内，无器械",
            chronic_diseases=[]
        )
    ),
    dict(
        case_id="08_exercise_孕妇_偏低_缓解水肿",
        label_in="新方向-缓解孕期水肿",
        func_type="exercise",
        kwargs=dict(
            user_profile=dict(age=28, gender="女", height=162, weight=52, bmi=19.8, crowd_type="孕妇",
                              chronic_diseases=[], pregnancy_week=20, allergies=[], dietary_restrictions=[]),
            goal="缓解脚踝水肿+改善下肢循环",
            preferences="床上/沙发可做，无器械",
            chronic_diseases=[]
        )
    ),

    # ---------- 5. diet_plan：青少年×BMI超高 ----------------------
    dict(
        case_id="09_diet_青少年_超高_减脂",
        label_in="模板内-减脂",
        func_type="diet_plan",
        kwargs=dict(
            user_profile=dict(age=15, gender="男", height=172, weight=88, bmi=29.7, crowd_type="青少年",
                              chronic_diseases=[], allergies=[], dietary_restrictions=["不喝牛奶"]),
            goal="中考体育前3个月减脂到BMI正常，不影响学习"
        )
    ),
    dict(
        case_id="10_diet_青少年_超高_补脑冲刺",
        label_in="新方向-高考补脑冲刺",
        func_type="diet_plan",
        kwargs=dict(
            user_profile=dict(age=17, gender="女", height=162, weight=78, bmi=29.8, crowd_type="青少年",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="高三下学期备考，补脑+抗疲劳，同时控制体重不继续增长"
        )
    ),

    # ---------- 6. qa：通用×BMI正常 -------------------------------
    dict(
        case_id="11_qa_通用_正常_均衡营养",
        label_in="模板内-均衡饮食",
        func_type="qa",
        kwargs=dict(
            question="普通上班族，30岁，BMI22，吃饭总是外卖怎么做到营养均衡？",
            user_profile=dict(age=30, gender="女", height=165, weight=60, bmi=22.0, crowd_type="通用",
                              chronic_diseases=[], allergies=[], dietary_restrictions=["不吃香菜"]),
            health_snapshot=dict()
        )
    ),
    dict(
        case_id="12_qa_通用_正常_倒班调睡眠",
        label_in="新方向-三班倒调睡眠",
        func_type="qa",
        kwargs=dict(
            question="做二休二的倒班制（日班/夜班轮），总睡不够，饮食和作息怎么调整？",
            user_profile=dict(age=32, gender="男", height=178, weight=72, bmi=22.7, crowd_type="通用",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            health_snapshot=dict(sleep_quality="差", shift_work="二休二")
        )
    ),

    # ---------- 7. exercise：普通人×BMI过低 -------------------------
    dict(
        case_id="13_exercise_普通_过低_增重",
        label_in="模板内-增重",
        func_type="exercise",
        kwargs=dict(
            user_profile=dict(age=24, gender="男", height=178, weight=54, bmi=17.0, crowd_type="普通人",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="增重到BMI 19+，增肌为主",
            preferences="在家，一副哑铃即可",
            chronic_diseases=[]
        )
    ),
    dict(
        case_id="14_exercise_普通_过低_纠正圆肩驼背",
        label_in="新方向-纠正圆肩驼背",
        func_type="exercise",
        kwargs=dict(
            user_profile=dict(age=24, gender="男", height=178, weight=54, bmi=17.0, crowd_type="普通人",
                              chronic_diseases=[], allergies=[], dietary_restrictions=[]),
            goal="程序员久坐，纠正圆肩驼背+缓解颈肩疼痛",
            preferences="每天15-20分钟，办公室/家里都能做",
            chronic_diseases=[]
        )
    ),
]


def case_expected_in_template(case_id):
    """判断该用例是否应该在模板内命中（A方向=模板内）"""
    return case_id in {
        "01_qa_老人_超高_减脂", "03_diet_糖尿病_正常_控糖", "05_food_健身_偏低_增肌",
        "07_exercise_孕妇_偏低_保持健康", "09_diet_青少年_超高_减脂",
        "11_qa_通用_正常_均衡营养", "13_exercise_普通_过低_增重",
    }


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
    # 先做一次查询验证：各case的模板库召回相似度
    print("==== 预查：模板库召回 top-1（用 case question/goal 作为查询） ====")
    qs = []
    for c in CASES:
        kw = c["kwargs"]
        if c["func_type"] == "qa":
            q = kw["question"]
        elif c["func_type"] == "food_recommend":
            q = f"{kw['crowd_type']} {' '.join(kw['ingredients'][:3])} {kw['goal']}"
        else:
            up = kw.get("user_profile") or {}
            q = f"{up.get('crowd_type','')} {kw.get('goal','')}"
        qs.append((c["case_id"], c["func_type"], q))

    recall_res = {}
    try:
        for cid, ftype, q in qs:
            hits = mode_router._retriever.search(q, top_k=1) if mode_router._retriever else []
            if hits:
                h = hits[0]
                meta = h.get("metadata", {})
                print(f"  {cid:40s} sim={h.get('similarity'):.3f}  hit={meta.get('target_crowd','?')}-{meta.get('bmi_cn','?')}-{meta.get('direction','?')}  func={meta.get('func_type','?')}")
                recall_res[cid] = h.get('similarity', 0)
            else:
                print(f"  {cid:40s} 无召回")
                recall_res[cid] = 0.0
    except Exception as e:
        print(f"  预查跳过：{e}")

    print("\n==== 执行 ModeRouter.route(high_performance=False) 14个用例 ====")
    results = []
    for i, c in enumerate(CASES, 1):
        t0 = time.time()
        try:
            resp = mode_router.route(c["func_type"], high_performance=False, **c["kwargs"])
        except Exception as e:
            import traceback
            resp = {"mode": "ERROR", "route": "EXCEPTION", "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc(limit=1)}
        elapsed = time.time() - t0
        route = resp.get("route")
        validation = resp.get("validation", {})
        passed = validation.get("passed")
        result = resp.get("result", {})
        key_fields = extract_key_fields(c["func_type"], result)
        in_tpl = case_expected_in_template(c["case_id"])
        row = {
            "case_id": c["case_id"],
            "label": c["label_in"],
            "in_template_expected": in_tpl,
            "func": c["func_type"],
            "route": route,
            "mode": resp.get("mode"),
            "valid_passed": passed,
            "valid_issues": validation.get("issues") or validation.get("c_issues") or validation.get("a_issues") or [],
            "recall_sim": recall_res.get(c["case_id"]),
            "elapsed_sec": round(elapsed, 1),
            "timing_ms": resp.get("timing_ms"),
            "key_fields": key_fields,
            "error": resp.get("error"),
        }
        results.append(row)
        print(f"[{i:02d}/14] {c['case_id']:42s} {c['label_in']:12s}  recall={recall_res.get(c['case_id']):.3f}  route={route:16s}  valid={passed}  {round(elapsed,1)}s  -> {json.dumps(key_fields, ensure_ascii=False)}")

    # 汇总
    print("\n==== 汇总 ====")
    total = len(results)
    a_pass = sum(1 for r in results if r["route"] == "A_template_local" and r["valid_passed"])
    a_fail_c_pass = sum(1 for r in results if r["route"] == "C_fallback" and r["valid_passed"])
    exc_cnt = sum(1 for r in results if r["mode"] == "ERROR")
    in_expected = [r for r in results if r["in_template_expected"]]
    out_expected = [r for r in results if not r["in_template_expected"]]
    in_a_hit = sum(1 for r in in_expected if r["route"] == "A_template_local")
    out_a_hit = sum(1 for r in out_expected if r["route"] == "A_template_local")
    recall_ok = sum(1 for r in in_expected if (r["recall_sim"] or 0) >= 0.6)
    print(f"  用例: {total}  A本地改写(valid pass): {a_pass}  C回退(valid pass): {a_fail_c_pass}  异常: {exc_cnt}")
    print(f"  模板内方向(7个): 召回>=0.6: {recall_ok}/7  最终走A: {in_a_hit}/7")
    print(f"  模板外方向(7个): 最终走A: {out_a_hit}/7  (应为0-3，走C更合理)")
    print(f"  校验通过率: {sum(1 for r in results if r['valid_passed'])}/{total}")

    with open("_local_mode_14cases_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n详情已写入: _local_mode_14cases_report.json")


if __name__ == "__main__":
    main()
