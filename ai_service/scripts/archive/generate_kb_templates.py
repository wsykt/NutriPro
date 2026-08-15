"""健康知识库模板生成 - 两步流水线（本地 Ollama 初稿 → 云端 DeepSeek 完善 → 入 ChromaDB）

覆盖矩阵（默认 1400 条）：
  人群 × BMI 等级 × 功能 = (6人群+通用=7) × (过低/偏低/正常/偏高/超高=5) × (健康问答/饮食方案/菜谱推荐/运动方案=4)
  每个分类默认生成 10 套模板 → 7×5×4×10 = 1400 条

支持：
  --dry-run              只打印任务清单，不调用模型
  --crowd 普通人          只跑指定人群，可传多个（逗号分隔）
  --bmi normal           只跑指定BMI等级，逗号分隔
  --func qa              只跑指定功能，逗号分隔（qa/diet_plan/food_recommend/exercise）
  --per-group 2          每分类生成模板数，调试用
  --start 0 --end 10     跑任务清单切片（0-based，前闭后开）
  --resume ./checkpoint.json   断点续跑（读取已完成模板ID，跳过）
  --no-ingest            生成完不入库，只落盘JSON
  --ingest-only ./xxx.json      只入库一个已生成的 JSON 文件（不跑模型）
  --workers 4            多进程并行生成（按人群切分；入库在主进程串行，避免并发写）
  --no-cloud             离线模式：跳过云端完善，仅本地草稿入库（省云端Token）

运行示例：
  # 小批量试跑（普通人+正常BMI+健康问答×2条，不落库）
  python generate_kb_templates.py --crowd 普通人 --bmi normal --func qa --per-group 2 --no-ingest

  # 完整跑 1400 条（断点续跑）
  python generate_kb_templates.py --resume ./checkpoint.json

  # 4 进程并行生成 1400 条（每人群任务连续分配给同一 worker）
  python generate_kb_templates.py --workers 4 --resume ./checkpoint.json

  # 离线模式（无云端，仅本地草稿入库）
  python generate_kb_templates.py --crowd 普通人 --no-cloud --no-ingest
"""

import os
import sys
import json
import time
import uuid
import argparse
import logging
from typing import List, Dict, Any

# 确保 health/ai_service 在路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gen_templates")


# ============================================================
# 常量定义
# ============================================================

CROWDS = ["普通人", "孕妇", "健身人群", "老年人", "青少年", "糖尿病患者", "通用"]
CROWD_GROUP_MAP = {
    "普通人": "dietary_guideline",
    "孕妇": "crowd_specific",
    "健身人群": "crowd_specific",
    "老年人": "crowd_specific",
    "青少年": "crowd_specific",
    "糖尿病患者": "crowd_specific",
    "通用": "nutrition_standard",
}

BMI_RANGES = [
    # (id, 中文名, BMI区间, 典型主诉方向)
    ("very_low", "过低", "<18.5", ["增重", "增肌", "改善瘦弱", "提升免疫力", "均衡营养", "增加膳食热量", "改善食欲", "防止低血糖"]),
    ("low", "偏低", "18.5-20", ["适度增重", "增肌减脂", "塑形", "强化营养", "补充蛋白质", "增加肌肉量"]),
    ("normal", "正常", "18.5-24", ["保持健康", "维持体重", "均衡饮食", "规律运动", "慢病预防", "改善体能", "日常保健"]),
    ("high", "偏高", "24-28", ["减脂", "控制体重", "轻断食", "降低体脂", "防止三高", "增加运动", "改善代谢"]),
    ("very_high", "超高", "≥28", ["减肥", "重度减脂", "手术前后营养", "三高管理", "糖尿病风险干预", "低卡高蛋白", "关节友好运动"]),
]

FUNCS = [
    # (id, 中文名, 输出结构, 文档标题前缀)
    ("qa", "健康问答", "str", "问答模板"),
    ("diet_plan", "一日饮食方案", "json_diet", "饮食方案"),
    ("food_recommend", "食材菜谱推荐", "json_food", "菜谱模板"),
    ("exercise", "个性化运动方案", "json_exercise", "运动方案"),
]


# ============================================================
# 任务清单生成
# ============================================================

def build_tasks(crowd_filter=None, bmi_filter=None, func_filter=None, per_group=10):
    """生成 人群×BMI×功能 分类，每类 per_group 条"""
    crowd_ok = lambda c: (crowd_filter is None) or (c in crowd_filter)
    bmi_ok = lambda bid: (bmi_filter is None) or (bid in bmi_filter)
    func_ok = lambda fid: (func_filter is None) or (fid in func_filter)

    tasks = []
    for crowd in CROWDS:
        if not crowd_ok(crowd):
            continue
        for bmi_id, bmi_cn, bmi_range, directions in BMI_RANGES:
            if not bmi_ok(bmi_id):
                continue
            for func_id, func_cn, func_schema, func_title_prefix in FUNCS:
                if not func_ok(func_id):
                    continue
                for i in range(per_group):
                    # 每类按主诉方向轮转，避免重复
                    direction = directions[i % len(directions)]
                    task_id = f"tpl_{crowd}_{bmi_id}_{func_id}_{i:02d}"
                    tasks.append({
                        "task_id": task_id,
                        "crowd": crowd,
                        "bmi_id": bmi_id,
                        "bmi_cn": bmi_cn,
                        "bmi_range": bmi_range,
                        "func_id": func_id,
                        "func_cn": func_cn,
                        "func_schema": func_schema,
                        "func_title_prefix": func_title_prefix,
                        "direction": direction,
                        "seed_index": i,
                    })
    return tasks


# ============================================================
# 各功能的 Prompt 模板（本地 Ollama 生成初稿时用）
# ============================================================

def _user_profile(crowd: str, bmi_range: str) -> str:
    """构造一个代表性的 user_profile 字符串"""
    profile_templates = {
        "普通人": f"30岁上班族，BMI范围{bmi_range}，无慢病，日常轻体力活动",
        "孕妇": f"28岁孕妇，孕中期，BMI范围{bmi_range}，血压正常，产检无异常",
        "健身人群": f"25岁健身爱好者，BMI范围{bmi_range}，每周力量训练4次，目标增肌",
        "老年人": f"68岁退休老人，BMI范围{bmi_range}，高血压控制良好，日常活动一般",
        "青少年": f"15岁中学生，BMI范围{bmi_range}，学业繁忙，每天课间运动不足",
        "糖尿病患者": f"55岁2型糖尿病患者，BMI范围{bmi_range}，HbA1c 7.2%，口服降糖药",
        "通用": f"35岁成人，BMI范围{bmi_range}，希望通过生活方式改善健康状态",
    }
    return profile_templates.get(crowd, profile_templates["通用"])


def build_local_prompt(task: Dict[str, Any]) -> List[Dict[str, str]]:
    """本地 Ollama 初稿 prompt：按功能生成 1 套完整模板（question + answer）"""
    crowd = task["crowd"]
    bmi_cn = task["bmi_cn"]
    bmi_range = task["bmi_range"]
    direction = task["direction"]
    seed = task["seed_index"]
    user_profile_str = _user_profile(crowd, bmi_range)

    # --- qa（健康问答） ---
    if task["func_id"] == "qa":
        system = (
            "你是健康科普内容生成助手。请基于人群+BMI情况+主诉方向，"
            "生成1套典型用户健康问答（1个问题，1个科学回答）。回答结构清晰，分点说明，"
            "200-400字。核心结论（如推荐摄入量、安全阈值、禁忌事项）须保留原文表述，不做模糊改写。"
            "结尾必须附带："
            "「温馨提示：本内容仅供膳食科普参考，不构成医疗建议，慢性病请遵从执业医师指导。」"
        )
        user = (
            f"【目标人群】：{crowd}（BMI{bmi_cn}，范围{bmi_range}）\n"
            f"【主诉方向】：{direction}\n"
            f"【参考用户画像】：{user_profile_str}\n"
            f"【随机编号】：{seed}\n\n"
            "请严格输出合法JSON（不要额外文字），字段：\n"
            "{\n"
            '  "question": "具体的用户问题",\n'
            '  "answer": "完整的科普回答"\n'
            "}\n"
            "要求：问题要具体真实（如『我BMI24.5属于超重，平时上班久坐，如何在不饿肚子的情况下减脂？』）；"
            "回答要给出科学、可执行的具体建议。"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    # --- diet_plan（一日饮食方案） ---
    if task["func_id"] == "diet_plan":
        system = (
            "你是个性化膳食方案专家。请基于人群、BMI和健康目标，生成科学合理的一日三餐方案。"
            "只输出纯JSON，不要任何markdown或解释。"
        )
        user = (
            f"【用户人群】：{crowd}\n"
            f"【BMI】：{bmi_cn}（范围{bmi_range}）\n"
            f"【健康目标/主诉】：{direction}\n"
            f"【参考画像】：{user_profile_str}\n"
            f"【随机编号】：{seed}\n\n"
            "严格按以下JSON结构输出：\n"
            "{\n"
            '  "goal": "用户目标（如减脂/增肌/控糖）",\n'
            '  "total_calories": 整数kcal,\n'
            '  "daily_plan": {\n'
            '    "早餐": [{"food": "食材名","portion": "份量如80克/1个/250毫升"}],\n'
            '    "午餐": [{"food": "食材名","portion": "份量"}],\n'
            '    "晚餐": [{"food": "食材名","portion": "份量"}],\n'
            '    "加餐": [{"food": "食材名","portion": "份量"}]\n'
            "  },\n"
            '  "nutrition_breakdown": {"protein": 整数g, "carbohydrate": 整数g, "fat": 整数g},\n'
            '  "tips": ["建议1","建议2","建议3"],\n'
            '  "avoided_foods": ["需要避免或减少的食材"],\n'
            '  "replaced_foods": [{"from": "常见不健康食材","to": "健康替换方案"}]\n'
            "}\n"
            "热量参考：成人女性1500-2100kcal/天，男性1800-2800kcal/天；"
            "减脂人群-300~500kcal，增肌人群+300~500kcal。"
            "孕妇额外+200~450kcal（孕中晚期），糖尿病患者注意低GI。"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    # --- food_recommend（食材菜谱推荐） ---
    if task["func_id"] == "food_recommend":
        system = (
            "你是营养膳食菜谱生成专家。请为指定人群、BMI、目标设计3道菜谱（早/午/晚各1道），"
            "使用常见、易得的食材。只输出纯JSON。"
        )
        user = (
            f"【目标人群】：{crowd}\n"
            f"【BMI】：{bmi_cn}（{bmi_range}）\n"
            f"【目标】：{direction}\n"
            f"【参考画像】：{user_profile_str}\n"
            f"【随机编号】：{seed}\n\n"
            "请为该用户设计一天3道适合的菜谱，严格以下JSON格式：\n"
            "{\n"
            '  "total_meals": 3,\n'
            '  "meal_plan": [\n'
            '    {"meal_type": "早餐","name": "菜名","ingredients": [{"name":"食材名","amount":"用量"}],\n'
            '     "cook_method": "1-2句话简易做法","calories_estimate": 整数kcal,\n'
            '     "protein_estimate": 整数g, "tags": ["快手","低脂","高蛋白"等]},\n'
            '    {"meal_type": "午餐", ...同上},\n'
            '    {"meal_type": "晚餐", ...同上}\n'
            "  ],\n"
            '  "total_calories": 整数kcal（3餐合计）,\n'
            '  "total_protein": 整数g,\n'
            '  "tips": ["备餐建议1","替代方案建议1"],\n'
            '  "missing_ingredients": ["建议额外补充的食材/调味品"]\n'
            "}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    # --- exercise（个性化运动方案） ---
    if task["func_id"] == "exercise":
        system = (
            "你是运动健康指导专家。请基于人群、BMI、健康目标生成安全科学的一周运动方案。"
            "只输出纯JSON。慢病患者必须加安全注意事项。"
        )
        user = (
            f"【用户人群】：{crowd}\n"
            f"【BMI】：{bmi_cn}（{bmi_range}）\n"
            f"【运动目标】：{direction}\n"
            f"【参考画像】：{user_profile_str}\n"
            f"【随机编号】：{seed}\n\n"
            "严格以下JSON格式（一周5-7天运动，总时长WHO建议150-300分钟之间）：\n"
            "{\n"
            '  "goal": "用户目标原文",\n'
            '  "weekly_schedule": [\n'
            '    {"day": "周一","exercise_type": "如快走/力量训练/瑜伽","duration": "整数分钟",\n'
            '     "intensity": "低/中/高","description": "详细动作说明和组数",\n'
            '     "calories_burn_estimate": 整数kcal}\n'
            "  ],\n"
            '  "weekly_total_minutes": 整数分钟（150-300）,\n'
            '  "weekly_total_calories": 整数kcal,\n'
            '  "warm_up": "热身建议（5-10分钟）",\n'
            '  "cool_down": "拉伸放松建议（5-10分钟）",\n'
            '  "precautions": ["安全注意事项1","安全注意事项2，慢病患者必须有"],\n'
            '  "progression_plan": "4周进阶计划说明（如每2周+5%强度）"\n'
            "}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    return []


# ============================================================
# 云端 DeepSeek 完善 prompt
# ============================================================

def build_cloud_polish_prompt(task: Dict[str, Any], draft_content: Any) -> List[Dict[str, str]]:
    """云端完善：在本地初稿基础上提升专业性、数值合理性、人群适配性"""
    func_id = task["func_id"]
    draft_str = json.dumps(draft_content, ensure_ascii=False, indent=2)

    base_user = (
        f"【功能类型】：{task['func_cn']} ({func_id})\n"
        f"【人群】：{task['crowd']}，BMI {task['bmi_cn']} ({task['bmi_range']})\n"
        f"【主诉方向】：{task['direction']}\n"
        f"【参考画像】：{_user_profile(task['crowd'], task['bmi_range'])}\n\n"
        f"【本地模型初稿】：\n{draft_str}\n\n"
    )

    if func_id == "qa":
        return [
            {"role": "system", "content": (
                "你是权威健康科普编审。请对以下健康问答初稿进行专业完善："
                "1) 科学性核查：补充最新中国居民膳食指南/慢病指南的依据要点；"
                "2) 实用性：增加具体执行建议（如具体克数、频率、替代方案）；"
                "3) 针对人群和BMI的专属建议；"
                "4) 扩充到400-600字（目标约500字）；"
                "5) 核心结论（推荐摄入量、安全阈值、禁忌事项等数据性/结论性语句）须保留原文表述，"
                "不做模糊改写或意译，降低下游大模型二次推断的歧义风险；"
                "6) 必须保留结尾的合规免责声明。"
                "输出与输入相同的JSON结构（question + answer）。"
            )},
            {"role": "user", "content": base_user + "请完善后输出同样的JSON结构。"},
        ]

    if func_id == "diet_plan":
        return [
            {"role": "system", "content": (
                "你是临床营养编审专家。请审核并完善这份一日膳食方案："
                "1) 核查总热量合理性（成人BMR基础上±缺口/盈余）；"
                "2) 核查蛋白质（0.8-2.0g/kg体重）、碳水(50-65%)、脂肪(20-30%)供能比；"
                "3) 人群专属：孕妇补充叶酸/DHA/钙铁；老年人增加细软易消化+VD钙；糖尿病低GI；健身高蛋；青少年满足生长；"
                "4) 餐次和食材搭配是否符合中国居民膳食宝塔；"
                "5) tips补充人群专属烹饪建议和注意事项；"
                "6) 对BMI极高/极低的人群给出安全边界说明。"
                "输出与输入完全相同的JSON结构。"
            )},
            {"role": "user", "content": base_user + "请完善后输出同样的JSON结构，不要额外文字。"},
        ]

    if func_id == "food_recommend":
        return [
            {"role": "system", "content": (
                "你是中国注册营养师。请完善这份一日3餐菜谱："
                "1) 核查每餐、全日热量和蛋白质克数；"
                "2) cook_method 扩充为步骤化、可执行（2-4步，写明火候/时间）；"
                "3) 食材量细化为中国家庭常用的g/ml/个/勺；"
                "4) tags至少3个标签（如控糖/低脂/高蛋白/快手/家常/软食/适合老年人等）；"
                "5) 人群专属：孕妇避免生冷+增补食材；老人细软；糖尿低GI；健身增肌加大蛋白；"
                "6) 营养替代方案：如果用户买不到某种食材怎么办。"
                "输出与输入完全相同的JSON结构。"
            )},
            {"role": "user", "content": base_user + "请完善后输出同样的JSON结构。"},
        ]

    if func_id == "exercise":
        return [
            {"role": "system", "content": (
                "你是运动医学编审。请审核完善一周运动方案："
                "1) 核查总时长150-300分钟（WHO上限）；"
                "2) 慢病/超高BMI人群：避免高强度，强调关节友好（游泳/快走/坐姿）、心率区间、暂停信号；"
                "3) 老年人：增加平衡训练+防跌倒提示；"
                "4) 孕妇：只做孕中期安全运动（散步/游泳/凯格尔），禁止仰卧/跳跃/屏气；"
                "5) 青少年：结合骨骼发育的弹跳+日常课间活动；"
                "6) 健身人群：分化训练组数次数细化；"
                "7) progression_plan 给出4周清晰进阶节奏（时长/强度/频率）。"
                "输出与输入完全相同的JSON结构。"
            )},
            {"role": "user", "content": base_user + "请完善后输出同样的JSON结构。"},
        ]

    return []


# ============================================================
# 模型调用封装
# ============================================================

def _force_mode(llm, mode: str):
    """临时切换 LLMRouter 到指定模式（local/cloud），返回还原函数"""
    original = llm._mode
    llm._mode = mode

    def restore():
        llm._mode = original

    return restore


def call_local_draft(llm, task: Dict[str, Any]) -> Any:
    """本地 Ollama 生成初稿，返回结构化内容（qa是{q,a}；其他是dict）"""
    restore = _force_mode(llm, "local")
    try:
        msgs = build_local_prompt(task)
        # 先调一次 chat，拿到原始文本打印调试，再走一次 safe_parse_json
        raw_text = llm.chat(msgs)
        logger.info(f"[本地草稿] 原始输出({task['task_id']})前400字符: {raw_text[:400]}")
        if not raw_text:
            logger.warning(f"[本地草稿] {task['task_id']} 返回空文本")
            return {} if task["func_id"] != "qa" else {"question": "", "answer": ""}
        parsed = llm.safe_parse_json(raw_text)
        if not parsed:
            logger.warning(f"[本地草稿] {task['task_id']} JSON解析失败，原始输出后150字符: ...{raw_text[-150:]}")
        if task["func_id"] == "qa":
            return parsed or {"question": "", "answer": ""}
        return parsed or {}
    except Exception as e:
        logger.warning(f"[本地草稿] {task['task_id']} 失败: {e}")
        return {} if task["func_id"] != "qa" else {"question": "", "answer": ""}
    finally:
        restore()


def call_cloud_polish(llm, task: Dict[str, Any], draft: Any) -> Any:
    """云端 DeepSeek 完善初稿"""
    restore = _force_mode(llm, "cloud")
    try:
        msgs = build_cloud_polish_prompt(task, draft)
        if task["func_id"] == "qa":
            return llm.chat_json(msgs, max_retries=2) or draft
        else:
            return llm.chat_json(msgs, max_retries=2) or draft
    except Exception as e:
        logger.warning(f"[云端完善] {task['task_id']} 失败，退回草稿: {e}")
        return draft
    finally:
        restore()


# ============================================================
# 入库：文档+metadata 构造（对齐 import_cards_to_chromadb.py）
# ============================================================

def build_document_and_metadata(final: Dict[str, Any], task: Dict[str, Any]) -> (str, Dict[str, Any], str):
    """把最终模板转成 ChromaDB 文档+元数据+唯一ID"""
    func_id = task["func_id"]
    func_cn = task["func_cn"]
    crowd = task["crowd"]
    bmi_cn = task["bmi_cn"]
    direction = task["direction"]
    content = final.get("final_content", {})

    # ---- 标题和正文文本（用于向量编码和检索命中） ----
    if func_id == "qa":
        q = content.get("question", "")
        a = content.get("answer", "")
        title = f"{task['func_title_prefix']}｜{crowd}｜BMI{bmi_cn}｜{direction}｜{q[:20]}"
        purified = f"【用户问题】{q}\n\n【专业回答】\n{a}"
    elif func_id == "diet_plan":
        goal = content.get("goal", direction)
        cal = content.get("total_calories", "")
        title = f"{task['func_title_prefix']}｜{crowd}｜BMI{bmi_cn}｜{direction}｜{cal}kcal"
        purified = (
            f"【目标】{goal}（每日总热量 {cal}kcal）\n\n"
            f"【一日膳食方案】\n{json.dumps(content.get('daily_plan', {}), ensure_ascii=False, indent=2)}\n\n"
            f"【三大营养素】{json.dumps(content.get('nutrition_breakdown', {}), ensure_ascii=False)}\n\n"
            f"【人群专属建议】\n" + "\n".join(f"- {t}" for t in content.get("tips", [])) + "\n\n"
            f"【禁忌食材】{json.dumps(content.get('avoided_foods', []), ensure_ascii=False)}\n"
            f"【替换方案】{json.dumps(content.get('replaced_foods', []), ensure_ascii=False)}"
        )
    elif func_id == "food_recommend":
        title = f"{task['func_title_prefix']}｜{crowd}｜BMI{bmi_cn}｜{direction}"
        meals = content.get("meal_plan", [])
        lines = []
        for m in meals:
            lines.append(
                f"【{m.get('meal_type','')}】{m.get('name','')}\n"
                f"  食材：{json.dumps(m.get('ingredients', []), ensure_ascii=False)}\n"
                f"  做法：{m.get('cook_method','')}\n"
                f"  热量{m.get('calories_estimate','')}kcal，蛋白质{m.get('protein_estimate','')}g，标签：{json.dumps(m.get('tags', []), ensure_ascii=False)}"
            )
        purified = (
            f"【全日总览】总热量{content.get('total_calories','')}kcal，蛋白质{content.get('total_protein','')}g\n\n"
            + "\n\n".join(lines) + "\n\n"
            + f"【备餐与替代建议】\n" + "\n".join(f"- {t}" for t in content.get("tips", [])) + "\n"
            + f"【建议补充】{json.dumps(content.get('missing_ingredients', []), ensure_ascii=False)}"
        )
    else:  # exercise
        title = f"{task['func_title_prefix']}｜{crowd}｜BMI{bmi_cn}｜{direction}"
        sched = content.get("weekly_schedule", [])
        day_lines = []
        for d in sched:
            day_lines.append(
                f"【{d.get('day','')}】{d.get('exercise_type','')}｜{d.get('duration','')}分钟｜强度{d.get('intensity','')}｜消耗{d.get('calories_burn_estimate','')}kcal\n"
                f"  动作说明：{d.get('description','')}"
            )
        purified = (
            f"【目标】{content.get('goal','')}\n"
            f"【本周总量】{content.get('weekly_total_minutes','')}分钟，约消耗{content.get('weekly_total_calories','')}kcal\n\n"
            + "\n\n".join(day_lines) + "\n\n"
            + f"【热身】{content.get('warm_up','')}\n【放松】{content.get('cool_down','')}\n\n"
            + f"【安全注意事项】\n" + "\n".join(f"- {p}" for p in content.get("precautions", [])) + "\n\n"
            + f"【4周进阶计划】{content.get('progression_plan','')}"
        )

    document = f"【标题】{title}\n{purified}"
    card_id = f"tpl_{task['crowd']}_{task['bmi_id']}_{task['func_id']}_{task['seed_index']:02d}_{uuid.uuid4().hex[:8]}"

    category = CROWD_GROUP_MAP.get(crowd, "nutrition_standard")
    metadata = {
        # 核心分类标签（用户新要求的4要素）
        "template_type": "ai_template",
        "func_type": func_id,           # qa / diet_plan / food_recommend / exercise
        "func_cn": func_cn,
        "target_crowd": crowd,
        "crowd": crowd,
        "group": crowd,
        "bmi_id": task["bmi_id"],
        "bmi_cn": bmi_cn,
        "bmi_range": task["bmi_range"],
        "direction": direction,

        # 兼容原有字段（import_cards_to_chromadb.py 里的字段）
        "category": category,
        "source": f"系统生成_模板库_{func_cn}",
        "topic": f"{crowd}-BMI{bmi_cn}-{direction}",
        "source_channel": "ai_template_generator_v1",
        "source_type": "vector_kb",
        "is_official_guide": "False",
        "version": "1.0",
        "ingest_time": time.strftime("%Y-%m-%d %H:%M:%S"),

        # 模板索引信息
        "card_id": card_id,
        "seed_index": str(task["seed_index"]),
    }
    # 剔除空值（ChromaDB 不支持 None/""）
    metadata = {k: v for k, v in metadata.items() if v is not None and str(v) != ""}
    return document, metadata, card_id


def ingest_to_chroma(retriever, documents: List[str], metadatas: List[Dict], ids: List[str],
                     batch_size=1, checkpoint_path: str = None, completed_ids: set = None):
    """逐条或小批量入库，外层try/except+checkpoint续跑（用户要求：一条一条塞进去更稳）"""
    if not documents:
        return 0
    total = 0
    failed = []
    ckpt = {"completed_ids": list(completed_ids) if completed_ids else [], "failed_ids": []}

    def _flush():
        if checkpoint_path:
            tmp = checkpoint_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as _f:
                json.dump(ckpt, _f, ensure_ascii=False, indent=2)
            os.replace(tmp, checkpoint_path)

    done = set(completed_ids) if completed_ids else set()
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_metas = metadatas[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        # 跳过已完成
        todo_idx = [j for j in range(len(batch_ids)) if batch_ids[j] not in done]
        if not todo_idx:
            total += len(batch_ids)
            continue
        bd = [batch_docs[j] for j in todo_idx]
        bm = [batch_metas[j] for j in todo_idx]
        bi = [batch_ids[j] for j in todo_idx]
        try:
            # 单条模式=逐条add，错误隔离到具体单条
            if batch_size == 1:
                for d, m, id_ in zip(bd, bm, bi):
                    try:
                        retriever.add(documents=[d], metadatas=[m], ids=[id_])
                        done.add(id_)
                        total += 1
                        ckpt["completed_ids"].append(id_)
                    except Exception as _e:
                        failed.append((id_, str(_e)))
                        ckpt.setdefault("failed_ids", []).append({"id": id_, "error": str(_e)[:500]})
                        logger.warning(f"  [FAIL] {id_}: {_e}")
                if (total % 10 == 0 or i == len(documents) - batch_size):
                    _flush()
            else:
                retriever.add(documents=bd, metadatas=bm, ids=bi)
                for id_ in bi:
                    done.add(id_)
                    ckpt["completed_ids"].append(id_)
                total += len(bi)
                _flush()
        except Exception as e:
            logger.error(f"  [BATCH FAIL] batch@{i}: {e}")
            # 回退到逐条塞
            if batch_size > 1:
                logger.info("  -> 回退到逐条模式重试本批次")
                for d, m, id_ in zip(bd, bm, bi):
                    if id_ in done:
                        continue
                    try:
                        retriever.add(documents=[d], metadatas=[m], ids=[id_])
                        done.add(id_)
                        total += 1
                        ckpt["completed_ids"].append(id_)
                    except Exception as e2:
                        failed.append((id_, str(e2)))
                        ckpt.setdefault("failed_ids", []).append({"id": id_, "error": str(e2)[:500]})
                        logger.warning(f"    [FAIL] {id_}: {e2}")
                _flush()
            else:
                pass
        pct = round(total / len(documents) * 100, 1)
        logger.info(f"  进度 {total}/{len(documents)} ({pct}%)  失败 {len(failed)}")
    _flush()
    if failed:
        logger.warning(f"入库完成，成功 {total} 失败 {len(failed)}：{failed[:5]}")
    return total


# ============================================================
# 单任务处理（供多进程 worker 调用，模块级函数保证可 pickle）
# ============================================================

def _process_one_task_worker(task: Dict[str, Any]) -> Dict[str, Any]:
    """多进程 worker：独立初始化 LLM，处理单个任务（只生成，不入库）。
    返回 record dict；失败时返回包含空 draft 的 record，便于统一统计。"""
    from llm.router import llm
    draft = call_local_draft(llm, task)
    empty_qa = (task["func_id"] == "qa" and not (draft.get("question") and draft.get("answer")))
    empty_json = (task["func_id"] != "qa" and not draft)
    if empty_qa or empty_json:
        final_content = draft
        polished_by = "local_only_fallback"
    else:
        final_content = call_cloud_polish(llm, task, draft)
        polished_by = "cloud_polished"
    return {
        "task": task,
        "task_id": task["task_id"],
        "local_draft": draft,
        "final_content": final_content,
        "polished_by": polished_by,
        "generate_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def _build_ingest_payload(record: Dict[str, Any]) -> tuple:
    """由 record 构建入库 payload（文档/元数据/ID），与生成模式共用"""
    doc, meta, cid = build_document_and_metadata(record, record["task"])
    record["_chroma_id"] = cid
    return doc, meta, cid


# ============================================================
# 断点续跑（JSON checkpoint）
# ============================================================

def load_checkpoint(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_task_ids": [], "templates": []}


def save_checkpoint(path: str, ckpt: Dict[str, Any]):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


# ============================================================
# 主流水线
# ============================================================

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--crowd", default=None, help="逗号分隔人群名")
    p.add_argument("--bmi", default=None, help="逗号分隔BMI id: very_low/low/normal/high/very_high")
    p.add_argument("--func", default=None, help="逗号分隔: qa/diet_plan/food_recommend/exercise")
    p.add_argument("--per-group", type=int, default=10)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=None)
    p.add_argument("--resume", default=None)
    p.add_argument("--no-ingest", action="store_true")
    p.add_argument("--ingest-only", default=None, help="只入库指定JSON")
    p.add_argument("--ingest-batch-size", type=int, default=1, help="入库批大小，默认1即逐条入库")
    p.add_argument("--ingest-resume", default=None, help="逐条入库断点续跑ckp路径")
    p.add_argument("--checkpoint", default="checkpoint_templates.json")
    p.add_argument("--output", default="kb_templates_output.json")
    p.add_argument("--workers", type=int, default=1,
                   help="并行进程数（>1 时按人群切分任务到多进程生成，入库在主进程串行）")
    p.add_argument("--no-cloud", action="store_true",
                   help="跳过云端完善，仅本地草稿直接入库（离线模式/省云端Token）")
    return p.parse_args()


def main():
    args = parse_args()

    # ---- 入库-only 模式（不再跑模型） ----
    if args.ingest_only:
        logger.info(f"[仅入库模式] 读取 {args.ingest_only}")
        with open(args.ingest_only, "r", encoding="utf-8") as f:
            data = json.load(f)
        templates = data.get("templates", data) if isinstance(data, dict) else data
        from vector.retriever import retriever as r
        docs, metas, ids = [], [], []
        for t in templates:
            doc, meta, cid = build_document_and_metadata(t, t["task"])
            docs.append(doc); metas.append(meta); ids.append(cid)
        completed_ids = set()
        ingest_ckp_path = args.ingest_resume or os.path.splitext(args.ingest_only)[0] + "_ingest_ckp.json"
        if args.ingest_resume and os.path.exists(args.ingest_resume):
            with open(args.ingest_resume, "r", encoding="utf-8") as _f:
                _d = json.load(_f)
            completed_ids = set(_d.get("completed_ids", []))
            logger.info(f"  入库断点续跑，已完成 {len(completed_ids)} 条")
        logger.info(f"  共 {len(docs)} 条准备入库，batch_size={args.ingest_batch_size}（逐条={args.ingest_batch_size==1}）")
        n = ingest_to_chroma(r, docs, metas, ids,
                             batch_size=args.ingest_batch_size,
                             checkpoint_path=ingest_ckp_path,
                             completed_ids=completed_ids)
        logger.info(f"[入库完成] 成功 {n} 条，当前ChromaDB总数：{r.count()}")
        return

    # ---- 生成模式 ----
    crowd_filter = set(args.crowd.split(",")) if args.crowd else None
    bmi_filter = set(args.bmi.split(",")) if args.bmi else None
    func_filter = set(args.func.split(",")) if args.func else None

    tasks = build_tasks(crowd_filter, bmi_filter, func_filter, args.per_group)
    end_idx = args.end if args.end is not None else len(tasks)
    tasks = tasks[args.start:end_idx]
    logger.info(f"[任务清单] {len(tasks)} 条（{args.start}:{end_idx}）")
    if args.dry_run:
        for t in tasks[:20]:
            print(f"  {t['task_id']}  {t['crowd']:6s} BMI-{t['bmi_cn']:3s} {t['func_cn']:10s} 方向:{t['direction']}")
        if len(tasks) > 20:
            print(f"  ... 共{len(tasks)}条，省略其余")
        return

    # 断点续跑
    ckpt_path = args.resume or args.checkpoint
    ckpt = load_checkpoint(ckpt_path)
    completed = set(ckpt.get("completed_task_ids", []))
    logger.info(f"[断点续跑] checkpoint中已完成 {len(completed)} 条")

    # 延迟 import 模型（避免 dry-run 时加载 embedding）
    from llm.router import llm
    # ChromaDB 只有在要真正入库时才 import，--no-ingest 不需要加载 embedding 模型
    retriever = None
    if not args.no_ingest:
        from vector.retriever import retriever as _rv
        retriever = _rv

    logger.info(f"LLM 初始模式: {llm._mode}")
    if retriever is not None:
        logger.info(f"ChromaDB 当前记录数: {retriever.count()}")
    else:
        logger.info("ChromaDB: 跳过（--no-ingest）")

    docs_list, metas_list, ids_list = [], [], []

    # ---- 多进程模式：按人群切分任务到 N 个 worker，生成阶段并行 ----
    if args.workers > 1 and not args.no_ingest:
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor

        todo_tasks = [t for t in tasks if t["task_id"] not in completed]
        done_ids = set(completed)
        logger.info(f"[多进程] workers={args.workers}，待处理 {len(todo_tasks)} 条，按人群切分")

        # 按人群分组，保证同一人群任务连续分配给同一 worker（减少 Ollama 模型切换开销）
        todo_by_crowd = {}
        for t in todo_tasks:
            todo_by_crowd.setdefault(t["crowd"], []).append(t)
        crowd_chunks = list(todo_by_crowd.values())
        # 把人群块均衡地分给 workers（大块优先）
        chunks = [[] for _ in range(args.workers)]
        for i, chunk in enumerate(sorted(crowd_chunks, key=len, reverse=True)):
            target = i % args.workers
            chunks[target].extend(chunk)

        mp.set_start_method("spawn", force=True)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = []
            for w_idx, chunk in enumerate(chunks):
                for t in chunk:
                    futures.append((t["task_id"], pool.submit(_process_one_task_worker, t)))
            for tid, fut in futures:
                try:
                    record = fut.result()
                except Exception as e:
                    logger.error(f"[worker] 任务 {tid} 异常: {e}")
                    record = None
                if record is None:
                    continue
                ckpt.setdefault("templates", []).append(record)
                ckpt.setdefault("completed_task_ids", []).append(tid)
                done_ids.add(tid)
                doc, meta, cid = _build_ingest_payload(record)
                docs_list.append(doc); metas_list.append(meta); ids_list.append(cid)
                # 每 10 条 flush 一次 checkpoint + 入库
                if len(done_ids) % 10 == 0:
                    save_checkpoint(ckpt_path, ckpt)
                    if not args.no_ingest and docs_list:
                        ingest_to_chroma(retriever, docs_list, metas_list, ids_list)
                        docs_list, metas_list, ids_list = [], [], []
        save_checkpoint(ckpt_path, ckpt)
        if not args.no_ingest and docs_list:
            ingest_to_chroma(retriever, docs_list, metas_list, ids_list)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(ckpt, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 多进程完成。输出: {args.output}（{len(ckpt.get('templates', []))}条）")
        if not args.no_ingest:
            logger.info(f"   ChromaDB 总数: {retriever.count()}")
        return

    for idx, task in enumerate(tasks):
        tid = task["task_id"]
        if tid in completed:
            logger.info(f"[{idx+1}/{len(tasks)}] 跳过(已完成): {tid}")
            continue

        logger.info(f"[{idx+1}/{len(tasks)}] 执行 {tid} | {task['crowd']} BMI-{task['bmi_cn']} {task['func_cn']} 方向:{task['direction']}")

        # Step1: 本地草稿
        draft = call_local_draft(llm, task)
        # 如果本地输出完全空（失败），直接跳过云端完善（但仍保存空模板供后续补）
        empty_qa = (task["func_id"] == "qa" and not (draft.get("question") and draft.get("answer")))
        empty_json = (task["func_id"] != "qa" and not draft)
        if empty_qa or empty_json:
            logger.warning(f"  本地草稿为空，跳过云端，使用空模板占位")

        # Step2: 云端完善（草稿不为空且未禁用云端才调用）
        if empty_qa or empty_json:
            final_content = draft
            polished_by = "local_only_fallback"
        elif args.no_cloud:
            final_content = draft
            polished_by = "local_only_no_cloud"
            logger.info(f"  跳过云端完善（--no-cloud 离线模式）")
        else:
            final_content = call_cloud_polish(llm, task, draft)
            polished_by = "cloud_polished"

        record = {
            "task": task,
            "task_id": tid,
            "local_draft": draft,
            "final_content": final_content,
            "polished_by": polished_by,
            "generate_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        ckpt.setdefault("templates", []).append(record)
        ckpt.setdefault("completed_task_ids", []).append(tid)

        # 准备入库数据
        doc, meta, cid = build_document_and_metadata(record, task)
        record["_chroma_id"] = cid
        docs_list.append(doc)
        metas_list.append(meta)
        ids_list.append(cid)

        # 每10条保存一次 checkpoint 并批量入库
        if (idx + 1) % 10 == 0:
            save_checkpoint(ckpt_path, ckpt)
            if not args.no_ingest:
                ingest_to_chroma(retriever, docs_list, metas_list, ids_list)
                docs_list, metas_list, ids_list = [], [], []

    # 尾处理
    save_checkpoint(ckpt_path, ckpt)
    if not args.no_ingest and docs_list:
        ingest_to_chroma(retriever, docs_list, metas_list, ids_list)

    # 最终输出 JSON
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 完成。输出: {args.output}（{len(ckpt.get('templates', []))}条）")
    if not args.no_ingest:
        logger.info(f"   ChromaDB 总数: {retriever.count()}")


if __name__ == "__main__":
    main()
