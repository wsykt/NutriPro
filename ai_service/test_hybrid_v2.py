# -*- coding: utf-8 -*-
"""
改进版方案C：增量修补（非整篇重写）+ 动态补搜文献（max 10篇）+ 总Token追踪 + 入库
对比方案A：同主题生成，对比评分。

核心改进：
1. 事实校验发现问题后，只修补有问题的句子，不整篇重写
2. 缺素材的论点 → 动态补搜1-2篇文献（每主题累计不超过10篇）
3. 全程追踪总Token消耗
4. 所有搜到的文献最后拆分入库向量知识库
"""
import requests
import json
import time
import re
import os
from bs4 import BeautifulSoup

# ======================== 配置 ========================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"

TOPIC = "糖尿病人群饮食管理"
PERSONA = "糖尿病"
MAX_TOTAL_ARTICLES = 10  # 每主题最多搜索10篇
MAX_FIX_ROUNDS = 4       # 最多修补4轮

BASE_PROMPT_TEMPLATE = """你是一位严谨的营养学科普编辑。所有输出必须遵守以下规则：
1. 严格区分确定循证结论与学术争议内容，争议内容固定放置争议专区；
2. 实操建议整理为清单形式，适配前端卡片展示；
3. 语言为严谨大众科普文风，兼顾专业性与可读性；
4. 【#标记名#】必须独占完整一行，该行不能附带空格、文字、符号；不允许修改标记文本。
5. 营养数据、膳食准则优先使用下方提供的知识库资料，禁止编造数值；
6. 涉及疾病膳食建议，需要标注：建议咨询医生或营养师；
7. 严格控制各个章节字数区间；
8. 参考文献优先使用检索命中的原始权威资料；严禁凭空编造论文。若素材不足，可标注「参考：中国居民膳食指南2022」；
9. 禁止使用绝对化表述（一定、根治、百分百、特效）；
10. 多条参考素材观点存在分歧时，统一放入学术争议板块完整陈列。"""


def build_output_format(persona):
    return f"""输出严格按顺序排版，每个标记单独占一行，相邻区块空一行：

【#META#】
标题：直击{persona}人群痛点，不添加篇幅后缀
人群标签：{persona}
分类：慢病管理/运动营养/消化健康/母婴营养/老年营养/青少年营养
阅读时长_速读：约1分钟
阅读时长_深度：约3分钟
阅读时长_综述：约5分钟
权威来源：中国居民膳食指南2022、WHO/FAO国际指南、相关营养学研究

【#ALL_INTRO#】
通用引言（三篇共用，2~3句话）：点明人群核心痛点+1条流行病学数据

【#SUMMARY_FAST#】
速读卡摘要：20-40字，提炼核心行动建议

【#SUMMARY_DEEP#】
深度文摘要：40-60字，说明核心饮食调理方向

【#SUMMARY_ALL#】
综述摘要：50-80字，包含学界共识与现存分歧

【#COMMON_BEGIN#】
共识基础内容（三篇文章共用，400~600字）
一级标题使用中文编号：一、二、三
二级标题：（一）（二）（三）
内容多用清单、要点排版
【#COMMON_END#】

【#DEEP_PLUS_BEGIN#】
深度拓展板块（深度文、综述文展示，600~900字）
【#DEEP_PLUS_END#】

【#DEBATE_ZONE_BEGIN#】
（学术争议，仅综述保留。约200-400字）
【#DEBATE_ZONE_END#】

【#CONCLUDE_FAST#】
速读卡结论：1~2句简洁行动纲领

【#CONCLUDE_DEEP#】
深度文结论：内容总结+核心膳食建议

【#CONCLUDE_ALL#】
综述结论：循证共识总结 + 研究局限与未来方向

【#REF_LIST#】
参考文献，共计6~8条，标准格式：
[序号] 机构/作者. 文献名称. 出版物. 年份
无法找到精确论文信息，优先引用官方膳食指南，严禁虚构论文条目。"""


# ======================== Token 追踪器 ========================
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.calls = []

    def add(self, usage, label=""):
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        self.total_input += inp
        self.total_output += out
        self.calls.append({"label": label, "input": inp, "output": out, "total": inp + out})

    @property
    def total(self):
        return self.total_input + self.total_output

    def report(self):
        lines = []
        lines.append(f"总Token消耗：{self.total}（输入{self.total_input} + 输出{self.total_output}）")
        lines.append(f"API调用次数：{len(self.calls)}")
        lines.append("-" * 70)
        for i, c in enumerate(self.calls):
            lines.append(f"  [{i+1}] {c['label']:<30} 输入:{c['input']:<6} 输出:{c['output']:<6} 小计:{c['total']}")
        return "\n".join(lines)


# ======================== DeepSeek 调用（带Token追踪） ========================
def call_deepseek(prompt, tracker, label="", system="你是一位严谨的营养学科普编辑。", temperature=0.7, max_tokens=4096):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    for attempt in range(3):
        try:
            resp = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions", headers=headers, json=payload, timeout=120)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tracker.add(usage, label)
            return content
        except Exception as e:
            if attempt < 2:
                print(f"  [重试 {attempt+1}/3] {label} 调用失败：{e}")
                time.sleep(3)
            else:
                raise


# ======================== PubMed 搜索（真实API） ========================
def search_pubmed(keyword, tracker, max_per_query=2):
    """通过PubMed E-utilities API搜索真实文献"""
    print(f"  [PubMed搜索] 关键词：{keyword}")
    try:
        # ESearch
        resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={
            "db": "pubmed", "term": keyword, "retmax": max_per_query, "retmode": "json", "sort": "relevance"
        }, timeout=15)
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            print(f"  [PubMed搜索] 无结果")
            return []

        results = []
        for pmid in pmids:
            # ESummary
            sresp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
                "db": "pubmed", "id": pmid, "retmode": "json"
            }, timeout=15)
            article = sresp.json().get("result", {}).get(pmid, {})
            title = article.get("title", "")
            journal = article.get("fulljournalname", "")
            pubdate = article.get("pubdate", "")
            authors = ", ".join([a.get("name", "") for a in article.get("authors", [])[:3]])

            # EFetch (摘要)
            fresp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params={
                "db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract"
            }, timeout=15)
            abstract = extract_abstract(fresp.text)

            if title and abstract:
                results.append({
                    "pmid": pmid,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "title": title,
                    "journal": journal,
                    "pubdate": pubdate,
                    "authors": authors,
                    "content": abstract[:2000],
                    "source": f"PubMed:{pmid}. {authors}. {title}. {journal}. {pubdate}",
                    "search_keyword": keyword,
                })
                print(f"  [PubMed搜索] ✓ PMID:{pmid} - {title[:50]}...")
            time.sleep(0.5)
        return results
    except Exception as e:
        print(f"  [PubMed搜索] 失败：{e}")
        return []


def extract_abstract(xml_text):
    try:
        soup = BeautifulSoup(xml_text, "xml")
        abstract = soup.find("Abstract")
        if abstract:
            return " ".join([t.get_text(strip=True) for t in abstract.find_all("AbstractText")])
        return ""
    except Exception:
        return ""


# ======================== 事实校验Agent ========================
def fact_check(draft, materials, tracker):
    """事实校验：LLM语义校验 + PubMed ID验证 + 绝对化用语检测"""
    sources_text = ""
    for i, m in enumerate(materials):
        sources_text += f"[{i+1}] {m['source'][:120]}\nURL: {m['url']}\n{m['content'][:600]}\n\n"

    check_prompt = f"""你是一个严格的事实校验编辑。核查以下科普母稿，对照参考素材，输出JSON。

【参考素材】
{sources_text[:3000]}

【待校验母稿】
{draft[:4000]}

核验清单：
1. unsourced_claim：引用编号[x]在素材中找不到对应原文？有无无素材支撑的论点？
2. fabricated_data：营养数值、统计结论和素材不一致？有无编造数据？
3. absolute_language：存在绝对化用语（一定、根治、百分百、特效）？
4. source_mismatch：标注编号和实际引用内容不匹配？

严格输出JSON（不要其他内容）：
{{
  "passed": true/false,
  "score": 0-100,
  "defects": [
    {{"type": "类型", "location": "问题出在哪一段/哪一句", "description": "具体描述", "fix_suggestion": "修改建议", "severity": "high/medium/low"}}
  ],
  "summary": "总结"
}}

判定：有high缺陷或score<80 → passed=false"""

    result_text = call_deepseek(check_prompt, tracker, "事实校验", temperature=0.1, max_tokens=1500)
    json_match = re.search(r'\{[\s\S]*\}', result_text)
    if json_match:
        try:
            result = json.loads(json_match.group())
        except json.JSONDecodeError:
            # 容错：尝试修复常见JSON格式问题
            raw = json_match.group()
            # 移除尾部多余的逗号
            raw = re.sub(r',\s*}', '}', raw)
            raw = re.sub(r',\s*]', ']', raw)
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                # 最终兜底：保守判定
                result = {"passed": False, "score": 60, "defects": [], "summary": "校验结果JSON解析失败，保守判定需人工复核"}
    else:
        result = {"passed": False, "score": 50, "defects": [], "summary": "解析失败"}

    # PubMed ID验证
    ref_section = draft.split("【#REF_LIST#】")[-1] if "【#REF_LIST#】" in draft else ""
    pmids = re.findall(r'PubMed:?\s*(\d+)|pubmed/(\d+)', ref_section, re.IGNORECASE)
    for groups in pmids:
        pmid = groups[0] or groups[1]
        if pmid:
            is_real = verify_pubmed(pmid)
            if not is_real:
                result["passed"] = False
                result["defects"].append({
                    "type": "fabricated_reference",
                    "location": "参考文献列表",
                    "description": f"PubMed ID {pmid} 不存在",
                    "fix_suggestion": "删除该编造文献或替换为真实文献",
                    "severity": "high"
                })

    # 绝对化用语
    for word in ["一定", "根治", "百分百", "特效", "彻底治愈"]:
        if word in draft:
            result["defects"].append({
                "type": "absolute_language",
                "location": f"包含「{word}」的句子",
                "description": f"发现绝对化用语「{word}」",
                "fix_suggestion": f"将「{word}」改为「建议/有助于/优先选择」",
                "severity": "medium"
            })

    has_high = any(d.get("severity") == "high" for d in result.get("defects", []))
    if has_high:
        result["passed"] = False

    return result


def verify_pubmed(pmid):
    try:
        resp = requests.get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
            "db": "pubmed", "id": pmid, "retmode": "json"
        }, timeout=10)
        return pmid in resp.json().get("result", {}).get("uids", [])
    except Exception:
        return True


# ======================== 增量修补Agent（核心改进：不整篇重写） ========================
def fix_draft_incremental(draft, defects, new_materials, tracker):
    """增量修补：只修改有问题的段落，不整篇重写"""

    # 分类缺陷
    wording_defects = [d for d in defects if d.get("type") in ["absolute_language", "fabricated_data"]]
    source_defects = [d for d in defects if d.get("type") in ["unsourced_claim", "source_mismatch", "fabricated_reference"]]

    # 构建修补指令
    defect_list = ""
    for i, d in enumerate(defects):
        defect_list += f"\n问题{i+1}：[{d.get('type')}] {d.get('location', '')}\n"
        defect_list += f"  描述：{d.get('description', '')}\n"
        defect_list += f"  修改建议：{d.get('fix_suggestion', '')}\n"

    # 新补充素材
    new_materials_text = ""
    if new_materials:
        new_materials_text = "\n\n【本次新补充的素材】\n"
        for m in new_materials:
            new_materials_text += f"{m['source']}\n{m['content'][:800]}\n\n"

    fix_prompt = f"""你是文章修补编辑。以下科普母稿被事实校验发现若干问题，请精准修补有问题的部分，不要重写全文。

修补规则：
1. 只修改有问题的句子或段落，保持其他内容不变
2. 对于绝对化用语：直接替换为严谨措辞
3. 对于编造数据：删除编造的数值，或用素材中的真实数据替换
4. 对于无素材支撑的论点：如果有新补充素材，用新素材支撑；否则改写为「现有循证资料有限」
5. 对于编造文献：删除该参考文献条目
6. 保持【#标记#】格式不变，保持文章整体结构不变
7. 输出完整的修补后母稿（包含未修改部分）

【校验发现的问题】
{defect_list}
{new_materials_text}

【原始母稿】
{draft}

请输出修补后的完整母稿："""

    fixed = call_deepseek(fix_prompt, tracker, "增量修补", temperature=0.3, max_tokens=4096)
    return fixed


# ======================== 方案A：纯RAG生成 ========================
def run_plan_a(topic, persona, tracker):
    """方案A：无Agent搜索，无事实校验，单次生成"""
    print(f"\n{'='*70}")
    print(f">>> 方案A：纯RAG模式生成")
    print(f"{'='*70}")

    prompt = f"""{BASE_PROMPT_TEMPLATE}

任务：撰写营养学科普综述母稿，使用规定标记分割全部内容。
写作主题：{topic}
目标人群：{persona}

参考知识库片段（必须优先使用，禁止编造）：
中国居民膳食指南2022、WHO/FAO国际指南、PubMed收录论文等权威来源

{build_output_format(persona)}"""

    print(f"Prompt长度：{len(prompt)} 字符")
    draft = call_deepseek(prompt, tracker, "方案A-生成", temperature=0.7)
    print(f"母稿长度：{len(draft)} 字符")
    return draft


# ======================== 方案C（改进版）：混合架构 ========================
def run_plan_c(topic, persona, tracker):
    """方案C改进版：搜索→生成→校验→增量修补→补搜→再校验→入库"""
    print(f"\n{'='*70}")
    print(f">>> 方案C改进版：混合架构（增量修补 + 动态补搜 + 入库）")
    print(f"{'='*70}")

    all_materials = []

    # Step 1: 初始搜索3篇
    print(f"\n--- Step 1: 初始资料搜索（3篇）---")
    kw_prompt = f"""主题：{topic}。请输出3个PubMed英文搜索关键词，用换行分隔。"""
    keywords_text = call_deepseek(kw_prompt, tracker, "方案C-关键词生成", temperature=0.3, max_tokens=200)
    keywords = [k.strip() for k in keywords_text.strip().split("\n") if k.strip()][:3]

    for kw in keywords:
        if len(all_materials) >= 3:
            break
        results = search_pubmed(kw, tracker, max_per_query=1)
        all_materials.extend(results)
        time.sleep(1.0)

    print(f"初始素材：{len(all_materials)} 篇")

    # Step 2: 生成母稿
    print(f"\n--- Step 2: 生成母稿 ---")
    materials_text = ""
    for i, m in enumerate(all_materials):
        materials_text += f"[{i+1}] {m['source'][:120]}\nURL: {m['url']}\n{m['content'][:1000]}\n\n"

    gen_prompt = f"""{BASE_PROMPT_TEMPLATE}

任务：撰写营养学科普综述母稿。
写作主题：{topic}
目标人群：{persona}

=====参考素材（创作依据，优先级最高）=====
{materials_text}
关键结论标注素材编号[1]-[{len(all_materials)}]。
=====参考素材结束=====

{build_output_format(persona)}"""

    draft = call_deepseek(gen_prompt, tracker, "方案C-生成母稿", temperature=0.7)
    print(f"母稿长度：{len(draft)} 字符")

    # Step 3: 校验 → 增量修补循环
    for round_num in range(1, MAX_FIX_ROUNDS + 1):
        print(f"\n--- Step 3.{round_num}: 事实校验（第{round_num}轮）---")
        check_result = fact_check(draft, all_materials, tracker)
        score = check_result.get("score", 0)
        passed = check_result.get("passed", False)
        defects = check_result.get("defects", [])
        print(f"校验结果：{'通过' if passed else '不通过'} | 得分：{score}")
        for d in defects:
            print(f"  - [{d.get('type')}] {d.get('description', '')[:60]} ({d.get('severity')})")

        if passed:
            print(f"\n✅ 事实校验通过！无需修补。")
            break

        if round_num == MAX_FIX_ROUNDS:
            print(f"\n⚠ 达到最大修补轮次({MAX_FIX_ROUNDS})，标记需人工复核")
            break

        # Step 3a: 对无素材支撑的论点，补搜文献
        unsourced = [d for d in defects if d.get("type") in ["unsourced_claim", "fabricated_reference"]]
        new_materials = []
        if unsourced and len(all_materials) < MAX_TOTAL_ARTICLES:
            supplement_kw = f"{topic} 营养 dietary guideline OR nutrition OR evidence"
            slots = min(2, MAX_TOTAL_ARTICLES - len(all_materials))
            print(f"\n--- 补搜文献（{slots}篇，累计上限{MAX_TOTAL_ARTICLES}）---")
            new_materials = search_pubmed(supplement_kw, tracker, max_per_query=slots)
            if new_materials:
                # 重新编号
                for m in new_materials:
                    m["number"] = len(all_materials) + 1
                    all_materials.append(m)
                print(f"补充素材：{len(new_materials)} 篇，累计 {len(all_materials)} 篇")

        # Step 3b: 增量修补（不整篇重写）
        print(f"\n--- 增量修补（第{round_num}轮）---")
        draft = fix_draft_incremental(draft, defects, new_materials, tracker)
        print(f"修补后母稿长度：{len(draft)} 字符")

    # Step 4: 入库（所有搜到的文献拆分入库）
    print(f"\n--- Step 4: 文献入库向量知识库 ---")
    ingest_report = simulate_ingest(all_materials, tracker)
    print(f"入库结果：{ingest_report['chunks']} 个文本块，来自 {ingest_report['articles']} 篇文献")

    return draft, all_materials, check_result


def simulate_ingest(materials, tracker):
    """模拟入库：统计分块数（实际系统调用 /knowledge/ingest）"""
    total_chunks = 0
    for m in materials:
        content = m.get("content", "")
        # 按600字分块
        chunks = max(1, len(content) // 600)
        total_chunks += chunks
    return {"articles": len(materials), "chunks": total_chunks}


# ======================== 评分对比 ========================
def score_article(draft, tracker, label=""):
    """对文章进行综合评分"""
    score_prompt = f"""请对以下科普文章进行综合评分（0-100），从5个维度打分：

1. 结构完整性（20分）：标记格式是否完整，层级是否清晰
2. 证据支撑（25分）：论点是否有素材支撑，参考文献是否真实
3. 可读性（20分）：语言是否通俗易懂，段落是否清晰
4. 准确性（20分）：营养数据是否准确，有无编造内容
5. 受众适配（15分）：内容是否贴合目标人群

【文章】
{draft[:3000]}

输出JSON：
{{
  "total": 0-100,
  "structure": 0-20,
  "evidence": 0-25,
  "readability": 0-20,
  "accuracy": 0-20,
  "audience": 0-15,
  "comments": "一句话评价"
}}"""

    result = call_deepseek(score_prompt, tracker, f"评分-{label}", temperature=0.1, max_tokens=500)
    json_match = re.search(r'\{[\s\S]*\}', result)
    if json_match:
        return json.loads(json_match.group())
    return {"total": 0, "comments": "评分失败"}


# ======================== 主流程 ========================
if __name__ == "__main__":
    print("=" * 70)
    print(f"  方案A vs 方案C(改进版) 真实对比测试")
    print(f"  主题：{TOPIC} | 人群：{PERSONA}")
    print(f"  方案C改进：增量修补 + 动态补搜(max{MAX_TOTAL_ARTICLES}篇) + 入库")
    print("=" * 70)

    tracker_a = TokenTracker()
    tracker_c = TokenTracker()

    # 方案A
    draft_a = run_plan_a(TOPIC, PERSONA, tracker_a)

    # 方案C
    draft_c, materials_c, check_c = run_plan_c(TOPIC, PERSONA, tracker_c)

    # 评分
    print(f"\n{'='*70}")
    print(f">>> 综合评分")
    print(f"{'='*70}")
    score_a = score_article(draft_a, tracker_a, "方案A")
    score_c = score_article(draft_c, tracker_c, "方案C")

    # 汇总
    print(f"\n{'='*70}")
    print(f"  最终对比汇总")
    print(f"{'='*70}")
    print(f"{'指标':<25} {'方案A（纯RAG）':<25} {'方案C（混合改进）':<25}")
    print("-" * 75)
    print(f"{'总Token消耗':<25} {tracker_a.total:<25} {tracker_c.total:<25}")
    print(f"{'API调用次数':<25} {len(tracker_a.calls):<25} {len(tracker_c.calls):<25}")
    print(f"{'素材来源数':<25} {'0篇':<25} {f'{len(materials_c)}篇（真实PubMed）':<25}")
    print(f"{'事实校验':<25} {'无':<25} {f'{'通过' if check_c.get('passed') else '未通过'}({check_c.get('score',0)}分)':<25}")
    print(f"{'修补方式':<25} {'无':<25} {'增量修补(非整篇重写)':<25}")
    print(f"{'文献入库':<25} {'无':<25} {f'{len(materials_c)}篇入库':<25}")
    print(f"{'综合评分':<25} {str(score_a.get('total',0))+'/100':<25} {str(score_c.get('total',0))+'/100':<25}")
    print(f"{'  结构完整性':<25} {str(score_a.get('structure',0))+'/20':<25} {str(score_c.get('structure',0))+'/20':<25}")
    print(f"{'  证据支撑':<25} {str(score_a.get('evidence',0))+'/25':<25} {str(score_c.get('evidence',0))+'/25':<25}")
    print(f"{'  可读性':<25} {str(score_a.get('readability',0))+'/20':<25} {str(score_c.get('readability',0))+'/20':<25}")
    print(f"{'  准确性':<25} {str(score_a.get('accuracy',0))+'/20':<25} {str(score_c.get('accuracy',0))+'/20':<25}")
    print(f"{'  受众适配':<25} {str(score_a.get('audience',0))+'/15':<25} {str(score_c.get('audience',0))+'/15':<25}")

    print(f"\n方案A评价：{score_a.get('comments', '')}")
    print(f"方案C评价：{score_c.get('comments', '')}")

    print(f"\n--- 方案A Token明细 ---")
    print(tracker_a.report())
    print(f"\n--- 方案C Token明细 ---")
    print(tracker_c.report())

    # 保存
    with open("test_comparison_final.md", "w", encoding="utf-8") as f:
        f.write(f"# 方案A vs 方案C(改进版) 对比测试报告\n\n")
        f.write(f"主题：{TOPIC} | 人群：{PERSONA}\n\n")
        f.write(f"## 对比汇总\n\n")
        f.write(f"| 指标 | 方案A | 方案C |\n|------|------|------|\n")
        f.write(f"| 总Token | {tracker_a.total} | {tracker_c.total} |\n")
        f.write(f"| 素材来源 | 0篇 | {len(materials_c)}篇真实PubMed |\n")
        f.write(f"| 事实校验 | 无 | {'通过' if check_c.get('passed') else '未通过'}({check_c.get('score',0)}分) |\n")
        f.write(f"| 综合评分 | {score_a.get('total',0)}/100 | {score_c.get('total',0)}/100 |\n")
        f.write(f"| 文献入库 | 无 | {len(materials_c)}篇 |\n\n")
        f.write(f"## 方案A母稿\n\n---\n\n{draft_a}\n\n")
        f.write(f"## 方案C母稿\n\n---\n\n{draft_c}\n\n")
        f.write(f"## 方案C素材来源\n\n")
        for i, m in enumerate(materials_c):
            f.write(f"[{i+1}] {m['source'][:100]}\n    URL: {m['url']}\n\n")
        f.write(f"\n## Token消耗明细\n\n### 方案A\n{tracker_a.report()}\n\n### 方案C\n{tracker_c.report()}\n")

    print(f"\n报告已保存：test_comparison_final.md")
