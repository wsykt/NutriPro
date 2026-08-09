# -*- coding: utf-8 -*-
"""
AI 功能三方案对比测试
=====================
对比 4 个核心 AI 功能在三种 LLM 模式下的表现：
  方案A（纯本地）：Ollama qwen2.5-7B 全程生成
  方案B（混合）   ：Ollama 搭框架 → DeepSeek 补强结构+格式
  方案C（纯云端）：DeepSeek 全程生成

4 个测试功能：
  1. 健康咨询问答（/api/v1/chat，用户自然语言提问 → 文本回答）
  2. 一日饮食方案（/api/v1/diet/plan，人群+目标 → JSON三餐+份量+营养）
  3. 食材菜谱推荐（/api/v1/food/recommend，现有食材 → JSON三餐菜谱+热量）
  4. 个性化运动方案（/api/v1/exercise/advice，身体指标+目标 → JSON周计划）

对比维度：
  - 总耗时(s)
  - 云端token消耗（输入/输出/总计）
  - 本地调用次数
  - 输出字数 / JSON字段完整性
  - 结构化JSON字段校验（针对2/3/4项）

用法：
    python compare_ai_3plans.py                  # 跑全部功能+三方案
    python compare_ai_3plans.py --feature chat   # 只测健康咨询
    python compare_ai_3plans.py --plan A         # 只跑方案A
    python compare_ai_3plans.py --report         # 只生成对比报告
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

AI_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_DIR)

from config.settings import settings
from services.retrieval_service import build_kb_context

OUTPUT_DIR = os.path.join(AI_DIR, "test_output", "ai_3plans")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 测试用例（与生产输入保持一致）
# ============================================================
TEST_CASES = {
    # 1. 健康咨询问答（文本输出）
    "chat": {
        "name": "健康咨询问答",
        "description": "血脂偏高+高血压人群的日常饮食建议",
        "input": {
            "message": "我血脂偏高，还有高血压，日常饮食应该怎么调整？能不能给我一个一周的饮食方向建议？",
            "health_snapshot": {
                "profile": {
                    "username": "测试用户", "gender": "男", "age": 52,
                    "height_cm": 172, "weight_kg": 82, "bmi": 27.7,
                    "crowdType": "老年人",
                }
            },
            "target_crowd": "老年人",
            "kb_query": "高血压 高血脂 饮食调整 老年人",
        },
        "output_type": "text",
        "check_fields": [],
        "quality_checks": [
            ("提到总脂肪/饱和脂肪限制", lambda x: ("脂肪" in x and "不饱和" in x) or "总脂肪" in x),
            ("提到低钠/限盐", lambda x: "盐" in x or "钠" in x or "DASH" in x),
            ("提到蔬菜水果摄入", lambda x: "蔬菜" in x or "蔬果" in x or "水果" in x),
            ("提到酒精/体重/运动", lambda x: any(k in x for k in ["运动", "体重", "酒精", "戒烟"])),
            ("给出明确可执行建议（≥4条）", lambda x: sum(1 for c in '①②③④⑤⑥123456' if c in x) >= 4 or x.count('\n') >= 4),
        ],
    },
    # 2. 一日饮食方案（JSON输出）
    "diet": {
        "name": "一日饮食方案",
        "description": "孕妇孕中期增重控糖饮食",
        "input": {
            "user_profile": {
                "age": 29, "gender": "女", "weight": 65, "height": 165,
                "crowd_type": "孕妇",
                "allergies": ["海鲜"],
                "dietary_restrictions": ["不吃羊肉"],
                "trimester": "孕中期",
            },
            "goal": "孕期合理增重+控糖",
        },
        "output_type": "json",
        "check_fields": ["goal", "total_calories", "daily_plan", "nutrition_breakdown", "tips"],
        "plan_meals": ["早餐", "午餐", "晚餐"],
        "nutrition_fields": ["protein", "carbohydrate", "fat"],
        "quality_checks": [
            ("总热量合理 (2000-2800)", lambda d: 2000 <= int(d.get("total_calories", 0)) <= 2800),
            ("三餐齐全", lambda d: all(m in (d.get("daily_plan") or {}) for m in ["早餐", "午餐", "晚餐"])),
            ("每顿≥2道菜", lambda d: all(len((d.get("daily_plan") or {}).get(m, [])) >= 2 for m in ["早餐", "午餐", "晚餐"])),
            ("每道菜含food和portion", lambda d: all(
                all("food" in item and "portion" in item
                    for item in (d.get("daily_plan") or {}).get(m, []))
                for m in ["早餐", "午餐", "晚餐"])),
            ("营养三要素齐全", lambda d: all(f in (d.get("nutrition_breakdown") or {}) for f in ["protein", "carbohydrate", "fat"])),
            ("tips≥2条", lambda d: len(d.get("tips", [])) >= 2),
        ],
    },
    # 3. 食材菜谱推荐（JSON输出）
    "food_recommend": {
        "name": "食材菜谱推荐",
        "description": "用鸡胸/西兰花/糙米给健身者做三餐",
        "input": {
            "ingredients": ["鸡胸肉", "西兰花", "糙米", "鸡蛋", "牛奶", "番茄"],
            "crowd_type": "健身人群",
            "goal": "增肌减脂",
        },
        "output_type": "json",
        "check_fields": ["meal_plan", "total_calories", "total_protein", "tips"],
        "quality_checks": [
            ("3餐齐全", lambda d: len(d.get("meal_plan", [])) >= 3),
            ("每顿用了至少一个给定食材", lambda d: all(
                any(ing in (str(meal.get("ingredients", [])) + meal.get("name", "") + meal.get("cook_method", ""))
                    for ing in ["鸡胸肉", "西兰花", "糙米", "鸡蛋", "牛奶", "番茄"])
                for meal in d.get("meal_plan", []))),
            ("每顿含热量估算", lambda d: all(meal.get("calories_estimate", 0) > 0 for meal in d.get("meal_plan", []))),
            ("每顿含做法", lambda d: all(bool(meal.get("cook_method", "")) for meal in d.get("meal_plan", []))),
            ("总热量合理(1200-2500)", lambda d: 1200 <= int(d.get("total_calories", 0)) <= 2500),
            ("总蛋白合理(60-200g)", lambda d: 60 <= int(d.get("total_protein", 0)) <= 200),
            ("tips≥2条", lambda d: len(d.get("tips", [])) >= 2),
        ],
    },
    # 4. 个性化运动方案（JSON输出）
    "exercise": {
        "name": "个性化运动方案",
        "description": "高血压中老年减脂运动",
        "input": {
            "user_profile": {
                "age": 58, "gender": "男", "weight": 85, "height": 170,
                "bmi": 29.4, "crowd_type": "老年人",
            },
            "goal": "减脂+控血压",
            "preferences": "喜欢散步、游泳，不喜欢剧烈运动",
            "chronic_diseases": ["高血压"],
        },
        "output_type": "json",
        "check_fields": ["goal", "weekly_schedule", "weekly_total_minutes", "precautions"],
        "quality_checks": [
            ("周计划≥4天", lambda d: len(d.get("weekly_schedule", [])) >= 4),
            ("每天含day/exercise_type/duration/intensity", lambda d: all(
                all(k in day for k in ["day", "exercise_type", "duration", "intensity"])
                for day in d.get("weekly_schedule", []))),
            ("每周总时长≥150分钟", lambda d: int(d.get("weekly_total_minutes", 0)) >= 150),
            ("有热身/拉伸建议", lambda d: bool(d.get("warm_up", "")) and bool(d.get("cool_down", ""))),
            ("注意事项≥3条", lambda d: len(d.get("precautions", [])) >= 3),
            ("提到高血压禁忌/安全提示", lambda d: any(
                k in str(d.get("precautions", [])) or k in str(d.get("weekly_schedule", ""))
                for k in ["血压", "憋气", "高强度", "头晕", "禁忌"])),
        ],
    },
}


# ============================================================
# Token/Timing 追踪器
# ============================================================
class PlanTokenTracker:
    def __init__(self):
        self.local_calls = 0
        self.cloud_calls = 0
        self.local_tokens_est = 0      # 字符数//3 估算
        self.cloud_prompt_tokens = 0
        self.cloud_completion_tokens = 0
        self.cloud_total_tokens = 0
        self.timings = []  # [(stage, elapsed), ...]

    def record_local(self, content):
        self.local_calls += 1
        self.local_tokens_est += len(content) // 3

    def record_cloud(self, usage):
        self.cloud_calls += 1
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        self.cloud_prompt_tokens += pt
        self.cloud_completion_tokens += ct
        self.cloud_total_tokens += pt + ct

    def add_timing(self, stage, elapsed):
        self.timings.append((stage, round(elapsed, 2)))

    @property
    def total_elapsed(self):
        return sum(t for _, t in self.timings)

    def summary(self):
        return {
            "local_calls": self.local_calls,
            "cloud_calls": self.cloud_calls,
            "local_tokens_est": self.local_tokens_est,
            "cloud_prompt_tokens": self.cloud_prompt_tokens,
            "cloud_completion_tokens": self.cloud_completion_tokens,
            "cloud_total_tokens": self.cloud_total_tokens,
            "timings": [(s, round(t, 2)) for s, t in self.timings],
            "total_elapsed": round(self.total_elapsed, 2),
        }


# ============================================================
# 通用 LLM 调用包装
# ============================================================
def call_llm_local(system: str, user_prompt: str, tracker: PlanTokenTracker,
                   stage: str, temp: float = 0.5, max_predict: int = 2500) -> str:
    import requests
    t0 = time.time()
    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "num_predict": max_predict,
                },
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        elapsed = time.time() - t0
        if resp.status_code != 200:
            print(f"    ✗ [{stage}] Ollama HTTP {resp.status_code}: {resp.text[:200]}")
            tracker.add_timing(stage, elapsed)
            return ""
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        tracker.record_local(content)
        tracker.add_timing(stage, elapsed)
        print(f"    ✓ [{stage}] 本地 {elapsed:.1f}s | {len(content)}字")
        return content
    except Exception as e:
        tracker.add_timing(stage, time.time() - t0)
        print(f"    ✗ [{stage}] Ollama异常: {e}")
        return ""


def call_llm_cloud(system: str, user_prompt: str, tracker: PlanTokenTracker,
                   stage: str, temp: float = 0.7, max_tokens: int = 3000) -> str:
    import requests
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }
    t0 = time.time()
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                headers=headers, json=payload, timeout=180,
            )
            elapsed = time.time() - t0
            if resp.status_code != 200:
                print(f"    ✗ [{stage}] 云端 HTTP {resp.status_code}")
                if attempt < 2:
                    time.sleep(2)
                    continue
                tracker.add_timing(stage, elapsed)
                return ""
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tracker.record_cloud(usage)
            tracker.add_timing(stage, elapsed)
            print(f"    ✓ [{stage}] 云端 {elapsed:.1f}s | {len(content)}字 | "
                  f"tokens: in={usage.get('prompt_tokens',0)} out={usage.get('completion_tokens',0)}")
            return content
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                tracker.add_timing(stage, time.time() - t0)
                print(f"    ✗ [{stage}] 云端异常: {e}")
                return ""
    return ""


def safe_parse_json(text: str) -> dict:
    """尽量宽容地从LLM输出中解析JSON"""
    if not text:
        return {}
    import re
    # 去掉```json ```包裹
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text, flags=re.IGNORECASE)
    # 提取最外层{}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        text = match.group(0)
    try:
        return json.loads(text)
    except Exception:
        pass
    # 宽容：修复尾随逗号
    try:
        text2 = re.sub(r",\s*([\]}])", r"\1", text)
        return json.loads(text2)
    except Exception:
        return {}


# ============================================================
# 通用知识库检索（三方案共用，确保输入公平）
# ============================================================
def get_kb_context(feature_key: str) -> str:
    case = TEST_CASES[feature_key]
    query = case["input"].get("kb_query") or case["input"].get("goal") or case["description"]
    crowd = case["input"].get("target_crowd") or \
            (case["input"].get("user_profile") or {}).get("crowd_type") or \
            (case["input"].get("user_profile") or {}).get("crowdType") or \
            case["input"].get("crowd_type") or ""
    search_query = f"{crowd} {query}" if crowd else query
    return build_kb_context(search_query, top_k=3)


# ============================================================
# 构造各功能的 Prompt（复用项目自带提示词）
# ============================================================
def build_prompts(feature_key: str, kb_context: str = ""):
    """返回 (system_prompt, base_user_prompt) — 复用项目自带 Agent Prompt"""
    case = TEST_CASES[feature_key]
    inp = case["input"]

    if feature_key == "chat":
        # 复用 orchestrator._build_messages
        health_snapshot = inp.get("health_snapshot", {})
        prof = health_snapshot.get("profile", {})
        profile_ctx = (f"【用户健康档案】\n"
                       f"姓名：{prof.get('username','')}\n"
                       f"性别：{prof.get('gender','')}\n"
                       f"年龄：{prof.get('age','')}\n"
                       f"身高：{prof.get('height_cm','')}cm\n"
                       f"体重：{prof.get('weight_kg','')}kg\n"
                       f"BMI：{prof.get('bmi','')}\n"
                       f"人群标签：{prof.get('crowdType','')}")
        system_prompt = "你是一个专业的健康咨询助手，用中文给出实用的健康建议。\n\n"
        if profile_ctx:
            system_prompt += f"{profile_ctx}\n\n"
        if kb_context:
            system_prompt += f"{kb_context}\n\n"
        system_prompt += "输出要求：\n1. 基于上述数据给出具体建议\n2. 不提供疾病诊断，仅膳食科普\n3. 用中文回答，条理清晰"
        user_prompt = inp["message"]
        return system_prompt, user_prompt

    if feature_key == "diet":
        from agent.diet_plan import DIET_PLAN_PROMPT
        user_profile = inp["user_profile"]
        goal = inp["goal"]
        allergies = user_profile.get("allergies", [])
        restrictions = user_profile.get("dietary_restrictions", [])
        system_prompt = "你是一个专业膳食方案制定专家。只输出JSON。"
        user_prompt = DIET_PLAN_PROMPT + "\n\n"
        user_prompt += f"用户档案：{json.dumps(user_profile, ensure_ascii=False)}\n"
        user_prompt += f"健康目标：{goal}\n"
        user_prompt += f"过敏食材：{allergies}\n"
        user_prompt += f"饮食禁忌：{restrictions}\n"
        if kb_context:
            user_prompt += kb_context
        return system_prompt, user_prompt

    if feature_key == "food_recommend":
        from agent.food_recommend import FOOD_RECOMMEND_PROMPT
        ingredients = inp["ingredients"]
        crowd_type = inp["crowd_type"]
        goal = inp["goal"]
        system_prompt = "你是一个专业营养膳食推荐专家。只输出JSON。"
        ingredients_str = "、".join(ingredients) if isinstance(ingredients, list) else str(ingredients)
        user_prompt = FOOD_RECOMMEND_PROMPT + f"\n\n现有食材：{ingredients_str}\n人群标签：{crowd_type}\n目标：{goal}"
        if kb_context:
            user_prompt += f"\n{kb_context}"
        return system_prompt, user_prompt

    if feature_key == "exercise":
        from agent.exercise_advice import EXERCISE_ADVICE_PROMPT
        user_profile = inp["user_profile"]
        goal = inp["goal"]
        preferences = inp.get("preferences", "")
        chronic_diseases = inp.get("chronic_diseases", [])
        bmi = user_profile.get("bmi", 0)
        age = user_profile.get("age", 30)
        gender = user_profile.get("gender", "男")
        crowd = user_profile.get("crowd_type", "普通人")
        profile_str = f"年龄{age}岁，{gender}，BMI{bmi:.1f}，人群标签{crowd}"
        if chronic_diseases:
            profile_str += f"，慢病：{'、'.join(chronic_diseases)}"
        system_prompt = "你是专业运动健康指导专家。只输出JSON。"
        user_prompt = EXERCISE_ADVICE_PROMPT + f"\n\n用户档案：{profile_str}\n运动目标：{goal}\n运动偏好：{preferences}"
        if kb_context:
            user_prompt += f"\n{kb_context}"
        return system_prompt, user_prompt

    raise ValueError(f"未知功能: {feature_key}")


# ============================================================
# 三方案实现
# ============================================================
def run_plan_a(feature_key: str, kb_context: str) -> dict:
    """方案A：纯本地 Ollama 一次生成"""
    tracker = PlanTokenTracker()
    case = TEST_CASES[feature_key]
    sys_p, user_p = build_prompts(feature_key, kb_context)
    max_predict = 3500 if case["output_type"] == "json" else 3000

    print(f"\n[方案A 纯本地] {case['name']}")
    raw = call_llm_local(sys_p, user_p, tracker, f"A-{feature_key}-Stage1",
                         temp=0.4, max_predict=max_predict)

    if case["output_type"] == "json":
        parsed = safe_parse_json(raw)
        return {"plan": "A", "success": bool(parsed) or bool(raw),
                "raw_output": raw, "parsed": parsed, "tracker": tracker.summary()}
    return {"plan": "A", "success": bool(raw),
            "raw_output": raw, "tracker": tracker.summary()}


def run_plan_b(feature_key: str, kb_context: str) -> dict:
    """方案B：本地 Ollama 搭框架（宽松）→ 云端 DeepSeek 补结构+格式校验"""
    tracker = PlanTokenTracker()
    case = TEST_CASES[feature_key]
    sys_p, user_p = build_prompts(feature_key, kb_context)

    print(f"\n[方案B 混合] {case['name']}")
    # Stage1：本地搭框架（更宽容，允许字段不全）
    if case["output_type"] == "json":
        local_sys = (sys_p + "\n\n重要：尽量输出完整结构；若个别字段不确定可暂留默认值，后续会被云端补强。")
        local_max = 2500
    else:
        local_sys = sys_p + "\n\n（先输出框架性要点，后续会被完整化补强）"
        local_max = 2000

    framework = call_llm_local(local_sys, user_p, tracker, f"B-{feature_key}-Stage1",
                               temp=0.3, max_predict=local_max) or ""

    # Stage2：云端补强（对于text型润色扩展；对于json型修复缺失字段和格式）
    if case["output_type"] == "json":
        cloud_sys = (
            f"你是专业格式校对专家。收到一份基于以下指令生成的{case['name']}初稿（JSON），"
            "初稿可能字段不全、格式不严谨。请严格按照指令补全所有缺失字段、规范JSON格式，"
            "并把食材份量、数值估算更细化更合理。只输出最终JSON，禁止额外文字。\n\n"
            f"原始指令：\n{sys_p}\n{user_p}"
        )
        cloud_user = f"【初稿】\n{framework}"
        raw = call_llm_cloud(cloud_sys, cloud_user, tracker, f"B-{feature_key}-Stage2",
                             temp=0.5, max_tokens=3000)
        parsed = safe_parse_json(raw)
        return {"plan": "B", "success": bool(parsed) or bool(framework),
                "raw_output": raw or framework, "parsed": parsed,
                "framework": framework, "tracker": tracker.summary()}
    else:
        cloud_sys = (
            "你是健康科普润色专家。收到一份用户健康咨询的框架性回答初稿，请在此基础上扩展润色，"
            "要求：1) 补充更具体的执行建议（≥4条分点）；2) 语气专业友好；3) 保持中文输出；"
            "4) 不提供疾病诊断。"
        )
        cloud_user = (
            f"【用户问题】\n{TEST_CASES['chat']['input']['message']}\n\n"
            f"【上下文】\n{sys_p}\n\n"
            f"【初稿（基于知识库生成，可修改润色）】\n{framework}"
        )
        final = call_llm_cloud(cloud_sys, cloud_user, tracker, f"B-{feature_key}-Stage2",
                               temp=0.7, max_tokens=3000) or framework
        return {"plan": "B", "success": bool(final),
                "raw_output": final, "framework": framework,
                "tracker": tracker.summary()}


def run_plan_c(feature_key: str, kb_context: str) -> dict:
    """方案C：纯云端 DeepSeek 一次性生成"""
    tracker = PlanTokenTracker()
    case = TEST_CASES[feature_key]
    sys_p, user_p = build_prompts(feature_key, kb_context)
    max_tokens = 4000 if case["output_type"] == "json" else 3500

    print(f"\n[方案C 纯云端] {case['name']}")
    raw = call_llm_cloud(sys_p, user_p, tracker, f"C-{feature_key}-Stage1",
                         temp=0.6, max_tokens=max_tokens)

    if case["output_type"] == "json":
        parsed = safe_parse_json(raw)
        return {"plan": "C", "success": bool(parsed) or bool(raw),
                "raw_output": raw, "parsed": parsed, "tracker": tracker.summary()}
    return {"plan": "C", "success": bool(raw),
            "raw_output": raw, "tracker": tracker.summary()}


# ============================================================
# 质量评估（所有方案共用）
# ============================================================
def evaluate_result(feature_key: str, result: dict) -> dict:
    case = TEST_CASES[feature_key]
    output_type = case["output_type"]

    if output_type == "json":
        parsed = result.get("parsed") or {}
        total_chars = len(result.get("raw_output", ""))
        json_chars = len(json.dumps(parsed, ensure_ascii=False)) if parsed else 0

        checks_passed = 0
        checks_detail = []
        for check_name, check_fn in case.get("quality_checks", []):
            try:
                ok = bool(check_fn(parsed))
            except Exception:
                ok = False
            checks_detail.append({"name": check_name, "passed": ok})
            if ok:
                checks_passed += 1

        # 必需字段完整性
        required_fields = case.get("check_fields", [])
        fields_present = [f for f in required_fields if f in parsed and parsed[f] is not None]
        field_integrity = f"{len(fields_present)}/{len(required_fields)}" if required_fields else "—"

        return {
            "valid": bool(parsed),
            "parse_ok": bool(parsed),
            "total_chars": total_chars,
            "json_chars": json_chars,
            "field_integrity": field_integrity,
            "missing_fields": [f for f in required_fields if f not in parsed or parsed[f] is None],
            "quality_score": round(checks_passed / max(len(case["quality_checks"]), 1) * 100, 1),
            "checks_passed": checks_passed,
            "checks_total": len(case["quality_checks"]),
            "checks_detail": checks_detail,
        }
    else:
        raw = result.get("raw_output", "") or ""
        total_chars = len(raw)
        checks_passed = 0
        checks_detail = []
        for check_name, check_fn in case.get("quality_checks", []):
            try:
                ok = bool(check_fn(raw))
            except Exception:
                ok = False
            checks_detail.append({"name": check_name, "passed": ok})
            if ok:
                checks_passed += 1
        return {
            "valid": total_chars > 100,
            "total_chars": total_chars,
            "quality_score": round(checks_passed / max(len(case["quality_checks"]), 1) * 100, 1),
            "checks_passed": checks_passed,
            "checks_total": len(case["quality_checks"]),
            "checks_detail": checks_detail,
        }


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="AI功能三方案对比测试")
    parser.add_argument("--feature", choices=list(TEST_CASES.keys()),
                        help="只测指定功能（chat/diet/food_recommend/exercise）")
    parser.add_argument("--plan", choices=["A", "B", "C"], help="只跑指定方案")
    parser.add_argument("--report", action="store_true", help="生成对比报告（需要已有结果）")
    args = parser.parse_args()

    if args.report:
        generate_report()
        return

    features = [args.feature] if args.feature else list(TEST_CASES.keys())
    plans = [args.plan] if args.plan else ["A", "B", "C"]

    for fk in features:
        fdir = os.path.join(OUTPUT_DIR, fk)
        os.makedirs(fdir, exist_ok=True)
        kb = get_kb_context(fk)
        print(f"\n{'#'*70}")
        print(f"# 功能: {TEST_CASES[fk]['name']} — {TEST_CASES[fk]['description']}")
        print(f"# 知识库上下文长度: {len(kb)}字")
        print(f"{'#'*70}")

        all_results = {}
        for plan in plans:
            t0 = time.time()
            if plan == "A":
                result = run_plan_a(fk, kb)
            elif plan == "B":
                result = run_plan_b(fk, kb)
            else:
                result = run_plan_c(fk, kb)
            total_wall = time.time() - t0
            result["total_wall_time"] = round(total_wall, 2)
            result["quality"] = evaluate_result(fk, result)
            all_results[plan] = result

            # 保存单方案单功能
            path = os.path.join(fdir, f"result_plan_{plan}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n  ➜ 已保存: {path}")
            t = result["tracker"]
            q = result["quality"]
            print(f"    总耗时: {result['total_wall_time']}s | "
                  f"云端token: {t['cloud_total_tokens']} | "
                  f"本地调用: {t['local_calls']}次 | "
                  f"质量分: {q.get('quality_score', 'N/A')}/100 | "
                  f"字数: {q.get('total_chars', 0)}")

    # 如果所有功能都跑完，生成总报告
    if not args.feature and not args.plan:
        generate_report()


def generate_report():
    print(f"\n{'='*70}")
    print("生成 AI 功能三方案对比报告")
    print(f"{'='*70}")

    features_data = {}
    for fk, fcase in TEST_CASES.items():
        fdir = os.path.join(OUTPUT_DIR, fk)
        if not os.path.isdir(fdir):
            continue
        fdata = {}
        for plan in ["A", "B", "C"]:
            path = os.path.join(fdir, f"result_plan_{plan}.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    fdata[plan] = json.load(f)
        if fdata:
            features_data[fk] = {"case": fcase, "results": fdata}

    if not features_data:
        print("  ⚠ 没有可用结果，请先运行测试")
        return

    report_path = os.path.join(OUTPUT_DIR, "comparison_report.md")
    L = []
    L.append("# AI 功能三方案对比测试报告\n")
    L.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    L.append("---\n")

    # 一、方案说明
    L.append("## 一、方案说明\n")
    L.append("| 方案 | 执行方式 | 适用场景 |")
    L.append("|------|---------|---------|")
    L.append("| A 纯本地 | Ollama qwen2.5-7B 一次性生成 | 离线/隐私/大批量初稿 |")
    L.append("| B 混合 | Ollama 搭框架 → DeepSeek 补格式+数值+润色 | 平衡质量与成本 |")
    L.append("| C 纯云端 | DeepSeek 一次性生成 | 最高质量/最高token效率 |\n")

    L.append("## 二、测试功能清单\n")
    L.append("| 编号 | 功能 | 输入样例 | 输出 |")
    L.append("|------|------|---------|------|")
    for i, (fk, fcase) in enumerate(TEST_CASES.items(), 1):
        L.append(f"| {i} | {fcase['name']} | {fcase['description']} | {fcase['output_type']} |")
    L.append("")

    # 三、核心指标总表
    L.append("## 三、核心指标总表\n")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        L.append(f"### {fname}\n")
        L.append("| 指标 | A 纯本地 | B 混合 | C 纯云端 |")
        L.append("|------|---------|--------|---------|")
        plans = data["results"]
        for metric_key, label in [
            ("total_wall_time", "总耗时(s)"),
            ("cloud_total_tokens", "云端总token"),
            ("cloud_prompt_tokens", "云端输入token"),
            ("cloud_completion_tokens", "云端输出token"),
            ("cloud_calls", "云端调用次数"),
            ("local_calls", "本地调用次数"),
            ("local_tokens_est", "本地token(估算)"),
        ]:
            row = f"| {label} |"
            for plan in ["A", "B", "C"]:
                if plan not in plans:
                    row += " — |"
                    continue
                t = plans[plan]["tracker"]
                val = t.get(metric_key, 0) if metric_key.startswith("local") or metric_key.startswith("cloud") else \
                      plans[plan].get(metric_key, 0)
                row += f" {val} |"
            L.append(row)
        # 质量指标
        row = "| 输出字数 |"
        for plan in ["A", "B", "C"]:
            q = plans[plan]["quality"] if plan in plans else {}
            row += f" {q.get('total_chars', '—')} |"
        L.append(row)
        row = "| 质量分 |"
        for plan in ["A", "B", "C"]:
            q = plans[plan]["quality"] if plan in plans else {}
            row += f" {q.get('quality_score', '—')} |"
        L.append(row)
        L.append("")

    # 四、逐功能质量检查通过率
    L.append("## 四、逐功能质量检查通过率\n")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        L.append(f"### {fname}\n")
        # 表头：检查项 × 三方案
        qchecks = data["case"].get("quality_checks", [])
        headers = ["检查项"] + [f"A通过" for _ in range(1)] + [f"B通过" for _ in range(1)] + [f"C通过"]
        L.append("| " + " | ".join(headers) + " |")
        L.append("|" + "|".join(["---"]*(len(qchecks) and len(TEST_CASES)*1 or 4)) + "|")
        # 其实做一个更清晰的表
    # 重做第四节
    L = L[:L.index("## 四、逐功能质量检查通过率\n")]
    L.append("## 四、逐功能质量检查通过率\n")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        qchecks = data["case"].get("quality_checks", [])
        plans = data["results"]
        L.append(f"### {fname}\n")
        L.append("| 质量检查项 | A 纯本地 | B 混合 | C 纯云端 |")
        L.append("|-----------|---------|--------|---------|")
        for cname, _ in qchecks:
            row = f"| {cname} |"
            for plan in ["A", "B", "C"]:
                if plan not in plans:
                    row += " — |"
                    continue
                det = plans[plan]["quality"].get("checks_detail", [])
                match = [d for d in det if d["name"] == cname]
                passed = "✓" if match and match[0]["passed"] else "✗"
                row += f" {passed} |"
            L.append(row)
        row = "| **总分** |"
        for plan in ["A", "B", "C"]:
            if plan in plans:
                q = plans[plan]["quality"]
                row += f" **{q.get('checks_passed', 0)}/{q.get('checks_total', 0)} ({q.get('quality_score', 0)}分)** |"
            else:
                row += " — |"
        L.append(row)
        L.append("")

    # 五、云端token节省分析
    L.append("## 五、云端token消耗对比\n")
    L.append("| 功能 | A 纯本地 | B 混合 | C 纯云端 | A比C节省 | B比C节省 |")
    L.append("|------|---------|--------|---------|---------|---------|")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        plans = data["results"]
        c_tokens = plans["C"]["tracker"]["cloud_total_tokens"] if "C" in plans else 0
        b_tokens = plans["B"]["tracker"]["cloud_total_tokens"] if "B" in plans else 0
        a_tokens = plans["A"]["tracker"]["cloud_total_tokens"] if "A" in plans else 0
        save_a = f"{(c_tokens-a_tokens)/c_tokens*100:.1f}%" if c_tokens else "—"
        save_b = f"{(c_tokens-b_tokens)/c_tokens*100:.1f}%" if c_tokens and c_tokens >= b_tokens else f"+{(b_tokens-c_tokens)/c_tokens*100:.1f}%" if c_tokens else "—"
        L.append(f"| {fname} | {a_tokens} | {b_tokens} | {c_tokens} | {save_a} | {save_b} |")
    L.append("")

    # 六、综合结论
    L.append("## 六、综合结论\n")
    L.append("### 6.1 成本视角\n")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        plans = data["results"]
        a = plans.get("A", {}).get("tracker", {}).get("cloud_total_tokens", 0)
        b = plans.get("B", {}).get("tracker", {}).get("cloud_total_tokens", 0)
        c = plans.get("C", {}).get("tracker", {}).get("cloud_total_tokens", 0)
        L.append(f"- **{fname}**：A方案云端token={a}（零成本），B={b}，C={c}")
    L.append("")
    L.append("### 6.2 时间视角\n")
    for fk, data in features_data.items():
        fname = data["case"]["name"]
        plans = data["results"]
        times = []
        for plan in ["A", "B", "C"]:
            if plan in plans:
                times.append(f"方案{plan}: {plans[plan]['total_wall_time']}s")
        L.append(f"- **{fname}**：{' / '.join(times)}")
    L.append("")
    L.append("### 6.3 推荐场景\n")
    L.append("| 场景 | 推荐方案 | 原因 |")
    L.append("|------|---------|------|")
    L.append("| 离线环境 / 隐私敏感 | 方案A | 全程本地，零云端传输 |")
    L.append("| 大批量初稿生成 | 方案A | 零token成本，后续可选择性升级 |")
    L.append("| 结构敏感任务(JSON输出) | 方案B或C | 云端处理字段完整性更稳定 |")
    L.append("| 最高质量 + 最高效率 | 方案C | 一次性出最优结果，总体token效率最高 |")
    L.append("| 团队审核工作流 | 方案B | 本地框架可预览，审核后再调用云端补强 |\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\n报告已生成: {report_path}")
    print("=" * 70)
    # 打印前60行
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
