"""A/C 方案模式路由器 v1.0

负责四种 AI 咨询功能的双模式调度：

= 模式说明 =
1. 【正常模式】(high_performance=false, 默认)
   流程：向量知识库模板召回 → 本地 Ollama 模型改写(A方案) → 校验失败 → 回退云端 DeepSeek(C方案)
   优势：省云端 Token，高质量模板驱动，速度稍慢

2. 【高性能模式】(high_performance=true)
   流程：直接调用云端 DeepSeek 一次性生成(C方案)，跳过本地校验
   优势：响应速度最快，演示体验流畅；劣势：消耗更多云端 Token

= 四种接入功能 =
① 健康咨询问答 (chat/qa)      - 文字回答
② 一日饮食方案 (diet_plan)     - JSON 结构化
③ 食材菜谱推荐 (food_recommend)- JSON 结构化
④ 个性化运动方案 (exercise)    - JSON 结构化

= 云端校验规则（仅正常模式 C 方案回退后执行）=
- 饮食方案：总热量区间、菜品数量(≥3餐)、营养素字段齐全、提示项
- 菜谱推荐：必填字段(meal_plan/total_calories)、总蛋白、总热量
- 运动方案：周天数(≥3)、总运动时长、热身说明、慢病安全提示
- 健康问答：要点齐全(限盐/蔬果/运动/体重/酒精，高血压等慢病场景)
"""

import time
import json
import re
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from config.settings import settings
from local_fallback_engine import canonical_crowd, crowd_kb_name, crowd_display_name
from services.async_task_service import async_task_service

logger = logging.getLogger(__name__)


# ============================================================
# 各功能的本地改写 Prompt 模板 (A方案用)
# ============================================================

REWRITE_PROMPTS = {
    # ① 健康问答
    "qa": """你是健康科普改写助手。请基于提供的知识库标准回答模板，结合用户实际问题进行个性化改写。

【要求】
1. 只改写模板内容，不编造额外信息
2. 回答条理清晰，分点说明
3. 保留模板中的关键数据和建议
4. 用自然流畅的中文回答，不要机械照搬模板
5. 末尾添加："温馨提示：本内容仅供膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。"

【用户问题】：{question}
【用户档案】：{user_profile}
【用户健康档案（系统根据已设置的身高/体重/年龄/性别/今日饮食/近期运动自动推导，无需用户重复说明）】：
{user_derived_context}
【知识库模板参考】：
{template_content}

请直接输出改写后的完整回答：""",

    # ② 一日饮食方案
    "diet_plan": """你是膳食方案改写专家。请基于标准饮食模板，根据用户档案和健康目标调整参数。

【输出严格JSON格式，不要任何额外文字】：
{{
  "goal": "用户目标",
  "total_calories": 合理的整数热量值,
  "daily_plan": {{
    "早餐": [{{"food": "食材名", "portion": "份量"}}, ...],
    "午餐": [{{"food": "食材名", "portion": "份量"}}, ...],
    "晚餐": [{{"food": "食材名", "portion": "份量"}}, ...],
    "加餐": [{{"food": "食材名", "portion": "份量"}}, ...]
  }},
  "nutrition_breakdown": {{"protein": 整数, "carbohydrate": 整数, "fat": 整数}},
  "tips": ["建议1", "建议2"],
  "avoided_foods": [],
  "replaced_foods": []
}}

【用户档案】：{user_profile}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【健康目标】：{goal}
【过敏/忌口】：{restrictions}
【标准模板参考】：
{template_content}

请直接输出调整后的JSON：""",

    # ③ 食材菜谱推荐
    "food_recommend": """你是菜谱推荐改写专家。请基于标准菜谱模板，结合用户指定食材调整方案。

【输出严格JSON格式，不要任何额外文字】：
{{
  "total_meals": 3,
  "meal_plan": [
    {{
      "meal_type": "早餐/午餐/晚餐",
      "name": "菜名",
      "ingredients": [{{"name":"食材","amount":"用量"}}],
      "cook_method": "简易做法1-2句话",
      "calories_estimate": 整数,
      "protein_estimate": 整数,
      "tags": ["标签1","标签2"]
    }}
  ],
  "total_calories": 整数,
  "total_protein": 整数,
  "tips": ["建议1","建议2"],
  "missing_ingredients": ["建议补充的食材"]
}}

【现有食材】：{ingredients}
【人群标签】：{crowd_type}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【目标】：{goal}
【标准模板参考】：
{template_content}

请直接输出调整后的JSON（必须全部使用用户提供的食材）：""",

    # ④ 个性化运动方案
    "exercise": """你是运动方案改写专家。请基于标准运动模板，结合用户身体状况调整。

【输出严格JSON格式，不要任何额外文字】：
{{
  "goal": "用户目标",
  "weekly_schedule": [
    {{"day": "周一", "exercise_type": "运动类型", "duration": "时长分钟", "intensity": "低/中/高", "description": "详细说明", "calories_burn_estimate": 整数}}
  ],
  "weekly_total_minutes": 整数,
  "weekly_total_calories": 整数,
  "warm_up": "热身建议",
  "cool_down": "拉伸建议",
  "precautions": ["注意事项1", "注意事项2"],
  "progression_plan": "进阶计划说明"
}}

【用户档案】：{user_profile}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【运动目标】：{goal}
【运动偏好】：{preferences}
【慢病情况】：{chronic_diseases}
【标准模板参考】：
{template_content}

请直接输出调整后的JSON（慢病患者必须标注安全提示和禁忌动作）：""",
}


# ============================================================
# C 方案云端生成 Prompt 模板 (正常模式回退 + 高性能模式直接用)
# ============================================================

CLOUD_PROMPTS = {
    "qa": """你是专业健康咨询助手。请基于用户问题给出科学、实用、条理清晰的回答。

【用户档案】：{user_profile}
【用户健康档案（系统根据已设置的身高/体重/年龄/性别/今日饮食/近期运动自动推导，无需用户重复说明）】：
{user_derived_context}
【用户问题】：{question}

【回答要求】：
1. 分点说明，逻辑清晰
2. 结合用户实际情况给出个性化建议
3. 包含具体的可执行建议，避免空泛
4. 不提供医疗诊断，仅做膳食科普和健康建议

请直接输出完整回答：""",

    "diet_plan": """你是个性化膳食方案专家。请为用户生成科学合理的一日三餐方案。

【输出严格JSON格式，不要任何额外文字】。格式要求：
{{
  "goal": "用户目标",
  "total_calories": 整数（kcal）,
  "daily_plan": {{
    "早餐": [{{"food": "食材名", "portion": "份量如80克/1个/250毫升"}}],
    "午餐": [{{"food": "食材名", "portion": "份量"}}],
    "晚餐": [{{"food": "食材名", "portion": "份量"}}],
    "加餐": [{{"food": "食材名", "portion": "份量"}}]
  }},
  "nutrition_breakdown": {{"protein": 整数g, "carbohydrate": 整数g, "fat": 整数g}},
  "tips": ["烹饪方式建议", "饮食时间建议", "人群专属注意事项"],
  "avoided_foods": ["需要避免的食材"],
  "replaced_foods": [{{"from": "原食材", "to": "替换食材"}}]
}}

【用户档案】：{user_profile}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【健康目标】：{goal}
【过敏/忌口】：{restrictions}

请直接输出合法JSON：""",

    "food_recommend": """你是营养膳食推荐专家。根据用户现有的食材设计3餐菜谱。

【输出严格JSON格式，不要任何额外文字】：
{{
  "total_meals": 3,
  "meal_plan": [
    {{
      "meal_type": "早餐/午餐/晚餐",
      "name": "菜名",
      "ingredients": [{{"name":"食材名","amount":"用量"}}],
      "cook_method": "简易做法（1-2句话）",
      "calories_estimate": 整数kcal,
      "protein_estimate": 整数g,
      "tags": ["快手","营养","低脂"等标签]
    }}
  ],
  "total_calories": 整数kcal,
  "total_protein": 整数g,
  "tips": ["备餐建议", "替代方案建议"],
  "missing_ingredients": ["建议补充的食材"]
}}

【现有食材（必须全部合理使用）】：{ingredients}
【人群标签】：{crowd_type}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【健康目标】：{goal}

请直接输出合法JSON（所有食材要在用户提供的列表范围内）：""",

    "exercise": """你是运动健康指导专家。为用户设计安全科学的个性化一周运动方案。

【输出严格JSON格式，不要任何额外文字】：
{{
  "goal": "用户目标原文",
  "weekly_schedule": [
    {{"day": "周一/周二...", "exercise_type": "如快走/力量训练/瑜伽", "duration": "30", "intensity": "低/中/高", "description": "详细动作说明", "calories_burn_estimate": 整数}}
  ],
  "weekly_total_minutes": 整数分钟（150-300之间）,
  "weekly_total_calories": 整数kcal,
  "warm_up": "热身建议（5-10分钟）",
  "cool_down": "拉伸放松建议（5-10分钟）",
  "precautions": ["安全注意事项1", "安全注意事项2（慢病患者必须有）"],
  "progression_plan": "4周进阶计划说明"
}}

【用户档案】：{user_profile}
【用户健康档案（系统自动推导）】：
{user_derived_context}
【运动目标】：{goal}
【运动偏好】：{preferences}
【慢病情况】：{chronic_diseases}

请直接输出合法JSON（注意：每周不超过WHO建议上限300分钟）：""",
}


# ============================================================
# 本地/云端校验规则 (仅正常模式下执行)
# ============================================================

def _validate_diet_plan(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """一日饮食方案校验"""
    issues = []
    if not isinstance(result, dict):
        return False, ["输出不是字典格式"]

    # 必填字段
    required = ["daily_plan", "total_calories", "nutrition_breakdown"]
    for f in required:
        if f not in result:
            issues.append(f"缺少必填字段: {f}")

    # 至少3餐
    dp = result.get("daily_plan", {})
    meal_count = sum(1 for v in dp.values() if isinstance(v, list) and len(v) > 0)
    if meal_count < 3:
        issues.append(f"餐次数量不足: {meal_count}/3")

    # 热量合理区间 800-4000
    cal = result.get("total_calories", 0)
    if isinstance(cal, (int, float)) and (cal < 800 or cal > 4000):
        issues.append(f"总热量超出合理区间: {cal}")

    return len(issues) == 0, issues


def _validate_food_recommend(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """食材菜谱推荐校验"""
    issues = []
    if not isinstance(result, dict):
        return False, ["输出不是字典格式"]

    if "meal_plan" not in result:
        issues.append("缺少必填字段: meal_plan")
    else:
        mp = result.get("meal_plan", [])
        if not isinstance(mp, list) or len(mp) < 3:
            issues.append(f"菜谱数量不足: {len(mp) if isinstance(mp, list) else 0}/3")

    # 总热量区间
    tc = result.get("total_calories", 0)
    if isinstance(tc, (int, float)) and (tc < 500 or tc > 4500):
        issues.append(f"总热量超出合理区间: {tc}")

    return len(issues) == 0, issues


def _validate_exercise(result: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """运动方案校验"""
    issues = []
    if not isinstance(result, dict):
        return False, ["输出不是字典格式"]

    if "weekly_schedule" not in result:
        issues.append("缺少必填字段: weekly_schedule")
    else:
        ws = result.get("weekly_schedule", [])
        if not isinstance(ws, list) or len(ws) < 3:
            issues.append(f"周运动天数不足: {len(ws) if isinstance(ws, list) else 0}/3")

    # WHO 建议上限300分钟
    total_min = result.get("weekly_total_minutes", 0)
    if isinstance(total_min, (int, float)) and total_min > 300:
        issues.append(f"周运动总时长超出WHO建议上限: {total_min}分钟(上限300)")

    return len(issues) == 0, issues


def _validate_qa(result: str, chronic_diseases: List[str] = None) -> Tuple[bool, List[str]]:
    """健康问答要点校验（慢病特定要点）"""
    issues = []
    if not result or not isinstance(result, str) or len(result.strip()) < 50:
        issues.append("回答过短或为空")
        return False, issues

    # 慢病场景：高血压要点检查
    text = result
    cd = chronic_diseases or []
    if any(h in " ".join(cd) for h in ["高血压", "血压", "hypertension"]):
        key_points = ["盐", "运动", "体重", "酒"]
        missing = [kp for kp in key_points if kp not in text]
        if missing:
            issues.append(f"高血压建议缺少要点: {', '.join(missing)}")

    # 糖尿病场景
    if any(h in " ".join(cd) for h in ["糖尿病", "血糖", "diabetes"]):
        key_points = ["GI", "碳水", "运动"]
        missing = [kp for kp in key_points if kp not in text]
        if missing:
            issues.append(f"糖尿病建议缺少要点: {', '.join(missing)}")

    return len(issues) == 0, issues


VALIDATORS = {
    "qa": _validate_qa,
    "diet_plan": _validate_diet_plan,
    "food_recommend": _validate_food_recommend,
    "exercise": _validate_exercise,
}


# ============================================================
# 主路由器
# ============================================================

class ModeRouter:
    """A/C 方案双模式路由器（附带C方案知识库自增长闭环）"""

    # 主题重复判定阈值（向量余弦相似度；同主题完全一致文本实测 0.52~0.74，异方向 0.19~0.42）
    # 配合结构化匹配（func/人群/BMI 一致）使用，避免跨主题误判
    DUP_SIMILARITY_THRESHOLD = 0.45
    # 是否开启C方案结果入库（默认开启，可通过 init 的开关关闭）
    AUTO_INGEST_C_RESULTS = True

    def __init__(self):
        self._llm = None        # 注入：LLMRouter 实例
        self._retriever = None  # 注入：向量检索器
        self._local_engine = None  # 注入：本地兜底引擎
        self._auto_ingest = True
        self._dedup_service = None  # 四层去重服务
        self._relevance_check = False  # 本地大模型相关性校验开关

    def init(self, llm, retriever, local_engine=None, auto_ingest: bool = True):
        """注入依赖（由 orchestrator 初始化时调用）"""
        self._llm = llm
        self._retriever = retriever
        self._local_engine = local_engine
        self._auto_ingest = auto_ingest and self.AUTO_INGEST_C_RESULTS

        # 初始化四层去重服务
        try:
            from services.kb_dedup_service import KBDedupService
            from config.settings import settings
            self._dedup_service = KBDedupService(retriever, llm=llm)
            self._relevance_check = settings.KB_LOCAL_RELEVANCE_CHECK
            logger.info(f"[mode_router] 去重服务已启用 | 相关性校验={self._relevance_check} | 双层存储={settings.KB_DUAL_LAYER_STORAGE}")
        except Exception as e:
            logger.warning(f"[mode_router] 去重服务初始化失败，降级为原有逻辑: {e}")
            self._dedup_service = None

    # ---------- 通用入口 ----------

    def route(self, func_type: str, high_performance: bool = False, **kwargs) -> Dict[str, Any]:
        """统一路由入口

        参数:
            func_type: qa / diet_plan / food_recommend / exercise
            high_performance: True=高性能模式(直接云端无校验)；False=正常模式(模板→本地→回退)
            **kwargs: 各功能的实际参数

        返回:
            {
              "result": 实际结果（dict或str）,
              "mode": "high_performance" / "normal",
              "route": "C_direct" / "A_template_local" / "C_fallback" / "C_direct_fallback_local" / "A_template_local",
              "timing_ms": {...},
              "validation": {"passed": True/False, "issues": [...]} (仅normal模式)
            }
        """
        start = time.time()
        timing = {}

        if high_performance:
            # ============= 高性能模式：直接 C 方案，跳过校验；云端失败自动回退本地兜底 =============
            t0 = time.time()
            try:
                result = self._run_cloud(func_type, timeout=settings.LLM_TIMEOUT_HIGH_PERF, **kwargs)
                timing["cloud_ms"] = round((time.time() - t0) * 1000)
                route = "C_direct"
            except Exception as e:
                # 云端异常（限流/断网/额度耗尽）→ 本地引擎兜底（保证用户可用）
                logger.warning(f"[高性能模式C失败回退本地] {func_type} err={type(e).__name__}: {e}")
                t_local = time.time()
                result = self._local_fallback(func_type, **kwargs)
                timing["cloud_fail_ms"] = round((t_local - t0) * 1000)
                timing["local_fallback_ms"] = round((time.time() - t_local) * 1000)
                route = "C_direct_fallback_local"
                resp_extra = {"cloud_error": f"{type(e).__name__}: {str(e)[:200]}"}
            timing["total_ms"] = round((time.time() - start) * 1000)

            resp = {
                "result": result,
                "mode": "high_performance",
                "route": route,
                "timing_ms": timing,
                "validation": {"skipped": True, "reason": "high_performance模式"},
            }
            if "resp_extra" in dir():
                resp.update(resp_extra)
            # 闭环：C 方案结果存入向量知识库（含检索+embedding+写库，耗时）
            # 高性能模式 → 后台线程执行，主流程立即返回；失败仅记日志
            if route == "C_direct":
                try:
                    async_task_service._executor.submit(
                        self._ingest_c_result_async, func_type, result, "C_direct", kwargs)
                except Exception as e:
                    logger.debug(f"[C_direct异步入库提交失败] {e}")
            # 本地大模型相关性校验（耗时本地 LLM 调用）
            # 高性能模式 → 后台线程执行，结果异步注入 validation.relevance；失败仅记日志
            try:
                async_task_service._executor.submit(
                    self._apply_relevance_check_async, resp, func_type, result, kwargs)
            except Exception as e:
                logger.debug(f"[相关性校验异步提交失败] {e}")
            return resp

        else:
            # ============= 正常模式：A → 失败 → C 带校验；C异常再回退A结果 =============

            # Stage 1: 模板召回 + 本地改写 (A方案)
            t1 = time.time()
            template_content, skip_llm = self._retrieve_template(func_type, **kwargs)
            timing["retrieve_ms"] = round((time.time() - t1) * 1000)

            t2 = time.time()
            if skip_llm and template_content:
                # 极高相似度命中：直接返回模板原文，跳过本地改写（0 token）
                if func_type == "qa":
                    a_result = template_content
                else:
                    try:
                        a_result = json.loads(template_content)
                    except Exception:
                        # 模板非合法 JSON → 回退本地改写
                        a_result = self._run_local_rewrite(func_type, template_content, **kwargs)
            else:
                a_result = self._run_local_rewrite(func_type, template_content, **kwargs)
            timing["local_rewrite_ms"] = round((time.time() - t2) * 1000)

            # Stage 2: 校验 A 方案输出
            validator = VALIDATORS.get(func_type)
            t3 = time.time()
            if func_type == "qa":
                chronic = kwargs.get("chronic_diseases") or kwargs.get("user_profile", {}).get("chronic_diseases", [])
                a_passed, a_issues = validator(a_result, chronic) if validator else (True, [])
            else:
                a_passed, a_issues = validator(a_result) if validator else (True, [])
            timing["validate_a_ms"] = round((time.time() - t3) * 1000)

            if a_passed:
                timing["total_ms"] = round((time.time() - start) * 1000)
                resp = {
                    "result": a_result,
                    "mode": "normal",
                    "route": "A_template_local",
                    "timing_ms": timing,
                    "validation": {"passed": True, "stage": "A", "issues": a_issues},
                }
                self._apply_relevance_check(resp, func_type, a_result, **kwargs)
                return resp

            # Stage 3: A 方案校验不通过 → 回退 C 方案 (带校验)
            cloud_error = None
            c_result = None
            c_passed = False
            c_issues = []
            t4 = time.time()
            try:
                c_result = self._run_cloud(func_type, **kwargs)
                timing["cloud_fallback_ms"] = round((time.time() - t4) * 1000)
            except Exception as e:
                # C 方案异常：如额度耗尽/网络异常 → 仍然返回A方案结果，route 保持 A_template_local，标注 c_fallback_failed
                cloud_error = f"{type(e).__name__}: {str(e)[:300]}"
                logger.warning(f"[C回退失败，沿用A方案] {func_type} err={cloud_error}")
                timing["cloud_fallback_ms"] = round((time.time() - t4) * 1000)
                final_result = a_result
                resp = {
                    "result": final_result,
                    "mode": "normal",
                    "route": "A_template_local",
                    "timing_ms": timing,
                    "validation": {
                        "passed": True,  # A方案已不通过但C失败，仍然降级返回；用passed=True保证前端正常解析
                        "stage": "A_C_fallback_failed",
                        "a_issues": a_issues,
                        "c_fallback_error": cloud_error,
                    },
                }
                timing["total_ms"] = round((time.time() - start) * 1000)
                resp["timing_ms"] = timing
                return resp

            # C 方案成功：再校验
            t5 = time.time()
            if func_type == "qa":
                chronic = kwargs.get("chronic_diseases") or kwargs.get("user_profile", {}).get("chronic_diseases", [])
                c_passed, c_issues = validator(c_result, chronic) if validator else (True, [])
            else:
                c_passed, c_issues = validator(c_result) if validator else (True, [])
            timing["validate_c_ms"] = round((time.time() - t5) * 1000)

            timing["total_ms"] = round((time.time() - start) * 1000)

            final_result = c_result if c_passed else (a_result if a_result else c_result)
            resp = {
                "result": final_result,
                "mode": "normal",
                "route": "C_fallback",
                "timing_ms": timing,
                "validation": {
                    "passed": c_passed,
                    "stage": "C_fallback",
                    "a_issues": a_issues,
                    "c_issues": c_issues,
                },
            }
            if cloud_error:
                resp["cloud_error"] = cloud_error
            # 闭环：C 方案回退的结果也入库（用户有真实需求，A方案未通过所以走C，信息更宝贵）
            if c_result is not None:
                try:
                    self._ingest_c_result(func_type, final_result, trigger_route="C_fallback", **kwargs)
                except Exception as e:
                    logger.debug(f"[C_fallback入库忽略] {e}")
            # 本地大模型相关性校验
            self._apply_relevance_check(resp, func_type, final_result, **kwargs)
            return resp

    # ---------- 内部方法 ----------

    def _retrieve_template(self, func_type: str, **kwargs) -> Tuple[str, bool]:
        """向量知识库模板召回（无匹配则返回空）

        返回: (template_text, skip_llm)
        - template_text: 命中的模板正文（多条用换行拼接）
        - skip_llm: 极高相似度命中时 True，调用方可直接返回模板跳过本地改写（0 token）
        人群标签先规范化（糖尿病患者→糖尿病），再用 KB 长名做 where 预过滤。
        """
        if not self._retriever or self._retriever.count() == 0:
            return "", False

        # 确定人群（KB 长名，用于 where 过滤）
        crowd_raw = ""
        if func_type in ("qa", "diet_plan", "exercise"):
            up = kwargs.get("user_profile", {}) or {}
            crowd_raw = up.get("crowd_type") or up.get("crowdType") or ""
        elif func_type == "food_recommend":
            crowd_raw = kwargs.get("crowd_type", "")
        kb_crowd = crowd_kb_name(crowd_raw) if crowd_raw else ""

        # 构造检索 query
        query_parts = []
        if func_type == "qa":
            query_parts.append(kwargs.get("question", ""))
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {})
            query_parts.append(f"{crowd_display_name(crowd_raw)} {kwargs.get('goal','')} 一日膳食方案 三餐模板")
        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", [])
            query_parts.append(f"{crowd_display_name(crowd_raw)} 食材菜谱推荐 {' '.join(ings[:3])}")
        elif func_type == "exercise":
            up = kwargs.get("user_profile", {})
            chronic = " ".join(kwargs.get("chronic_diseases") or [])
            query_parts.append(f"{crowd_display_name(crowd_raw)} {kwargs.get('goal','')} {chronic} 一周运动方案")

        query = " ".join(filter(None, query_parts)).strip()
        if not query:
            return "", False

        try:
            # 多拉候选，按相似度过滤，命中不足返回空
            results = self._retriever.search(query, top_k=5, target_crowd=kb_crowd)
            min_sim = settings.TEMPLATE_MIN_SIMILARITY
            skip_th = settings.TEMPLATE_MATCH_SKIP_LLM_THRESHOLD
            filtered = [r for r in results if r.get("similarity", 0) >= min_sim]
            if not filtered:
                return "", False
            # 极高匹配（≥0.95）直接返回模板原文，跳过 LLM 改写（0 token 消耗）
            skip_llm = filtered[0].get("similarity", 0) >= skip_th
            return "\n".join(r.get("content", "") for r in filtered[:2]), skip_llm
        except Exception:
            return "", False

    def _run_local_rewrite(self, func_type: str, template: str, **kwargs) -> Any:
        """A方案：本地 Ollama 基于模板改写（无模板则走本地引擎兜底）"""

        # 如果没有模板且有本地引擎，直接走本地规则
        if (not template or not template.strip()) and self._local_engine:
            return self._local_fallback(func_type, **kwargs)

        # 尝试本地 LLM 改写
        prompt_template = REWRITE_PROMPTS.get(func_type)
        if not prompt_template:
            return self._local_fallback(func_type, **kwargs)

        try:
            # 构造 prompt 参数
            fmt_params = self._build_prompt_params(func_type, template, **kwargs)
            prompt = prompt_template.format(**fmt_params)

            messages = [
                {"role": "system", "content": "你是专业的健康内容改写助手。严格按照要求输出。"},
                {"role": "user", "content": prompt},
            ]

            # 强制本地模式调用（mode 参数本次调用局部生效，不修改共享 _mode，避免并发串台）
            if func_type == "qa":
                output = self._llm.chat(messages, max_retries=1, mode="local")
            else:
                output = self._llm.chat_json(messages, max_retries=1, mode="local")

            # 结构化校验：确保 JSON 不为空
            if func_type != "qa" and (not output or not isinstance(output, dict)):
                return self._local_fallback(func_type, **kwargs)
            return output

        except Exception:
            # 本地 LLM 失败，退回本地规则引擎
            return self._local_fallback(func_type, **kwargs)

    def _run_cloud(self, func_type: str, timeout: Optional[int] = None, **kwargs) -> Any:
        """C方案：云端 DeepSeek 一次性生成

        timeout: 单次请求超时覆盖（高性能演示模式可放宽，默认用 settings.LLM_TIMEOUT）
        """
        prompt_template = CLOUD_PROMPTS.get(func_type)
        if not prompt_template:
            return {} if func_type != "qa" else ""

        fmt_params = self._build_prompt_params(func_type, "", **kwargs)
        prompt = prompt_template.format(**fmt_params)

        messages = [
            {"role": "system", "content": "你是专业的健康/营养/运动专家。严格按照要求输出。"},
            {"role": "user", "content": prompt},
        ]

        # 强制云端模式（mode 参数本次调用局部生效，不修改共享 _mode，避免并发串台）
        if func_type == "qa":
            output = self._llm.chat(messages, max_retries=2, timeout=timeout, mode="cloud")
        else:
            output = self._llm.chat_json(messages, max_retries=2, timeout=timeout, mode="cloud")

        return output

    def stream_qa(self, high_performance: bool = False, **kwargs) -> Any:
        """QA 真流式：返回云端流式增量生成器（高性能模式专用，逐字/逐句推送）

        与 _run_cloud("qa") 共用 CLOUD_PROMPTS["qa"] 的 prompt 构造，
        仅将非流式 chat 替换为 chat_stream（OpenAI stream=True 流式接口）。
        每次迭代 yield 一段增量文本；异常时 LLMRouter.chat_stream 内部
        会 yield 一条 "[流式响应异常: ...]" 标记，不主动抛出。

        返回: 同步生成器（每次 yield str），调用方用 asyncio.to_thread 桥接。
        """
        prompt_template = CLOUD_PROMPTS.get("qa")
        if not prompt_template or not self._llm:
            return (x for x in [])
        timeout = settings.LLM_TIMEOUT_HIGH_PERF if high_performance else settings.LLM_TIMEOUT
        fmt_params = self._build_prompt_params("qa", "", **kwargs)
        prompt = prompt_template.format(**fmt_params)
        messages = [
            {"role": "system", "content": "你是专业的健康/营养/运动专家。严格按照要求输出。"},
            {"role": "user", "content": prompt},
        ]
        return self._llm.chat_stream(messages, timeout=timeout)

    # ---------- 工具方法 ----------

    def _build_prompt_params(self, func_type: str, template: str, **kwargs) -> Dict[str, Any]:
        """构造 prompt 填充参数（各功能通用）"""
        p = {"template_content": template if template else "（无可用模板，请自行生成）"}

        # 系统自动推导的用户健康上下文（BMI分类/每日热量需求/运动水平/今日饮食/近期运动）
        p["user_derived_context"] = self._compute_user_derived_context(**kwargs)

        if func_type == "qa":
            up = kwargs.get("user_profile", {})
            p["question"] = kwargs.get("question", "")
            p["user_profile"] = json.dumps(up, ensure_ascii=False) if isinstance(up, dict) else str(up)

        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {})
            p["user_profile"] = json.dumps(up, ensure_ascii=False) if isinstance(up, dict) else str(up)
            p["goal"] = kwargs.get("goal", "均衡饮食")
            allergies = up.get("allergies", []) if isinstance(up, dict) else []
            restrictions = up.get("dietary_restrictions", []) if isinstance(up, dict) else []
            p["restrictions"] = f"过敏: {allergies}; 忌口: {restrictions}"

        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", [])
            p["ingredients"] = "、".join(ings) if isinstance(ings, list) else str(ings)
            p["crowd_type"] = crowd_display_name(kwargs.get("crowd_type", "普通人"))
            p["goal"] = kwargs.get("goal", "健康饮食")

        elif func_type == "exercise":
            up = kwargs.get("user_profile", {})
            p["user_profile"] = json.dumps(up, ensure_ascii=False) if isinstance(up, dict) else str(up)
            p["goal"] = kwargs.get("goal", "保持健康")
            p["preferences"] = kwargs.get("preferences", "无")
            cd = kwargs.get("chronic_diseases", [])
            p["chronic_diseases"] = "、".join(cd) if isinstance(cd, list) and cd else "无"

        return p

    # ============================================================
    # 用户健康上下文自动推导（注入大模型，用户无需在问题中重复说明）
    # ============================================================

    def _compute_user_derived_context(self, **kwargs) -> str:
        """根据用户已设置的身高/体重/年龄/性别/今日饮食/近期运动，
        自动推导：BMI 分类、每日热量需求(TDEE)、运动水平分级、今日饮食快照、近7日运动汇总。
        返回一段可直接拼入 prompt 的自然语言文本。"""
        parts = []

        # ---------- 1) 合并画像（兼容 user_profile / health_snapshot.profile / today_body_metrics） ----------
        up = kwargs.get("user_profile", {}) or {}
        hs = kwargs.get("health_snapshot", {}) or {}
        profile = hs.get("profile", {}) if isinstance(hs, dict) else {}
        if not profile:
            profile = up
        metrics = hs.get("today_body_metrics", {}) if isinstance(hs, dict) else {}

        height = profile.get("height_cm") or profile.get("height") or metrics.get("height_cm")
        weight = profile.get("weight_kg") or profile.get("weight") or metrics.get("weight_kg")
        age = profile.get("age")
        gender = profile.get("gender")
        bmi = profile.get("bmi") or metrics.get("bmi")

        # ---------- 2) BMI 与分类 ----------
        if not bmi and height and weight:
            try:
                h_m = float(height) / 100.0
                if h_m > 0:
                    bmi = round(float(weight) / (h_m * h_m), 1)
            except (TypeError, ValueError):
                bmi = None

        if bmi:
            try:
                bmi = float(bmi)
            except (TypeError, ValueError):
                bmi = None
        if bmi:
            if bmi < 18.5:
                bmi_cn = "过低"
            elif bmi < 20:
                bmi_cn = "偏低"
            elif bmi < 24:
                bmi_cn = "正常"
            elif bmi < 28:
                bmi_cn = "偏高"
            else:
                bmi_cn = "超高"

        # ---------- 3) 每日热量需求（Mifflin-St Jeor BMR × 活动系数） ----------
        recent_exercise = kwargs.get("recent_exercise") or hs.get("recent_exercise") or {}
        today_diet = kwargs.get("today_diet") or hs.get("today_diet")
        today_diet_total = kwargs.get("today_diet_total") or hs.get("today_diet_total") or {}

        activity_factor, activity_level = 1.2, "久坐（基本无运动）"
        try:
            sessions = int(recent_exercise.get("total_sessions", 0) or 0)
            duration = int(recent_exercise.get("total_duration_min", 0) or 0)
            if sessions >= 5 and duration >= 300:
                activity_factor, activity_level = 1.725, "高强度运动（每周≥5次且≥300分钟）"
            elif sessions >= 3 and duration >= 150:
                activity_factor, activity_level = 1.55, "中度运动（每周3-4次，约150-299分钟）"
            elif sessions >= 1 and duration >= 75:
                activity_factor, activity_level = 1.375, "低强度运动（每周1-2次或不足150分钟）"
            elif sessions > 0:
                activity_factor, activity_level = 1.2, "久坐为主（有零星运动记录）"
        except (TypeError, ValueError):
            pass

        bmr, tdee = None, None
        try:
            if height and weight and age:
                h, w, a = float(height), float(weight), int(age)
                bmr = 10 * w + 6.25 * h - 5 * a + (5 if gender == "男" else -161)
                tdee = round(bmr * activity_factor)
                bmr = round(bmr)
        except (TypeError, ValueError):
            pass

        # ---------- 4) 今日饮食快照 ----------
        diet_lines = []
        if isinstance(today_diet, list) and today_diet:
            for meal in today_diet:
                if not isinstance(meal, dict):
                    continue
                mt = meal.get("meal_type", "")
                foods = meal.get("foods") or []
                food_names = []
                for f in foods:
                    if not isinstance(f, dict):
                        continue
                    nm = f.get("food_name", "")
                    w = f.get("eat_weight_g")
                    food_names.append(f"{nm}{w if w is not None else ''}g".replace("gg", "g"))
                cal = meal.get("meal_calories_kcal")
                diet_lines.append(
                    f"{mt}：{'、'.join(food_names) if food_names else '（未记录明细）'}"
                    + (f"（约{cal}kcal）" if cal is not None else "")
                )
        if today_diet_total and isinstance(today_diet_total, dict):
            tc = today_diet_total.get("total_calories_kcal")
            tp = today_diet_total.get("total_protein_g")
            tcar = today_diet_total.get("total_carb_g")
            tf = today_diet_total.get("total_fat_g")
            if tc is not None:
                diet_lines.append(
                    f"今日合计：{tc}kcal ｜ 蛋白质{tp}g ｜ 碳水{tcar}g ｜ 脂肪{tf}g"
                )
        diet_txt = "\n    ".join(diet_lines) if diet_lines else "今日暂无饮食记录"

        # ---------- 5) 近7日运动汇总 ----------
        ex_lines = []
        if isinstance(recent_exercise, dict) and recent_exercise.get("note") is None:
            ex_lines.append(
                f"近7日运动：{recent_exercise.get('total_sessions', 0)}次，共"
                f"{recent_exercise.get('total_duration_min', 0)}分钟，约消耗"
                f"{recent_exercise.get('total_calories_burned', 0)}kcal"
            )
        else:
            ex_lines.append("近7日运动：暂无运动记录")

        # ---------- 6) 组装 ----------
        info = []
        gender_txt = gender or "未知"
        age_txt = f"{age}岁" if age is not None else "未知"
        hw_txt = f"身高{height}cm，体重{weight}kg" if height and weight else "身高/体重未记录"
        info.append(f"基本信息：{gender_txt}，{age_txt}，{hw_txt}")
        if bmi:
            info.append(f"BMI={bmi}（{bmi_cn}）")
        if tdee:
            info.append(
                f"每日热量需求：基础代谢BMR≈{bmr}kcal，活动水平为「{activity_level}」"
                f"（活动系数{activity_factor}），每日维持热量≈{tdee}kcal"
            )
        info.append(f"今日饮食：\n    {diet_txt}")
        info.append(f"{ex_lines[0]}")

        parts.append("\n".join(info))
        return "\n".join(parts)

    def _local_fallback(self, func_type: str, **kwargs) -> Any:
        """本地规则引擎兜底（A方案的最后一道防线）"""
        if not self._local_engine:
            return {} if func_type != "qa" else "（本地服务暂不可用）"

        try:
            if func_type == "diet_plan":
                return self._local_engine.fallback_diet_plan(
                    kwargs.get("user_profile", {}),
                    kwargs.get("goal", "")
                )
            elif func_type == "food_recommend":
                return self._local_engine.fallback_food_recommend(
                    kwargs.get("ingredients", []),
                    canonical_crowd(kwargs.get("crowd_type", "普通人")),
                    kwargs.get("goal", "健康饮食")
                )
            elif func_type == "exercise":
                return self._local_engine.fallback_exercise_advice(
                    kwargs.get("user_profile", {}),
                    kwargs.get("goal", ""),
                    kwargs.get("preferences", ""),
                    kwargs.get("chronic_diseases", [])
                )
            elif func_type == "qa":
                up = kwargs.get("health_snapshot") or {}
                return self._local_engine.answer_health_query(kwargs.get("question", ""), up)
        except Exception:
            pass

        return {} if func_type != "qa" else "（本地服务暂不可用）"

    # ============================================================
    # 本地大模型相关性校验（降低答非所问风险）
    # ============================================================

    def _apply_relevance_check(self, resp: Dict[str, Any], func_type: str,
                                result: Any, **kwargs) -> Dict[str, Any]:
        """对生成结果做本地大模型相关性校验，结果注入 resp['validation']['relevance']。
        - 开关由 settings.KB_LOCAL_RELEVANCE_CHECK 控制
        - 校验失败/异常均不阻断主流程，仅记录结果
        - 相关性过低时在 validation 中标注，前端可据此提示
        """
        if not self._relevance_check or not self._dedup_service:
            return resp

        user_question = self._build_user_question_for_relevance(func_type, **kwargs)
        if not user_question or len(user_question.strip()) < 2:
            return resp

        answer_text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)[:600]

        try:
            rel = self._dedup_service.check_relevance_with_local_llm(
                user_question, answer_text
            )
            val = resp.get("validation")
            if not isinstance(val, dict):
                val = {}
            val["relevance"] = rel
            resp["validation"] = val
            # 相关性低 → 记录告警日志便于排查（不改变返回结果）
            if isinstance(rel, dict) and not rel.get("relevant", True):
                logger.warning(
                    f"[相关性校验] func={func_type} 判定不相关 | "
                    f"conf={rel.get('confidence', 0)} | {rel.get('reason', '')[:100]}"
                )
        except Exception as e:
            logger.debug(f"[相关性校验异常，已忽略] {e}")
        return resp

    # ---------------- 高性能模式后台执行包装（异步化，主流程立即返回） ----------------

    def _ingest_c_result_async(self, func_type, result, trigger_route: str, kwargs: dict):
        """后台线程执行 C 方案入库：失败只记日志，不影响主流程"""
        try:
            self._ingest_c_result(func_type, result, trigger_route=trigger_route, **kwargs)
        except Exception as e:
            logger.debug(f"[C_direct后台入库失败，已忽略] {type(e).__name__}: {e}")

    def _apply_relevance_check_async(self, resp: Dict[str, Any], func_type: str,
                                     result: Any, kwargs: dict):
        """后台线程执行本地大模型相关性校验：失败只记日志，不影响主流程"""
        try:
            self._apply_relevance_check(resp, func_type, result, **kwargs)
        except Exception as e:
            logger.debug(f"[后台相关性校验失败，已忽略] {type(e).__name__}: {e}")

    def _build_user_question_for_relevance(self, func_type: str, **kwargs) -> str:
        """为相关性校验构造代表性用户问题（qa 取原文，其他功能由参数推导）"""
        if func_type == "qa":
            return kwargs.get("question", "")
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {}) or {}
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')}人群BMI={up.get('bmi','')}的{kwargs.get('goal','')}一日饮食方案"
        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", []) or []
            return f"用{','.join(list(ings)[:3])}做{kwargs.get('goal','')}菜谱推荐"
        else:  # exercise
            up = kwargs.get("user_profile", {}) or {}
            chronic = "、".join(kwargs.get("chronic_diseases") or [])
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')}人群{kwargs.get('goal','')}{chronic}一周运动方案"

    # ============================================================
    # 知识库自增长闭环：C 方案结果 → 入库（主题重复则高性能模式整合）
    # ============================================================

    def _extract_crowd_and_goal(self, func_type: str, **kwargs) -> tuple:
        """从 kwargs 解析：(人群标签短名, 主诉方向/目标, 用户画像dict, BMI_id, BMI中文名)
        人群标签统一走 canonical_crowd 规范化：糖尿病患者→糖尿病、健身人群→健身、老年人→老年。
        兼容 crowd_type / crowdType 两种字段名（Python端/JAVA端）。"""
        up = {}
        crowd = "通用"
        goal = "保持健康"

        if func_type == "qa":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = (kwargs.get("question", "") or "")[:20] or "健康问答"
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = kwargs.get("goal", "") or "均衡饮食"
        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", []) or []
            crowd = canonical_crowd(kwargs.get("crowd_type", "通用"))
            goal = (kwargs.get("goal", "") or "健康饮食") + f"（食材:{','.join(list(ings)[:3])}）"
        elif func_type == "exercise":
            up = kwargs.get("user_profile", {}) or {}
            crowd = canonical_crowd(up.get("crowd_type") or up.get("crowdType") or "通用")
            goal = kwargs.get("goal", "") or "保持健康"

        # BMI 分类
        bmi_val = up.get("bmi") if isinstance(up, dict) else None
        if bmi_val and isinstance(bmi_val, (int, float)):
            if bmi_val < 18.5:
                bmi_id, bmi_cn = "very_low", "过低"
            elif bmi_val < 20:
                bmi_id, bmi_cn = "low", "偏低"
            elif bmi_val < 24:
                bmi_id, bmi_cn = "normal", "正常"
            elif bmi_val < 28:
                bmi_id, bmi_cn = "high", "偏高"
            else:
                bmi_id, bmi_cn = "very_high", "超高"
        else:
            bmi_id, bmi_cn = "normal", "正常"

        return crowd, goal, up if isinstance(up, dict) else {}, bmi_id, bmi_cn

    def _build_ingest_doc(self, func_type: str, result: Any, **kwargs) -> tuple:
        """把 C 方案结果 → ChromaDB 的 (document, metadata_dict)。
        document 文本格式与 generate_kb_templates.py 保持一致，便于同库检索命中。
        target_crowd 等 metadata 统一使用 KB 长名（糖尿病患者/健身人群/老年人），保证 where 预过滤可命中。"""
        crowd, goal, up, bmi_id, bmi_cn = self._extract_crowd_and_goal(func_type, **kwargs)
        crowd_disp = crowd_display_name(crowd)     # 展示名：糖尿病患者
        crowd_kb = crowd_kb_name(crowd)            # KB 长名：糖尿病患者

        if func_type == "qa":
            question = kwargs.get("question", "")
            answer = result if isinstance(result, str) else (
                result.get("answer", "") if isinstance(result, dict) else str(result)
            )
            title = f"问答模板｜{crowd_disp}｜BMI{bmi_cn}｜{goal[:16]}｜{question[:20]}"
            document = f"【标题】{title}\n【用户问题】{question}\n\n【专业回答】\n{answer}"
            category = "dietary_guideline" if crowd == "普通人" else "crowd_specific"
        elif func_type == "diet_plan":
            cal = result.get("total_calories", "") if isinstance(result, dict) else ""
            g = result.get("goal", goal) if isinstance(result, dict) else goal
            title = f"饮食方案｜{crowd_disp}｜BMI{bmi_cn}｜{g[:16]}｜{cal}kcal"
            daily_plan = json.dumps(result.get("daily_plan", {}), ensure_ascii=False, indent=2) if isinstance(result, dict) else ""
            nb = json.dumps(result.get("nutrition_breakdown", {}), ensure_ascii=False) if isinstance(result, dict) else ""
            tips = result.get("tips", []) if isinstance(result, dict) else []
            avoided = result.get("avoided_foods", []) if isinstance(result, dict) else []
            replaced = json.dumps(result.get("replaced_foods", []), ensure_ascii=False) if isinstance(result, dict) else "[]"
            document = (
                f"【标题】{title}\n"
                f"【目标】{g}（每日总热量 {cal}kcal）\n\n"
                f"【一日膳食方案】\n{daily_plan}\n\n"
                f"【三大营养素】{nb}\n\n"
                f"【人群专属建议】\n" + "\n".join(f"- {t}" for t in tips) + "\n\n"
                f"【禁忌食材】{','.join(avoided)}\n【替换方案】{replaced}"
            )
            category = "crowd_specific"
        elif func_type == "food_recommend":
            title = f"菜谱模板｜{crowd_disp}｜BMI{bmi_cn}｜{goal[:16]}"
            meals = result.get("meal_plan", []) if isinstance(result, dict) else []
            lines = []
            for m in meals:
                lines.append(
                    f"【{m.get('meal_type','')}】{m.get('name','')}\n"
                    f"  食材：{json.dumps(m.get('ingredients', []), ensure_ascii=False)}\n"
                    f"  做法：{m.get('cook_method','')}\n"
                    f"  热量{m.get('calories_estimate','')}kcal，蛋白质{m.get('protein_estimate','')}g，标签：{','.join(m.get('tags', []))}"
                )
            document = (
                f"【标题】{title}\n"
                f"【全日总览】总热量{result.get('total_calories','') if isinstance(result,dict) else ''}kcal，"
                f"蛋白质{result.get('total_protein','') if isinstance(result,dict) else ''}g\n\n"
                + "\n\n".join(lines) + "\n\n"
                + "【备餐与替代建议】\n"
                + "\n".join(f"- {t}" for t in (result.get("tips", []) if isinstance(result, dict) else [])) + "\n"
                + "【建议补充】" + ",".join(result.get("missing_ingredients", []) if isinstance(result, dict) else [])
            )
            category = "meal_guidance"
        else:  # exercise
            title = f"运动方案｜{crowd_disp}｜BMI{bmi_cn}｜{goal[:16]}"
            sched = result.get("weekly_schedule", []) if isinstance(result, dict) else []
            dl = []
            for d in sched:
                dl.append(
                    f"【{d.get('day','')}】{d.get('exercise_type','')}｜{d.get('duration','')}分钟｜强度{d.get('intensity','')}｜消耗{d.get('calories_burn_estimate','')}kcal\n"
                    f"  动作说明：{d.get('description','')}"
                )
            document = (
                f"【标题】{title}\n"
                f"【目标】{result.get('goal', goal) if isinstance(result,dict) else goal}\n"
                f"【本周总量】{result.get('weekly_total_minutes','') if isinstance(result,dict) else ''}分钟，"
                f"约消耗{result.get('weekly_total_calories','') if isinstance(result,dict) else ''}kcal\n\n"
                + "\n\n".join(dl) + "\n\n"
                + f"【热身】{result.get('warm_up','') if isinstance(result,dict) else ''}\n"
                + f"【放松】{result.get('cool_down','') if isinstance(result,dict) else ''}\n\n"
                + "【安全注意事项】\n"
                + "\n".join(f"- {p}" for p in (result.get("precautions", []) if isinstance(result, dict) else [])) + "\n\n"
                + f"【4周进阶计划】{result.get('progression_plan','') if isinstance(result,dict) else ''}"
            )
            category = "crowd_specific"

        card_id = f"live_c_{func_type}_{crowd}_{bmi_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        metadata = {
            # 用户要求的核心标注（方便召回时快速过滤）——人群统一用 KB 长名
            "template_type": "ai_template",
            "func_type": func_type,
            "target_crowd": crowd_kb,
            "crowd": crowd_kb,
            "group": crowd_kb,
            "bmi_id": bmi_id,
            "bmi_cn": bmi_cn,
            "direction": goal[:40],

            # 兼容原有字段
            "category": category,
            "source": f"用户对话C方案_{func_type}",
            "topic": f"{crowd_kb}-BMI{bmi_cn}-{goal[:30]}",
            "source_channel": "live_c_ingest_v1",
            "source_type": "vector_kb",
            "is_official_guide": "False",
            "version": "1.0",
            "ingest_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "card_id": card_id,
        }
        metadata = {k: v for k, v in metadata.items() if v is not None and str(v) != ""}
        return document, metadata, card_id

    def _build_match_query(self, func_type: str, **kwargs) -> str:
        """构造相似度查询 query（用于判定是否主题重复）"""
        if func_type == "qa":
            return kwargs.get("question", "")
        elif func_type == "diet_plan":
            up = kwargs.get("user_profile", {}) or {}
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')} {kwargs.get('goal','')} 一日膳食方案 BMI={up.get('bmi','')}"
        elif func_type == "food_recommend":
            ings = kwargs.get("ingredients", []) or []
            return f"{crowd_display_name(kwargs.get('crowd_type',''))} {kwargs.get('goal','')} 食材菜谱推荐 {' '.join(list(ings)[:3])}"
        else:  # exercise
            up = kwargs.get("user_profile", {}) or {}
            chronic = " ".join(kwargs.get("chronic_diseases") or [])
            return f"{crowd_display_name(up.get('crowd_type') or up.get('crowdType') or '')} {kwargs.get('goal','')} {chronic} 一周运动方案"

    def _merge_with_cloud(self, func_type, old_content, new_result, **kwargs) -> str:
        """主题重复时：调用云端（高性能模式）把旧模板内容和新结果合并成更优质的一条。
        返回新的 document 字符串（直接入库，不再走 _build_ingest_doc 的结构化构造）。"""
        new_json_or_str = new_result if isinstance(new_result, str) else json.dumps(new_result, ensure_ascii=False, indent=2)
        crowd, goal, _, bmi_id, bmi_cn = self._extract_crowd_and_goal(func_type, **kwargs)
        msgs = [
            {"role": "system", "content": (
                "你是知识库编审专家。现在知识库中已经存在一条相似主题的模板，用户又调用云端API生成了一条新结果。"
                "请把两者合并去重，整合成一条更全面、更权威的模板："
                "1) 保留两者的优点和差异化信息；删除重复内容；"
                "2) 结构化内容按更合理的顺序重排（如饮食方案按餐次顺序、运动方案按周一到周日）；"
                "3) 冲突的数据（如热量值不一致）取新结果优先，保留旧值作备选并加注释；"
                "4) 最终输出保持与源文档相同的【标题】+正文格式，不要改变标题结构；"
                "5) 标题里追加「[整合版]」字样；"
                "6) QA 场景：把两个回答合并成要点更全的一个回答，问题只保留最贴合用户实际的版本。"
                "直接输出纯文本正文，不要JSON包裹，不要markdown标记。"
            )},
            {"role": "user", "content": (
                f"【功能】{func_type} | 人群:{crowd} | BMI:{bmi_cn}({bmi_id}) | 主诉:{goal}\n\n"
                "【库内旧模板】\n"
                f"{old_content}\n\n"
                "【新生成的云端结果】\n"
                f"{new_json_or_str}\n\n"
                "请按要求合并为1条更优质的模板文本（【标题】……开头）："
            )},
        ]
        # 强制云端模式（mode 参数本次调用局部生效，不修改共享 _mode，避免并发串台）
        try:
            merged = self._llm.chat(msgs, max_retries=1, mode="cloud") or ""
        except Exception as e:
            logger.debug(f"[云端整合] 失败: {e}")
            # 整合失败就直接把两者拼接作为 fallback
            merged = (
                f"[整合失败·双份保留]\n======== 旧模板 ========\n{old_content}\n"
                f"\n======== 新结果 ========\n{new_json_or_str}"
            )

        # 补上 [整合版] 标题（如果模型没加）
        if "[整合版]" not in merged and merged.startswith("【标题】"):
            merged = merged.replace("【标题】", "【标题】[整合版] ", 1)
        return merged

    def _is_same_topic(self, top, func_type: str, crowd_kb: str, bmi_id: str) -> bool:
        """结构化判定命中模板与当前请求是否同一主题：
        仅当 func_type、人群（KB长名）、BMI 档位全部一致时才视为同主题，
        避免不同功能/不同人群/不同BMI档位被误判为重复。"""
        meta = top.get("metadata") or {}
        if not isinstance(meta, dict):
            return False
        if meta.get("func_type") and meta.get("func_type") != func_type:
            return False
        if crowd_kb and meta.get("target_crowd") and meta.get("target_crowd") != crowd_kb:
            return False
        if bmi_id and meta.get("bmi_id") and meta.get("bmi_id") != bmi_id:
            return False
        return True

    def _ingest_c_result(self, func_type, result, trigger_route: str, **kwargs):
        """把 C 方案（C_direct/C_fallback）的结果自动写入向量知识库。
        优先走四层去重服务（元数据过滤→语义相似度→分级合并→双层存储），
        去重服务不可用时降级为原有逻辑。
        """
        if not self._auto_ingest:
            return
        if not self._retriever or not self._llm:
            return
        if func_type not in ("qa", "diet_plan", "food_recommend", "exercise"):
            return

        # 优先走四层去重服务
        if self._dedup_service:
            try:
                self._dedup_service.check_and_ingest(
                    func_type=func_type,
                    result=result,
                    trigger_route=trigger_route,
                    build_ingest_doc_fn=self._build_ingest_doc,
                    merge_with_cloud_fn=self._merge_with_cloud,
                    **kwargs,
                )
                return
            except Exception as e:
                logger.warning(f"[去重服务异常，降级为原有逻辑] {e}")

        # 降级：原有去重逻辑
        self._ingest_c_result_legacy(func_type, result, trigger_route, **kwargs)

    def _ingest_c_result_legacy(self, func_type, result, trigger_route: str, **kwargs):
        """原有去重入库逻辑（降级兜底）"""
        # 1) 空结果不入库
        if result is None:
            return
        if isinstance(result, str) and len(result.strip()) < 20:
            return
        if isinstance(result, dict) and not result:
            return

        # 2) 查询是否有同主题模板
        query = self._build_match_query(func_type, **kwargs)
        if not query or len(query.strip()) < 3:
            return
        try:
            hits = self._retriever.search(query, top_k=1)
        except Exception as e:
            logger.debug(f"[去重查询失败] {e}")
            hits = []

        top = hits[0] if hits else None

        # 3) 构造新文档 / 或与旧模板整合
        is_dup = False
        if top:
            crowd, _, _, bmi_id, _ = self._extract_crowd_and_goal(func_type, **kwargs)
            kb_crowd = crowd_kb_name(crowd)
            is_dup = (self._is_same_topic(top, func_type, kb_crowd, bmi_id)
                      and top.get("similarity", 0) >= self.DUP_SIMILARITY_THRESHOLD)

        if is_dup:
            old_content = top.get("content", "")
            merged_doc = self._merge_with_cloud(func_type, old_content, result, **kwargs)
            old_meta = dict(top.get("metadata", {}) or {})
            old_meta.update({
                "template_type": "ai_template",
                "func_type": old_meta.get("func_type") or func_type,
                "merged_from": json.dumps([{
                    "reason": "duplicate_topic_merge",
                    "trigger_route": trigger_route,
                    "merge_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "old_similarity": round(float(top.get("similarity", 0)), 3),
                }], ensure_ascii=False),
                "ingest_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": str(float(old_meta.get("version", "1.0") or "1.0") + 0.1),
                "source": old_meta.get("source", "") + f"+merged_with_{trigger_route}",
            })
            old_meta = {k: v for k, v in old_meta.items() if v is not None and str(v) != ""}
            new_id = f"live_merge_{func_type}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            documents, metadatas, ids = [merged_doc], [old_meta], [new_id]
        else:
            doc, meta, cid = self._build_ingest_doc(func_type, result, **kwargs)
            documents, metadatas, ids = [doc], [meta], [cid]

        # 4) 入库
        try:
            self._retriever.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(
                f"[知识库增长] {trigger_route} → {func_type} "
                f"{'[整合]' if documents[0].startswith('【标题】[整合版]') or '[整合版]' in documents[0] else '[新增]'} "
                f"ID={ids[0]}"
            )
        except Exception as e:
            logger.debug(f"[C方案入库失败] {e}")


# 全局单例
mode_router = ModeRouter()
