# -*- coding: utf-8 -*-
"""C方案自动入库·整合分支验证：
策略1：同主题真实 C 方案二次调用，验证相似度>=0.8 时触发整合（合并文档 live_merge_）
策略2：若相似度未达阈值，人工构造完全一致的模板/query 强制验证整合分支代码路径
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_fallback_engine import fallback_engine
from vector.retriever import retriever
from config.settings import settings
from llm.router import llm
from services.mode_router import mode_router

created = []

def cleanup():
    try:
        got = retriever.collection.get(include=["metadatas"])
        ids = [i for i, m in zip(got["ids"], got["metadatas"])
               if (m or {}).get("source_channel") == "live_c_ingest_v1" or str(i).startswith("live_merge_")]
        if ids:
            retriever.collection.delete(ids=ids)
            print(f"[清理] 已删除测试数据 {len(ids)} 条")
        else:
            print("[清理] 无待清理数据")
    except Exception as e:
        print(f"[清理失败] {e}")

retriever.ensure_initial_data()
mode_router.init(llm=llm, retriever=retriever, local_engine=fallback_engine, auto_ingest=True)
print(f"库内模板数: {retriever.count()}, auto_ingest={mode_router._auto_ingest}, 阈值={mode_router.DUP_SIMILARITY_THRESHOLD}")

user_profile = {"age": 55, "gender": "男", "height_cm": 172, "weight_kg": 68, "bmi": 22.98,
                "crowd_type": "糖尿病患者", "allergies": ["花生"], "dietary_restrictions": ["低糖少油"]}
goal = "低糖高蛋白增肌，控制餐后血糖不升"
base_kwargs = dict(user_profile=user_profile, goal=goal, today_diet=[], today_diet_total={},
                   recent_exercise={"total_sessions": 4, "total_duration_min": 240,
                                    "total_calories_burned": 1200, "note": None})

try:
    # ========== 策略1：真实 C 方案同主题二次调用 ==========
    print("\n==== 策略1：真实 C 方案同主题二次调用 ====")
    r1 = mode_router.route("diet_plan", high_performance=True, **base_kwargs)
    n1 = retriever.count()
    print(f"  第一次真实C: route={r1.get('route')}, result非空={bool(r1.get('result'))}, 库={n1}")
    assert r1.get("result"), "第一次真实C方案应返回结果"
    time.sleep(1)
    r2 = mode_router.route("diet_plan", high_performance=True, **base_kwargs)
    n2 = retriever.count()
    print(f"  第二次真实C: route={r2.get('route')}, result非空={bool(r2.get('result'))}, 库={n2}")
    got = retriever.collection.get(include=["metadatas"])
    merges = [i for i, m in zip(got["ids"], got["metadatas"]) if str(i).startswith("live_merge_")]
    print(f"  live_merge_ 记录: {len(merges)} 条")
    if merges:
        created += merges
        print(f"  ✓ 真实C二次调用触发整合！merged_id={merges[0]}")
    else:
        print("  (信息) 二次调用未触发整合（相似度<0.8，属阈值策略预期）→ 进入策略2")

    # ========== 策略2：人工构造高相似度场景强制触发整合分支 ==========
    print("\n==== 策略2：强制相似度>=0.8 触发整合分支 ====")
    q = "糖尿病患者 低糖高蛋白增肌 一日膳食方案 三餐模板"
    doc = f"【标题】{q}\n【目标】低糖高蛋白增肌\n【一日膳食方案】\n早餐：无糖豆浆+鸡蛋\n午餐：杂粮饭+清蒸鲈鱼\n晚餐：荞麦面+鸡胸肉"
    # 先插入一条与 query 文本高度一致的模板
    retriever.collection.upsert(ids=[f"live_dup_src_{int(time.time())}"],
                                documents=[doc],
                                metadatas=[{"source_channel": "live_c_ingest_v1", "template_type": "ai_template",
                                            "func_type": "diet_plan", "target_crowd": "糖尿病患者",
                                            "bmi_id": "normal", "bmi_cn": "正常", "direction": goal[:40],
                                            "category": "crowd_specific", "topic": "糖尿病患者-BMI正常-低糖高蛋白增肌",
                                            "source": "整合测试源", "version": "1.0"}])
    dup_id = [i for i in retriever.collection.get()["ids"] if str(i).startswith("live_dup_src_")][-1]
    created.append(dup_id)

    # 用相同 query 再次入库 → 应命中刚插入模板（相似度高）→ 走整合
    before = retriever.count()
    mode_router._ingest_c_result("diet_plan", {"goal": goal, "total_calories": 1900, "daily_plan": {}, "tips": ["t1"]},
                                 trigger_route="C_fallback", **base_kwargs)
    after = retriever.count()
    got2 = retriever.collection.get(include=["metadatas"])
    merges2 = [i for i, m in zip(got2["ids"], got2["metadatas"]) if str(i).startswith("live_merge_")]
    print(f"  入库前后: {before} -> {after}, live_merge_={len(merges2)} 条")
    if merges2:
        created += merges2
        m0 = retriever.collection.get(ids=[merges2[0]], include=["documents", "metadatas"])
        d0 = m0["documents"][0]
        print(f"  ✓ 整合分支触发！合并文档前缀: {d0[:40]}")
        print(f"    内容含[整合版]: {'[整合版]' in d0}, 双份保留标记: {'云端整合失败' in d0}")
    else:
        print("  ✗ 策略2也未能触发整合（相似度仍未达0.8）")
finally:
    cleanup()
