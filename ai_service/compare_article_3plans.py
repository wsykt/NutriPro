# -*- coding: utf-8 -*-
"""
科普文章母稿生成：三方案对比测试
================================
方案A（纯本地）：本地Ollama生成完整母稿（Stage1本地 + Stage3本地校验）
方案B（混合）：本地Ollama搭框架 → 云端DeepSeek外扩 → 本地校验
方案C（纯云端）：云端DeepSeek直接生成完整母稿（Stage1云端 + Stage3云端）

对比维度：总耗时、云端token消耗、本地调用次数、文章字数、15标签完整性

用法：
    python compare_article_3plans.py                 # 跑全部三方案
    python compare_article_3plans.py --plan A        # 只跑方案A
    python compare_article_3plans.py --plan B        # 只跑方案B
    python compare_article_3plans.py --plan C        # 只跑方案C
    python compare_article_3plans.py --report        # 生成对比报告
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime
from collections import OrderedDict

AI_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_DIR)

from pipeline_v32 import (
    retrieve_from_kb, stage1_build_framework, stage2_expand,
    stage3_validate, build_mother_format,
    SYSTEM_STAGE1, SYSTEM_STAGE2, SYSTEM_STAGE3,
    call_ollama, call_cloud,
)

OUTPUT_DIR = os.path.join(AI_DIR, "test_output", "article_3plans")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 测试主题（已有知识库数据，含细分人群）
TEST_PERSONA = "青少年"
TEST_TOPIC = "青少年饮食营养"
# 知识库检索用中文（ChromaDB中文文档）
TEST_QUERY = "青少年饮食营养 钙铁锌 生长发育"
# PubMed联网搜索用英文（PubMed是英文数据库，中文关键词搜不到结果）
TEST_PUBMED_QUERY = "adolescent nutrition calcium iron zinc growth development"

# 15 个母稿标签
REQUIRED_TAGS = [
    "【#META#】", "【#ALL_INTRO#】", "【#SUMMARY_FAST#】", "【#SUMMARY_DEEP#】",
    "【#SUMMARY_ALL#】", "【#COMMON_BEGIN#】", "【#COMMON_END#】",
    "【#DEEP_PLUS_BEGIN#】", "【#DEEP_PLUS_END#】",
    "【#DEBATE_ZONE_BEGIN#】", "【#DEBATE_ZONE_END#】",
    "【#CONCLUDE_FAST#】", "【#CONCLUDE_DEEP#】", "【#CONCLUDE_ALL#】",
    "【#REF_LIST#】"
]


# ============================================================
# Token 追踪器（分本地/云端，输入/输出）
# ============================================================
class PlanTokenTracker:
    """分来源 Token 追踪"""
    def __init__(self):
        self.local_calls = 0
        self.cloud_calls = 0
        self.local_tokens_est = 0      # 本地估算（字符数//3）
        self.cloud_prompt_tokens = 0   # 云端输入token
        self.cloud_completion_tokens = 0  # 云端输出token
        self.cloud_total_tokens = 0
        self.timings = []  # [(stage, elapsed_seconds), ...]

    def record_local(self, content):
        self.local_calls += 1
        # Ollama不返回token统计，用字符数估算
        est = len(content) // 3
        self.local_tokens_est += est

    def record_cloud(self, usage: dict):
        self.cloud_calls += 1
        pt = usage.get("prompt_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        self.cloud_prompt_tokens += pt
        self.cloud_completion_tokens += ct
        self.cloud_total_tokens += pt + ct

    def add_timing(self, stage: str, elapsed: float):
        self.timings.append((stage, elapsed))

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
            "total_elapsed": round(self.total_elapsed, 2),
            "timings": [(s, round(t, 2)) for s, t in self.timings],
        }


# ============================================================
# 包装调用：捕获 token 用量
# ============================================================
def call_ollama_tracked(prompt, system, tracker: PlanTokenTracker, label, temp=0.3, max_tokens=2500):
    """本地Ollama调用 + token追踪"""
    import requests
    from config.settings import settings
    start = time.time()
    try:
        resp = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": temp,
                    "num_ctx": settings.OLLAMA_NUM_CTX,
                    "num_predict": max_tokens,
                },
            },
            timeout=settings.OLLAMA_TIMEOUT,
        )
        elapsed = time.time() - start
        if resp.status_code != 200:
            print(f"    ✗ [{label}] Ollama HTTP {resp.status_code}: {resp.text[:200]}")
            tracker.add_timing(label, elapsed)
            return None
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        tracker.record_local(content)
        tracker.add_timing(label, elapsed)
        print(f"    ✓ [{label}] 本地 {elapsed:.1f}s | {len(content)}字")
        return content
    except Exception as e:
        elapsed = time.time() - start
        tracker.add_timing(label, elapsed)
        print(f"    ✗ [{label}] Ollama失败: {e}")
        return None


def call_cloud_tracked(prompt, system, tracker: PlanTokenTracker, label, temp=0.7, max_tokens=3000):
    """云端DeepSeek调用 + token追踪（精确usage）"""
    import requests
    from config.settings import settings
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }
    start = time.time()
    for attempt in range(3):
        try:
            resp = requests.post(
                f"{settings.DEEPSEEK_API_BASE}/chat/completions",
                headers=headers, json=payload, timeout=180,
            )
            elapsed = time.time() - start
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tracker.record_cloud(usage)
            tracker.add_timing(label, elapsed)
            print(f"    ✓ [{label}] 云端 {elapsed:.1f}s | {len(content)}字 | "
                  f"tokens: in={usage.get('prompt_tokens',0)} out={usage.get('completion_tokens',0)}")
            return content
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                elapsed = time.time() - start
                tracker.add_timing(label, elapsed)
                print(f"    ✗ [{label}] 云端失败: {e}")
                return None


# ============================================================
# 准备知识库素材（三方案共用，保证公平）
# ============================================================
def prepare_kb_materials():
    """从向量库检索知识卡片，三方案共用同一批素材"""
    print(f"\n=== 准备知识库素材 ===")
    print(f"主题: {TEST_TOPIC} | 人群: {TEST_PERSONA}")
    cards = retrieve_from_kb(TEST_QUERY, TEST_PERSONA, top_n=10)
    print(f"检索到 {len(cards)} 张知识卡片")
    return cards


def prepare_web_materials():
    """联网搜索PubMed文献（方案B/C共用）
    注意：PubMed是英文数据库，必须用英文关键词搜索
    """
    print(f"\n=== 准备联网素材（PubMed） ===")
    print(f"  英文关键词: {TEST_PUBMED_QUERY}")
    try:
        from pipeline_v32 import search_pubmed_online
        materials = search_pubmed_online(TEST_PUBMED_QUERY, max_results=4)
        print(f"  检索到 {len(materials)} 篇PubMed文献")
        for i, m in enumerate(materials):
            print(f"    [{i+1}] {m.get('id','')} | {m.get('title','')[:60]}")
        return materials
    except Exception as e:
        print(f"  ⚠ PubMed搜索失败: {e}，使用空素材")
        return []


# ============================================================
# 方案A：纯本地（Ollama生成完整母稿 + 本地校验）
# ============================================================
def run_plan_a(kb_cards):
    print(f"\n{'='*70}")
    print(f"  方案A：纯本地（Ollama生成完整母稿 + 本地校验）")
    print(f"{'='*70}")
    tracker = PlanTokenTracker()

    # Stage 1: 本地生成框架（完整母稿）
    print(f"\n[Stage 1] 本地Ollama生成完整母稿...")
    # 复用 pipeline_v32 的 prompt 构建逻辑，但走 tracked 调用
    from pipeline_v32 import build_mother_format, SYSTEM_STAGE1
    sub_cards = [c for c in kb_cards if c.get("sub_group")]
    gen_cards = [c for c in kb_cards if not c.get("sub_group")]
    top_cards = (sub_cards + gen_cards[:4])[:14]
    materials = "【本地知识库素材】\n"
    for i, c in enumerate(top_cards):
        source_note = ""
        if c.get("sub_group"):
            source_note += f" | 细分人群：{c['sub_group']}"
        if c.get("source_channel"):
            source_note += f" | 来源：{c['source_channel']}"
        content_len = 120 if c.get("sub_group") else 150
        materials += f"\n[{i+1}] {c.get('title','')}{source_note}\n内容：{c.get('content','')[:content_len]}\n"

    prompt = f"""请根据以下本地知识库素材，为「{TEST_TOPIC}」生成一篇完整的科普文章正文。
目标人群：{TEST_PERSONA}。

{materials}

【生成要求】
1. 仅基于上述知识库素材生成完整正文，不引入外部文献
2. 所有标签齐全、板块顺序正确
3. 三层难度递进：速读卡→深度文→综述文
4. 每个板块必须有实质内容，禁止只写提纲
5. 参考文献只列知识库中真实存在的资料

{build_mother_format(TEST_PERSONA)}"""

    article = call_ollama_tracked(prompt, SYSTEM_STAGE1, tracker, "A-Stage1生成", temp=0.3, max_tokens=3000)

    if not article:
        print("  ✗ 方案A失败：Stage1无输出")
        return {"plan": "A", "success": False, "article": "", "tracker": tracker.summary()}

    # Stage 3: 本地校验（轻量，仅检查标签）
    print(f"\n[Stage 3] 本地格式校验...")
    missing = [tag for tag in REQUIRED_TAGS if tag not in article]
    if missing:
        # 本地修复（补全缺失标签）
        fix_prompt = f"""以下是科普文章母稿，缺失部分标签。请补全所有缺失标签，确保15个标签齐全且顺序正确。
缺失标签：{', '.join(missing)}

【文章】
{article}

{build_mother_format(TEST_PERSONA)}"""
        fixed = call_ollama_tracked(fix_prompt, SYSTEM_STAGE3, tracker, "A-Stage3修复", temp=0.3, max_tokens=3000)
        if fixed:
            article = fixed

    return {
        "plan": "A",
        "success": bool(article),
        "article": article or "",
        "tracker": tracker.summary(),
    }


# ============================================================
# 方案B：混合（本地搭框架 → 云端外扩 → 本地校验）
# ============================================================
def run_plan_b(kb_cards, web_materials):
    print(f"\n{'='*70}")
    print(f"  方案B：混合（本地搭框架 → 云端外扩 → 本地校验）")
    print(f"{'='*70}")
    tracker = PlanTokenTracker()

    # Stage 1: 本地搭框架
    print(f"\n[Stage 1] 本地Ollama搭建框架...")
    from pipeline_v32 import build_mother_format, SYSTEM_STAGE1
    sub_cards = [c for c in kb_cards if c.get("sub_group")]
    gen_cards = [c for c in kb_cards if not c.get("sub_group")]
    top_cards = (sub_cards + gen_cards[:4])[:14]
    materials = "【本地知识库素材】\n"
    for i, c in enumerate(top_cards):
        source_note = ""
        if c.get("sub_group"):
            source_note += f" | 细分人群：{c['sub_group']}"
        if c.get("source_channel"):
            source_note += f" | 来源：{c['source_channel']}"
        content_len = 120 if c.get("sub_group") else 150
        materials += f"\n[{i+1}] {c.get('title','')}{source_note}\n内容：{c.get('content','')[:content_len]}\n"

    prompt = f"""请根据以下本地知识库素材，为「{TEST_TOPIC}」生成一篇完整的科普文章正文。
目标人群：{TEST_PERSONA}。

{materials}

【生成要求】
1. 仅基于上述知识库素材生成完整正文，不引入外部文献
2. 所有标签齐全、板块顺序正确
3. 三层难度递进：速读卡→深度文→综述文
4. 每个板块必须有实质内容，禁止只写提纲
5. 参考文献只列知识库中真实存在的资料

{build_mother_format(TEST_PERSONA)}"""

    framework = call_ollama_tracked(prompt, SYSTEM_STAGE1, tracker, "B-Stage1框架", temp=0.3, max_tokens=2500)

    if not framework:
        print("  ✗ 方案B失败：Stage1无输出")
        return {"plan": "B", "success": False, "article": "", "tracker": tracker.summary()}

    # Stage 2: 云端外扩
    print(f"\n[Stage 2] 云端DeepSeek外扩补强...")
    if web_materials:
        web_text = "【联网搜索新素材（仅限以下文献）】\n"
        for i, m in enumerate(web_materials):
            pmid_num = m.get("id", "").replace("PMID_", "").replace("PMID:", "")
            web_text += f"\n[{i+1}] PMID:{pmid_num}\n标题：{m.get('title','')}\n期刊：{m.get('journal','')}\n年份：{m.get('pubdate','')}\n内容：{m.get('content','')[:300]}\n"
        allowed_pmids = [m.get("id", "").replace("PMID_", "").replace("PMID:", "") for m in web_materials]
        allowed_pmids_str = ", ".join([f"PMID:{p}" for p in allowed_pmids if p])
    else:
        web_text = "（本次无联网新素材，请仅基于初稿做内容补强和格式完善）"
        allowed_pmids_str = "（无PMID白名单）"

    prompt2 = f"""以下是一篇关于「{TEST_TOPIC}」的科普文章初稿（基于本地知识库生成）。
请对文章进行内容补强和格式完善。

【文章初稿】
{framework}

{web_text}

【允许引用的PMID白名单】
{allowed_pmids_str}

【补强要求】
1. 严禁修改、打乱、新增、删减原有文章框架与标签结构
2. 所有【#标记名#】必须保持原样，独占完整一行
3. 必须确保输出包含全部15个母稿标签
4. 如果初稿中缺失某些标签，必须补全
5. 只能使用上方白名单中的PMID
6. 三层难度递进：速读卡(纯实操)→深度文(原理)→综述文(学术)
7. 全文控制在3000~6000字
8. 输出完整的补强后文章

{build_mother_format(TEST_PERSONA)}"""

    article = call_cloud_tracked(prompt2, SYSTEM_STAGE2, tracker, "B-Stage2外扩", temp=0.7, max_tokens=3500)

    if not article:
        print("  ⚠ Stage2无输出，使用框架作为最终结果")
        article = framework

    # Stage 3: 本地校验
    print(f"\n[Stage 3] 本地格式校验...")
    missing = [tag for tag in REQUIRED_TAGS if tag not in article]
    if missing:
        fix_prompt = f"""以下是科普文章母稿，缺失部分标签。请补全所有缺失标签。
缺失标签：{', '.join(missing)}

【文章】
{article}

{build_mother_format(TEST_PERSONA)}"""
        fixed = call_ollama_tracked(fix_prompt, SYSTEM_STAGE3, tracker, "B-Stage3修复", temp=0.3, max_tokens=3000)
        if fixed:
            article = fixed
    else:
        print("    ✓ 标签完整，无需修复")

    return {
        "plan": "B",
        "success": bool(article),
        "article": article or "",
        "tracker": tracker.summary(),
    }


# ============================================================
# 方案C：纯云端（DeepSeek直接生成完整母稿 + 云端校验）
# ============================================================
def run_plan_c(kb_cards, web_materials):
    print(f"\n{'='*70}")
    print(f"  方案C：纯云端（DeepSeek直接生成完整母稿 + 云端校验）")
    print(f"{'='*70}")
    tracker = PlanTokenTracker()

    # Stage 1: 云端直接生成完整母稿
    print(f"\n[Stage 1] 云端DeepSeek生成完整母稿...")
    from pipeline_v32 import build_mother_format, SYSTEM_STAGE1
    sub_cards = [c for c in kb_cards if c.get("sub_group")]
    gen_cards = [c for c in kb_cards if not c.get("sub_group")]
    top_cards = (sub_cards + gen_cards[:4])[:14]
    materials = "【本地知识库素材】\n"
    for i, c in enumerate(top_cards):
        source_note = ""
        if c.get("sub_group"):
            source_note += f" | 细分人群：{c['sub_group']}"
        if c.get("source_channel"):
            source_note += f" | 来源：{c['source_channel']}"
        content_len = 120 if c.get("sub_group") else 150
        materials += f"\n[{i+1}] {c.get('title','')}{source_note}\n内容：{c.get('content','')[:content_len]}\n"

    # 方案C额外注入联网素材（云端一次性消化）
    if web_materials:
        web_text = "\n【联网文献素材（可引用，PMID需真实）】\n"
        for i, m in enumerate(web_materials):
            pmid_num = m.get("id", "").replace("PMID_", "").replace("PMID:", "")
            web_text += f"\n[{i+1}] PMID:{pmid_num} | {m.get('title','')} | {m.get('journal','')} | {m.get('pubdate','')}\n内容：{m.get('content','')[:250]}\n"
    else:
        web_text = ""

    prompt = f"""请根据以下知识库素材和联网文献，为「{TEST_TOPIC}」生成一篇完整的科普文章正文。
目标人群：{TEST_PERSONA}。

{materials}
{web_text}

【生成要求】
1. 基于上述素材生成完整正文，可引用联网文献的PMID
2. 所有标签齐全、板块顺序正确
3. 三层难度递进：速读卡→深度文→综述文
4. 每个板块必须有实质内容，禁止只写提纲
5. 参考文献列出知识库资料和联网文献
6. 正文引用统一[序号]上角标

{build_mother_format(TEST_PERSONA)}"""

    article = call_cloud_tracked(prompt, SYSTEM_STAGE1, tracker, "C-Stage1生成", temp=0.5, max_tokens=3500)

    if not article:
        print("  ✗ 方案C失败：Stage1无输出")
        return {"plan": "C", "success": False, "article": "", "tracker": tracker.summary()}

    # Stage 3: 云端校验修复
    print(f"\n[Stage 3] 云端格式校验...")
    missing = [tag for tag in REQUIRED_TAGS if tag not in article]
    if missing:
        fix_prompt = f"""以下是科普文章母稿，缺失部分标签。请补全所有缺失标签，确保15个标签齐全且顺序正确。
缺失标签：{', '.join(missing)}

【文章】
{article}

{build_mother_format(TEST_PERSONA)}"""
        fixed = call_cloud_tracked(fix_prompt, SYSTEM_STAGE3, tracker, "C-Stage3修复", temp=0.3, max_tokens=3000)
        if fixed:
            article = fixed
    else:
        print("    ✓ 标签完整，无需修复")

    return {
        "plan": "C",
        "success": bool(article),
        "article": article or "",
        "tracker": tracker.summary(),
    }


# ============================================================
# 质量评估
# ============================================================
def evaluate_article(article: str) -> dict:
    """评估文章质量（15标签完整性 + 字数 + 结构）"""
    if not article:
        return {"valid": False, "reason": "空文章"}

    tags_found = [tag for tag in REQUIRED_TAGS if tag in article]
    tags_missing = [tag for tag in REQUIRED_TAGS if tag not in article]

    # 各板块字数统计
    sections = {}
    section_map = {
        "META": ("【#META#】", "【字数弹性规则】"),
        "ALL_INTRO": ("【#ALL_INTRO#】", "【#SUMMARY_FAST#】"),
        "COMMON": ("【#COMMON_BEGIN#】", "【#COMMON_END#】"),
        "DEEP_PLUS": ("【#DEEP_PLUS_BEGIN#】", "【#DEEP_PLUS_END#】"),
        "DEBATE": ("【#DEBATE_ZONE_BEGIN#】", "【#DEBATE_ZONE_END#】"),
        "REF_LIST": ("【#REF_LIST#】", None),
    }
    for name, (start, end) in section_map.items():
        if start in article:
            s_idx = article.index(start) + len(start)
            if end:
                e_idx = article.find(end, s_idx)
                if e_idx == -1:
                    e_idx = len(article)
            else:
                e_idx = len(article)
            sections[name] = len(article[s_idx:e_idx].strip())

    # 参考文献数量
    import re
    ref_count = len(re.findall(r"^\[\d+\]", article, re.MULTILINE))

    return {
        "valid": True,
        "total_length": len(article),
        "tags_found": len(tags_found),
        "tags_missing": tags_missing,
        "tag_integrity": f"{len(tags_found)}/15",
        "sections_char": sections,
        "ref_count": ref_count,
    }


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="科普文章母稿三方案对比测试")
    parser.add_argument("--plan", choices=["A", "B", "C"], help="只跑指定方案")
    parser.add_argument("--report", action="store_true", help="生成对比报告")
    args = parser.parse_args()

    if args.report:
        generate_report()
        return

    # 准备共用素材
    kb_cards = prepare_kb_materials()
    web_materials = prepare_web_materials() if (not args.plan or args.plan in ("B", "C")) else []

    results = {}
    plans_to_run = [args.plan] if args.plan else ["A", "B", "C"]

    for plan in plans_to_run:
        print(f"\n{'#'*70}")
        print(f"# 开始执行方案 {plan}")
        print(f"{'#'*70}")
        start = time.time()
        if plan == "A":
            result = run_plan_a(kb_cards)
        elif plan == "B":
            result = run_plan_b(kb_cards, web_materials)
        elif plan == "C":
            result = run_plan_c(kb_cards, web_materials)
        total = time.time() - start
        result["total_wall_time"] = round(total, 2)
        result["quality"] = evaluate_article(result.get("article", ""))
        results[plan] = result

        # 保存单方案结果
        path = os.path.join(OUTPUT_DIR, f"result_plan_{plan}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n方案 {plan} 结果已保存: {path}")

    # 如果三方案都跑了，自动生成报告
    if len(results) == 3:
        generate_report()


def generate_report():
    """生成三方案对比报告"""
    print(f"\n{'='*70}")
    print("生成三方案对比报告")
    print(f"{'='*70}")

    all_results = {}
    for plan in ["A", "B", "C"]:
        path = os.path.join(OUTPUT_DIR, f"result_plan_{plan}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                all_results[plan] = json.load(f)
        else:
            print(f"  ⚠ 方案 {plan} 结果不存在，请先运行")

    if len(all_results) < 2:
        print("  至少需要2个方案结果才能生成对比报告")
        return

    report_path = os.path.join(OUTPUT_DIR, "comparison_3plans.md")
    lines = []
    lines.append("# 科普文章母稿生成：三方案对比测试报告\n")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"测试主题: {TEST_TOPIC} | 目标人群: {TEST_PERSONA}\n")
    lines.append("---\n")

    # 1. 方案说明
    lines.append("## 一、方案说明\n")
    lines.append("| 方案 | Stage 1 框架 | Stage 2 外扩 | Stage 3 校验 | 说明 |")
    lines.append("|------|-------------|-------------|-------------|------|")
    lines.append("| A 纯本地 | Ollama | — | Ollama | 全程零云端token，最省成本 |")
    lines.append("| B 混合 | Ollama | DeepSeek | Ollama | 本地搭框架省token，云端补质量 |")
    lines.append("| C 纯云端 | DeepSeek | — | DeepSeek | 质量最优，token消耗最高 |\n")

    # 2. 核心指标对比
    lines.append("## 二、核心指标对比\n")
    lines.append("| 指标 | 方案A 纯本地 | 方案B 混合 | 方案C 纯云端 |")
    lines.append("|------|------------|-----------|------------|")
    for metric, label in [
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
            r = all_results.get(plan, {})
            t = r.get("tracker", {})
            val = t.get(metric, 0) if metric != "total_wall_time" else r.get("total_wall_time", 0)
            row += f" {val} |"
        lines.append(row)

    # 文章质量
    lines.append("| 文章字数 |")
    for plan in ["A", "B", "C"]:
        q = all_results.get(plan, {}).get("quality", {})
        lines[-1] += f" {q.get('total_length', 0)} |"
    lines.append("| 标签完整性 |")
    for plan in ["A", "B", "C"]:
        q = all_results.get(plan, {}).get("quality", {})
        lines[-1] += f" {q.get('tag_integrity', '0/15')} |"
    lines.append("| 参考文献数 |")
    for plan in ["A", "B", "C"]:
        q = all_results.get(plan, {}).get("quality", {})
        lines[-1] += f" {q.get('ref_count', 0)} |"
    lines.append("")

    # 3. 各阶段耗时分解
    lines.append("## 三、各阶段耗时分解\n")
    for plan in ["A", "B", "C"]:
        r = all_results.get(plan, {})
        if not r:
            continue
        timings = r.get("tracker", {}).get("timings", [])
        lines.append(f"### 方案{plan}\n")
        lines.append("| 阶段 | 耗时(s) |")
        lines.append("|------|---------|")
        for stage, elapsed in timings:
            lines.append(f"| {stage} | {elapsed} |")
        lines.append(f"| **总计** | **{r.get('total_wall_time', 0)}** |\n")

    # 4. 云端token消耗分析
    lines.append("## 四、云端token消耗分析\n")
    lines.append("| 方案 | 输入token | 输出token | 总token | 调用次数 | 单次均价token |")
    lines.append("|------|----------|----------|---------|---------|--------------|")
    for plan in ["A", "B", "C"]:
        t = all_results.get(plan, {}).get("tracker", {})
        pt = t.get("cloud_prompt_tokens", 0)
        ct = t.get("cloud_completion_tokens", 0)
        total = t.get("cloud_total_tokens", 0)
        calls = t.get("cloud_calls", 0)
        avg = total // calls if calls > 0 else 0
        lines.append(f"| 方案{plan} | {pt} | {ct} | {total} | {calls} | {avg} |")
    lines.append("")

    # 节省分析
    a_tokens = all_results.get("A", {}).get("tracker", {}).get("cloud_total_tokens", 0)
    b_tokens = all_results.get("B", {}).get("tracker", {}).get("cloud_total_tokens", 0)
    c_tokens = all_results.get("C", {}).get("tracker", {}).get("cloud_total_tokens", 0)
    lines.append("**云端token节省分析**：\n")
    if c_tokens > 0:
        lines.append(f"- 方案A vs 方案C：节省 {c_tokens - a_tokens} token ({(c_tokens - a_tokens)/c_tokens*100:.1f}%)")
    if c_tokens > 0:
        lines.append(f"- 方案B vs 方案C：节省 {c_tokens - b_tokens} token ({(c_tokens - b_tokens)/c_tokens*100:.1f}%)")
    if b_tokens > 0 and a_tokens == 0:
        lines.append(f"- 方案A 完全零云端token（本地大模型搭框架+校验）\n")

    # 5. 文章质量对比
    lines.append("## 五、文章质量对比\n")
    for plan in ["A", "B", "C"]:
        r = all_results.get(plan, {})
        q = r.get("quality", {})
        if not q.get("valid"):
            lines.append(f"### 方案{plan}: 文章无效\n")
            continue
        lines.append(f"### 方案{plan}\n")
        lines.append(f"- 总字数: {q.get('total_length', 0)}")
        lines.append(f"- 标签完整性: {q.get('tag_integrity', '0/15')}")
        if q.get("tags_missing"):
            lines.append(f"- 缺失标签: {', '.join(q['tags_missing'])}")
        lines.append(f"- 参考文献数: {q.get('ref_count', 0)}")
        sections = q.get("sections_char", {})
        if sections:
            lines.append(f"- 各板块字数:")
            for sname, sval in sections.items():
                lines.append(f"  - {sname}: {sval}字")
        # 文章预览
        article = r.get("article", "")
        lines.append(f"\n**文章预览**（前400字）:\n")
        lines.append("```\n" + (article[:400] if article else "(空)") + "\n```\n")

    # 6. 综合结论
    lines.append("## 六、综合结论\n")
    lines.append("### 6.1 成本视角\n")
    lines.append(f"- **方案A（纯本地）**：云端token = {a_tokens}，零成本（仅电费），适合大批量初稿生成")
    lines.append(f"- **方案B（混合）**：云端token = {b_tokens}，比纯云端节省 {(c_tokens-b_tokens)/c_tokens*100:.1f}%（如c_tokens>0）")
    lines.append(f"- **方案C（纯云端）**：云端token = {c_tokens}，质量最优但成本最高\n")

    lines.append("### 6.2 时间视角\n")
    for plan in ["A", "B", "C"]:
        r = all_results.get(plan, {})
        lines.append(f"- 方案{plan}: {r.get('total_wall_time', 0)}s")
    lines.append("")

    lines.append("### 6.3 推荐场景\n")
    lines.append("| 场景 | 推荐方案 | 原因 |")
    lines.append("|------|---------|------|")
    lines.append("| 大批量初稿（成本敏感） | 方案A | 零云端token，后续可选择性升级 |")
    lines.append("| 平衡质量与成本（推荐） | 方案B | 本地搭框架省token，云端补质量 |")
    lines.append("| 最高质量（不计成本） | 方案C | 一次性生成最优内容 |")
    lines.append("| 离线/隐私场景 | 方案A | 完全本地运行 |\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n对比报告已生成: {report_path}")
    print("=" * 70)
    # 打印前50行
    print("\n".join(lines[:50]))


if __name__ == "__main__":
    main()
