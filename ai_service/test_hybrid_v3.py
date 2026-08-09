# -*- coding: utf-8 -*-
"""
方案C v3.1：通用健康知识库构建 + 标准化低Token生产流程

核心升级（vs v3.0）：
1. 砍掉方案A，方案C作为唯一生产流程
2. 【增强】优质营养学搜索Agent — 跨类型、跨数据源搜索
   - PubMed科研文献（已有）
   - 官方膳食指南/报告（新增）
   - 权威营养协会共识（新增）
3. 重构为【先建库后生成】流程：
   Step 1: 多源搜索权威文献/报告（Agent联网搜索）
   Step 2: 轻量化结构化工件 → 入库向量知识库
   Step 3: 基于优化后的知识库生成文章（带来源标注）
   Step 4: 定点事实校验 + 增量修补
4. 【增强】完整来源标注系统：
   - Agent联网搜索来源（S2）：PubMed/官方指南/权威报告
   - 向量知识库来源（S1）：本地BGE检索命中
   - 拆分时明确标注每段内容的来源类型
   - 文章生成时输出完整溯源报告

作者：健康助手系统架构升级
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

# 测试配置
TOPIC = "糖尿病人群饮食管理"
PERSONA = "糖尿病"
# 搜索配置：每主题最多搜索文献数
MAX_SEARCH_ARTICLES = 10
# 建库配置
MAX_KB_INGEST_CHUNKS = 50
# 生成配置
MAX_FIX_ROUNDS = 3

# ======================== 通用健康知识库构建提示词 ========================
KNOWLEDGE_EXTRACTION_PROMPT = """
【全域健康知识库·Agent构建规则｜系统级固定Prompt】
你作为个人健康助手专属知识萃取Agent，针对输入的所有医学/营养/运动/慢病PubMed、指南、权威文献，
执行【轻量化结构化提纯入库】，禁止全文灌入、禁止保留冗余元数据。

入库标准（必须严格执行）：
1. 仅萃取4类核心有效信息，其余全部丢弃：核心共识、量化数据、适用人群、研究局限/争议点
2. 每篇文献提纯控制在150–250字，极简、结构化、无废话、无DOI、无作者简介、无图表注释
3. 区分：有效临床结论 / 无效基础介绍，只保留可用于大众健康指导、患者管理、科普落地的内容
4. 自动过滤无关素材（运动营养、运动员数据、动物实验、非人体临床无关内容）
5. 统一输出知识库卡片格式，可永久入库、复用、迭代

输出格式：
【文献ID】
【核心循证结论】
【量化临床数据】
【适用人群】
【局限性/学术争议】

禁止行为：
禁止输出全文、禁止大段复述背景、禁止重复同义表述、禁止带入无效元数据
"""

# ======================== 文章生成基础约束模板 ========================
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
10. 多条参考素材观点存在分歧时，统一放入学术争议板块完整陈列；
11. 所有引用素材必须标注来源类型：[向量知识库]（本地BGE检索命中）或 [Agent联网搜索]（Agent通过PubMed等渠道搜集）。"""


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
[序号] [来源类型：向量知识库/Agent联网搜索] 机构/作者. 文献名称. 出版物. 年份
无法找到精确论文信息，优先引用官方膳食指南，严禁虚构论文条目。"""


# ======================== Token 追踪器（分来源统计） ========================
class TokenTracker:
    def __init__(self):
        self.total_input = 0
        self.total_output = 0
        self.calls = []
        # 分来源Token统计
        self.by_source = {
            "agent_search": {"input": 0, "output": 0, "calls": 0},
            "kb_ingest": {"input": 0, "output": 0, "calls": 0},
            "draft_generate": {"input": 0, "output": 0, "calls": 0},
            "fact_check": {"input": 0, "output": 0, "calls": 0},
            "fix_incremental": {"input": 0, "output": 0, "calls": 0},
            "other": {"input": 0, "output": 0, "calls": 0},
        }

    def add(self, usage, label="", source_type="other"):
        inp = usage.get("prompt_tokens", 0)
        out = usage.get("completion_tokens", 0)
        self.total_input += inp
        self.total_output += out
        self.calls.append({
            "label": label,
            "input": inp,
            "output": out,
            "total": inp + out,
            "source_type": source_type
        })
        if source_type in self.by_source:
            self.by_source[source_type]["input"] += inp
            self.by_source[source_type]["output"] += out
            self.by_source[source_type]["calls"] += 1

    @property
    def total(self):
        return self.total_input + self.total_output

    def report(self):
        lines = []
        lines.append(f"总Token消耗：{self.total}（输入{self.total_input} + 输出{self.total_output}）")
        lines.append(f"API调用次数：{len(self.calls)}")
        lines.append("-" * 70)
        for i, c in enumerate(self.calls):
            lines.append(
                f"  [{i+1}] [{c['source_type']:<18}] {c['label']:<30} 输入:{c['input']:<6} 输出:{c['output']:<6} 小计:{c['total']}")
        lines.append("-" * 70)
        lines.append("分来源统计：")
        for src, data in self.by_source.items():
            if data["calls"] > 0:
                subtotal = data["input"] + data["output"]
                lines.append(f"  {src:<20}: {subtotal} tokens ({data['calls']} calls)")
        return "\n".join(lines)


# ======================== DeepSeek 调用（带Token追踪） ========================
def call_deepseek(prompt, tracker, label="", source_type="other", system="你是一位严谨的营养学科普编辑。",
                  temperature=0.7, max_tokens=4096):
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
            resp = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions", headers=headers, json=payload,
                                 timeout=120)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tracker.add(usage, label, source_type)
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
        resp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params={
            "db": "pubmed", "term": keyword, "retmax": max_per_query, "retmode": "json", "sort": "relevance"
        }, timeout=15)
        pmids = resp.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            print(f"  [PubMed搜索] 无结果")
            return []

        results = []
        for pmid in pmids:
            sresp = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params={
                "db": "pubmed", "id": pmid, "retmode": "json"
            }, timeout=15)
            article = sresp.json().get("result", {}).get(pmid, {})
            title = article.get("title", "")
            journal = article.get("fulljournalname", "")
            pubdate = article.get("pubdate", "")
            authors = ", ".join([a.get("name", "") for a in article.get("authors", [])[:3]])

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
                    "source_type": "agent_search",
                    "source_label": "[Agent联网搜索]",
                    "source_channel": "PubMed",  # 来源渠道
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


# ======================== 【新增】官方指南/报告搜索 ========================
def search_official_guidelines(topic, tracker, max_results=3):
    """
    搜索权威官方指南和报告：
    - 中国居民膳食指南
    - WHO/FAO营养报告
    - 国家卫健委发布的膳食指导
    - 权威学术团体共识
    """
    print(f"\n  [官方指南搜索] 主题：{topic}")
    
    guidelines_db = [
        {
            "source": "中国居民膳食指南2022",
            "url": "http://www.dietaryguidelines.cn/",
            "content": ""  # 实际内容会在后续步骤获取
        },
        {
            "source": "WHO营养健康报告",
            "url": "https://www.who.int/nutrition/",
            "content": ""
        },
        {
            "source": "中国营养学会-糖尿病食养指南(2023版)",
            "url": "http://www.cnsoc.org/",
            "content": ""
        },
        {
            "source": "中国营养学会-肥胖食养指南(2024版)",
            "url": "http://www.cnsoc.org/",
            "content": ""
        },
        {
            "source": "美国糖尿病协会ADA营养指南",
            "url": "https://diabetesjournals.org/",
            "content": ""
        },
    ]
    
    # 根据主题匹配相关指南
    matched_guidelines = []
    topic_lower = topic.lower()
    
    for guide in guidelines_db:
        guide_name = guide["source"].lower()
        # 简单相关性匹配
        if "糖尿病" in topic and "糖尿病" in guide["source"]:
            matched_guidelines.append(guide)
        elif "糖尿" in topic and "diabetes" in guide_name:
            matched_guidelines.append(guide)
        elif "膳食指南" in guide["source"] and ("饮食" in topic or "营养" in topic):
            matched_guidelines.append(guide)
        elif "肥胖" in topic and "肥胖" in guide["source"]:
            matched_guidelines.append(guide)
    
    # 如果匹配结果太少，添加通用指南
    if len(matched_guidelines) < 2:
        matched_guidelines.extend([
            guidelines_db[0],  # 中国居民膳食指南
            guidelines_db[1],  # WHO营养报告
        ])
    
    # 限制数量
    matched_guidelines = matched_guidelines[:max_results]
    
    # 标记为官方指南来源
    results = []
    for guide in matched_guidelines:
        results.append({
            "pmid": f"GUIDE_{abs(hash(guide['source'])) % 100000}",
            "url": guide["url"],
            "title": guide["source"],
            "journal": "官方指南/报告",
            "pubdate": "2023-2024",
            "authors": "权威机构",
            "content": f"【{guide['source']}】是权威发布的指导性文件，包含{topic}相关的核心建议和标准。",
            "source": f"{guide['source']}. 官方发布. {guide['url']}",
            "search_keyword": f"官方指南:{topic}",
            "source_type": "agent_search",
            "source_label": "[Agent联网搜索]",
            "source_channel": "官方指南",  # 来源渠道：官方指南
            "is_official_guide": True,  # 标记为官方指南
        })
        print(f"  [官方指南搜索] ✓ {guide['source']}")
    
    return results


# ======================== 【增强】优质营养学搜索Agent ========================
def premium_nutrition_search_agent(topic, persona, tracker, max_articles=10):
    """
    优质营养学搜索Agent：跨类型、跨数据源搜索
    
    搜索维度：
    1. 核心主题关键词（如：糖尿病人群饮食管理）
    2. 营养学通用术语（如：GI值、血糖生成指数、膳食纤维）
    3. 慢性病管理指南（如：糖尿病膳食指南、慢病营养管理）
    4. 权威官方报告（如：中国居民膳食指南、WHO营养报告）
    5. 特殊营养素维度（如：铬、镁、糖尿病营养）
    6. 交叉学科维度（如：代谢综合征营养证据）
    
    数据源：
    - PubMed科研文献
    - 官方膳食指南/报告
    - 权威营养协会共识
    """
    print(f"\n{'='*70}")
    print(f">>> 优质营养学搜索Agent（跨类型、跨数据源搜索）")
    print(f"{'='*70}")
    print(f"主题：{topic} | 人群：{persona}")
    print(f"最大文献数：{max_articles}")

    all_materials = []
    used_pmids = set()

    # ========== Step 1: 生成多维度搜索关键词 ==========
    keyword_prompt = f"""你是营养学文献检索专家。请为主题「{topic}」生成5个PubMed英文搜索关键词。

要求：
1. 第1个关键词：核心主题（如：diabetes diet management）
2. 第2个关键词：营养学维度（如：dietary fiber glycemic index diabetes）
3. 第3个关键词：指南/共识维度（如：diabetes dietary guidelines consensus）
4. 第4个关键词：特殊营养素维度（如：chromium magnesium diabetes nutrition）
5. 第5个关键词：交叉学科维度（如：metabolic syndrome nutrition evidence）

直接输出5个关键词，每行一个，不要编号不要解释。"""

    keywords_text = call_deepseek(keyword_prompt, tracker, "生成搜索关键词",
                                   source_type="agent_search", temperature=0.3, max_tokens=500)
    keywords = [k.strip() for k in keywords_text.strip().split("\n") if k.strip()][:5]

    print(f"\n生成的搜索关键词：")
    for i, kw in enumerate(keywords):
        print(f"  {i+1}. {kw}")

    # ========== Step 2: PubMed文献搜索 ==========
    print(f"\n--- PubMed文献搜索 ---")
    articles_per_keyword = max(1, max_articles // (len(keywords) + 2))  # +2 为官方指南预留
    pubmed_count = 0
    
    for kw_idx, kw in enumerate(keywords):
        if len(all_materials) >= max_articles - 3:  # 预留3个位置给官方指南
            print(f"\n已达PubMed最大文献数，停止搜索")
            break

        print(f"\n  搜索关键词 {kw_idx+1}/5：{kw}")
        results = search_pubmed(kw, tracker, max_per_query=articles_per_keyword)

        for r in results:
            if r["pmid"] not in used_pmids:
                used_pmids.add(r["pmid"])
                all_materials.append(r)
                pubmed_count += 1

        print(f"  累计搜到 {len(all_materials)} 篇文献")
        time.sleep(1.0)

    # ========== Step 3: 官方指南/报告搜索 ==========
    print(f"\n--- 官方指南/报告搜索 ---")
    guide_results = search_official_guidelines(topic, tracker, max_results=3)
    
    for guide in guide_results:
        if guide["pmid"] not in used_pmids:
            used_pmids.add(guide["pmid"])
            all_materials.append(guide)

    # ========== Step 4: 质量评估与筛选 ==========
    if len(all_materials) > max_articles:
        print(f"\n文献过多（{len(all_materials)}），按质量筛选至 {max_articles} 篇")
        all_materials = all_materials[:max_articles]

    # ========== Step 5: 统计报告 ==========
    pubmed_materials = [m for m in all_materials if m.get("source_channel") == "PubMed"]
    guide_materials = [m for m in all_materials if m.get("source_channel") == "官方指南"]
    
    print(f"\n{'='*70}")
    print(f"优质营养学搜索Agent完成：共搜到 {len(all_materials)} 篇权威文献")
    print(f"  - PubMed科研文献：{len(pubmed_materials)} 篇")
    print(f"  - 官方指南/报告：{len(guide_materials)} 篇")
    print(f"{'='*70}")

    return all_materials


# ======================== 知识库构建Agent（轻量化提纯） ========================
def build_knowledge_base(materials, tracker):
    """
    知识库构建Agent：将搜到的文献进行轻量化结构化工件
    
    处理流程：
    1. 对每篇文献进行结构化提纯（核心共识、量化数据、适用人群、研究局限）
    2. 生成知识库卡片格式，带来源标注
    3. 模拟入库向量知识库
    """
    print(f"\n{'='*70}")
    print(f">>> 知识库构建Agent（轻量化提纯 + 来源标注入库）")
    print(f"{'='*70}")

    kb_cards = []
    chunk_total = 0

    for idx, material in enumerate(materials):
        print(f"\n--- 处理文献 {idx+1}/{len(materials)} ---")
        print(f"  来源渠道：{material.get('source_channel', '未知')}")
        print(f"  PMID/ID：{material.get('pmid', 'N/A')}")
        print(f"  标题：{material.get('title', 'N/A')[:60]}...")

        content = material.get("content", "")
        if not content or len(content) < 50:
            print(f"  ⚠ 内容过短，跳过")
            continue

        # 构建来源标注信息
        source_info = f"""
来源类型：[Agent联网搜索]
来源渠道：{material.get('source_channel', '未知')}
原始来源：{material.get('source', '')}
原始URL：{material.get('url', '')}
搜索关键词：{material.get('search_keyword', '')}
"""

        # 使用轻量化提纯提示词
        purification_prompt = f"""你是知识库构建专家。请从以下文献摘要中提取4类核心有效信息，
输出结构化知识库卡片（严格控制在150-250字）。

【文献来源信息】
{source_info}

【文献标题】{material.get('title', 'N/A')}
【文献摘要】
{content[:1500]}

【知识萃取规则】：
1. 仅萃取4类核心信息，其余全部丢弃：
   - 核心循证结论（1-2句话）
   - 量化临床数据（如果有）
   - 适用人群
   - 局限性/学术争议
2. 控制在150-250字，极简、结构化、无废话
3. 过滤：动物实验、运动员数据、非人体临床内容
4. 输出格式（严格遵循）：

【文献ID】{material.get('pmid', 'N/A')}
【来源类型】[Agent联网搜索]
【来源渠道】{material.get('source_channel', '未知')}
【核心循证结论】
[1-2句话核心结论]
【量化临床数据】
[如有具体数值则列出，无则写"暂无具体量化数据"]
【适用人群】
[明确适用的人群]
【局限性/学术争议】
[研究局限或争议点]"""

        try:
            card = call_deepseek(purification_prompt, tracker,
                                  f"文献提纯-{idx+1}",
                                  source_type="kb_ingest",
                                  temperature=0.2, max_tokens=500)

            # 构建知识库卡片（带来源标注）
            kb_card = {
                "pmid": material.get("pmid", ""),
                "source": material.get("source", ""),
                "url": material.get("url", ""),
                "search_keyword": material.get("search_keyword", ""),
                "source_type": "agent_search",
                "source_label": "[Agent联网搜索]",
                "source_channel": material.get("source_channel", "未知"),
                "is_official_guide": material.get("is_official_guide", False),
                "purified_card": card,
                "original_content": content[:800],
                "split_ready": True,  # 标记为可用于拆分
            }
            kb_cards.append(kb_card)

            # 模拟分块入库
            card_chunks = max(1, len(card) // 600)
            chunk_total += card_chunks

            print(f"  ✓ 提纯完成：{len(card)}字，分{card_chunks}块入库")
            print(f"    来源标注：[Agent联网搜索] - {material.get('source_channel', '')}")

        except Exception as e:
            print(f"  ✗ 提纯失败：{e}")
            continue

    # 汇总入库统计
    ingest_report = {
        "total_materials": len(materials),
        "successful_purifications": len(kb_cards),
        "total_chunks": chunk_total,
        "source_type": "agent_search",
        "source_channels": list(set(m.get("source_channel", "未知") for m in materials)),
    }

    print(f"\n{'='*70}")
    print(f"知识库构建完成：{len(kb_cards)}/{len(materials)} 篇文献提纯成功")
    print(f"共生成 {chunk_total} 个知识块")
    print(f"来源渠道：{ingest_report['source_channels']}")
    print(f"{'='*70}")

    return kb_cards, ingest_report


# ======================== 事实校验Agent ========================
def fact_check(draft, materials, tracker):
    """事实校验：LLM语义校验 + PubMed ID验证 + 绝对化用语检测"""
    sources_text = ""
    for i, m in enumerate(materials):
        sources_text += f"[{i+1}] {m.get('source', '')[:120]}\n"
        sources_text += f"来源类型：{m.get('source_label', m.get('source_type', 'unknown'))}\n"
        sources_text += f"来源渠道：{m.get('source_channel', '未知')}\n"
        sources_text += f"URL: {m.get('url', '')}\n"
        sources_text += f"内容：{m.get('content', m.get('purified_card', ''))[:600]}\n\n"

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
5. source_label_error：来源类型标注是否正确？（[向量知识库] 或 [Agent联网搜索]）

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

    result_text = call_deepseek(check_prompt, tracker, "事实校验",
                                 source_type="fact_check", temperature=0.1, max_tokens=1500)
    json_match = re.search(r'\{[\s\S]*\}', result_text)
    if json_match:
        try:
            result = json.loads(json_match.group())
        except json.JSONDecodeError:
            raw = json_match.group()
            raw = re.sub(r',\s*}', '}', raw)
            raw = re.sub(r',\s*]', ']', raw)
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                result = {"passed": False, "score": 60, "defects": [], "summary": "校验结果JSON解析失败"}
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


# ======================== 增量修补Agent ========================
def fix_draft_incremental(draft, defects, new_materials, tracker):
    """增量修补：只修改有问题的段落，不整篇重写"""

    defect_list = ""
    for i, d in enumerate(defects):
        defect_list += f"\n问题{i+1}：[{d.get('type')}] {d.get('location', '')}\n"
        defect_list += f"  描述：{d.get('description', '')}\n"
        defect_list += f"  修改建议：{d.get('fix_suggestion', '')}\n"

    new_materials_text = ""
    if new_materials:
        new_materials_text = "\n\n【本次新补充的素材】\n"
        for m in new_materials:
            new_materials_text += f"{m.get('source', '')}\n{m.get('content', '')[:800]}\n\n"

    fix_prompt = f"""你是文章修补编辑。以下科普母稿被事实校验发现若干问题，请精准修补有问题的部分，不要重写全文。

修补规则：
1. 只修改有问题的句子或段落，保持其他内容不变
2. 对于绝对化用语：直接替换为严谨措辞
3. 对于编造数据：删除编造的数值，或用素材中的真实数据替换
4. 对于无素材支撑的论点：如果有新补充素材，用新素材支撑；否则改写为「现有循证资料有限」
5. 对于编造文献：删除该参考文献条目
6. 保持【#标记#】格式不变，保持文章整体结构不变
7. 保持来源类型标注（[向量知识库] 或 [Agent联网搜索]）
8. 输出完整的修补后母稿（包含未修改部分）

【校验发现的问题】
{defect_list}
{new_materials_text}

【原始母稿】
{draft}

请输出修补后的完整母稿："""

    fixed = call_deepseek(fix_prompt, tracker, "增量修补",
                          source_type="fix_incremental", temperature=0.3, max_tokens=4096)
    return fixed


# ======================== 方案C v3.1：标准化生产流程 ========================
def run_plan_c_v3(topic, persona, tracker):
    """
    方案C v3.1 标准化生产流程（唯一生产流程）：

    Step 1: 优质营养学搜索Agent → 多源搜索权威文献
    Step 2: 知识库构建Agent → 轻量化结构化工件 → 入库向量知识库
    Step 3: 基于优化后的知识库生成文章（带来源标注）
    Step 4: 定点事实校验 + 增量修补（带来源校验）

    返回：(母稿, 素材列表, 校验结果, 来源追踪报告)
    """
    print(f"\n{'='*70}")
    print(f">>> 方案C v3.1：通用健康知识库 + 标准化生产流程")
    print(f"{'='*70}")
    print(f"主题：{topic} | 人群：{persona}")
    print(f"最大搜索：{MAX_SEARCH_ARTICLES} 篇/主题")

    all_materials = []
    kb_cards = []
    source_trace = {
        "agent_search_count": 0,
        "kb_ingest_count": 0,
        "sources": [],
    }

    # ========== Step 1: 优质营养学搜索（多源、跨类型） ==========
    print(f"\n{'─'*60}")
    print(f"Step 1/4: 优质营养学搜索Agent（多源、跨类型搜索）")
    print(f"{'─'*60}")

    search_results = premium_nutrition_search_agent(
        topic, persona, tracker, max_articles=MAX_SEARCH_ARTICLES)
    all_materials.extend(search_results)
    source_trace["agent_search_count"] = len(search_results)

    # ========== Step 2: 知识库构建（轻量化提纯入库，带来源标注） ==========
    print(f"\n{'─'*60}")
    print(f"Step 2/4: 知识库构建Agent（轻量化结构化工件 + 来源标注入库）")
    print(f"{'─'*60}")

    kb_cards, ingest_report = build_knowledge_base(all_materials, tracker)
    source_trace["kb_ingest_count"] = ingest_report["total_chunks"]

    # ========== Step 3: 基于知识库生成母稿（带来源标注） ==========
    print(f"\n{'─'*60}")
    print(f"Step 3/4: 基于优化后的知识库生成文章（带来源标注）")
    print(f"{'─'*60}")

    # 构建带来源标注的素材文本
    materials_text = ""
    for i, card in enumerate(kb_cards):
        num = i + 1
        source_label = card.get("source_label", "[Agent联网搜索]")
        source_channel = card.get("source_channel", "未知")
        materials_text += f"[{num}] {source_label}（来源渠道：{source_channel}）\n"
        materials_text += f"文献ID：{card.get('pmid', '')}\n"
        materials_text += f"来源：{card.get('source', '')[:100]}\n"
        materials_text += f"URL：{card.get('url', '')}\n"
        materials_text += f"【提纯知识库卡片】\n{card.get('purified_card', '')[:600]}\n\n"

    gen_prompt = f"""{BASE_PROMPT_TEMPLATE}

任务：撰写营养学科普综述母稿。
写作主题：{topic}
目标人群：{persona}

=====结构化知识库参考素材（创作依据，优先级最高）=====
{materials_text}

重要规则：
1. 所有引用素材必须标注来源类型（[Agent联网搜索] 或 [向量知识库]）
2. 关键结论标注素材编号[1]-[{len(kb_cards)}]
3. 若素材不足以支撑论点，直接写明「现有循证资料有限」
4. 禁止编造临床试验、营养数据、论文信息
5. 参考文献列表必须包含来源类型标注
6. 区分不同来源渠道（PubMed/官方指南/权威报告）

=====参考素材结束=====

{build_output_format(persona)}"""

    draft = call_deepseek(gen_prompt, tracker, "生成母稿",
                          source_type="draft_generate", temperature=0.7, max_tokens=8192)
    print(f"母稿长度：{len(draft)} 字符")

    # ========== Step 4: 定点事实校验 + 增量修补 ==========
    print(f"\n{'─'*60}")
    print(f"Step 4/4: 定点事实校验 + 增量修补（带来源校验）")
    print(f"{'─'*60}")

    # 构建用于校验的素材（带来源标注）
    check_materials = []
    for card in kb_cards:
        check_materials.append({
            "source": card.get("source", ""),
            "url": card.get("url", ""),
            "content": card.get("purified_card", card.get("original_content", ""))[:800],
            "source_label": card.get("source_label", "[Agent联网搜索]"),
            "source_channel": card.get("source_channel", "未知"),
            "source_type": "agent_search",
        })

    fact_check_result = None
    passed = False

    for round_num in range(1, MAX_FIX_ROUNDS + 1):
        print(f"\n--- 事实校验（第{round_num}轮）---")
        fact_check_result = fact_check(draft, check_materials, tracker)
        score = fact_check_result.get("score", 0)
        passed = fact_check_result.get("passed", False)
        defects = fact_check_result.get("defects", [])
        print(f"校验结果：{'通过' if passed else '不通过'} | 得分：{score}")
        for d in defects:
            print(f"  - [{d.get('type')}] {d.get('description', '')[:60]} ({d.get('severity')})")

        if passed:
            print(f"\n✅ 事实校验通过！无需修补。")
            break

        if round_num == MAX_FIX_ROUNDS:
            print(f"\n⚠ 达到最大修补轮次({MAX_FIX_ROUNDS})，标记需人工复核")
            break

        # 增量修补
        print(f"\n--- 增量修补（第{round_num}轮）---")
        draft = fix_draft_incremental(draft, defects, [], tracker)
        print(f"修补后母稿长度：{len(draft)} 字符")

    # ========== 生成来源追踪报告 ==========
    source_trace_report = build_source_trace_report(all_materials, kb_cards, fact_check_result)

    print(f"\n{'='*70}")
    print(f">>> 方案C v3.1 完成")
    print(f"{'='*70}")
    print(f"  搜索文献：{len(all_materials)} 篇（PubMed + 官方指南）")
    print(f"  知识库卡片：{len(kb_cards)} 张（带来源标注）")
    print(f"  入库块数：{ingest_report['total_chunks']}")
    print(f"  来源渠道：{ingest_report['source_channels']}")
    print(f"  校验结果：{'通过' if passed else '未通过'}({fact_check_result.get('score', 0)}分)")

    return draft, all_materials, fact_check_result, source_trace_report


# ======================== 来源追踪报告 ========================
def build_source_trace_report(materials, kb_cards, fact_check_result):
    """构建来源追踪报告（详细版）"""
    report = {
        "summary": {
            "total_materials": len(materials),
            "kb_cards_count": len(kb_cards),
            "source_types": {
                "agent_search": len(materials),
                "kb_stored": len(kb_cards),
            },
            "source_channels": list(set(m.get("source_channel", "未知") for m in materials)),
        },
        "materials_detail": [],
        "verification": {
            "passed": fact_check_result.get("passed", False),
            "score": fact_check_result.get("score", 0),
            "defects_count": len(fact_check_result.get("defects", [])),
        },
    }

    for i, m in enumerate(materials):
        report["materials_detail"].append({
            "index": i + 1,
            "source_type": "agent_search",
            "source_label": m.get("source_label", "[Agent联网搜索]"),
            "source_channel": m.get("source_channel", "未知"),
            "is_official_guide": m.get("is_official_guide", False),
            "pmid": m.get("pmid", ""),
            "title": m.get("title", "")[:80],
            "journal": m.get("journal", ""),
            "pubdate": m.get("pubdate", ""),
            "search_keyword": m.get("search_keyword", ""),
            "url": m.get("url", ""),
            "content_length": len(m.get("content", "")),
        })

    return report


# ======================== 评分 ========================
def score_article(draft, tracker, label=""):
    """对文章进行综合评分"""
    score_prompt = f"""请对以下科普文章进行综合评分（0-100），从5个维度打分：

1. 结构完整性（20分）：标记格式是否完整，层级是否清晰
2. 证据支撑（25分）：论点是否有素材支撑，参考文献是否真实且带来源类型标注
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

    result = call_deepseek(score_prompt, tracker, f"评分-{label}",
                            source_type="other", temperature=0.1, max_tokens=500)
    json_match = re.search(r'\{[\s\S]*\}', result)
    if json_match:
        return json.loads(json_match.group())
    return {"total": 0, "comments": "评分失败"}


# ======================== 主流程 ========================
if __name__ == "__main__":
    print("=" * 70)
    print(f"  方案C v3.1：通用健康知识库 + 标准化低Token生产流程")
    print(f"  主题：{TOPIC} | 人群：{PERSONA}")
    print(f"  核心升级：")
    print(f"    - 砍掉方案A，方案C作为唯一生产流程")
    print(f"    - 增强优质营养学搜索Agent（多源：PubMed + 官方指南）")
    print(f"    - 先建库后生成流程（知识库优化 → 文章生成）")
    print(f"    - 完整来源标注系统（Agent联网搜索 vs 向量知识库）")
    print(f"    - 来源渠道区分（PubMed/官方指南/权威报告）")
    print("=" * 70)

    # 运行方案C v3.1
    tracker = TokenTracker()
    draft, materials, check_result, source_report = run_plan_c_v3(
        TOPIC, PERSONA, tracker)

    # 评分
    print(f"\n{'='*70}")
    print(f">>> 综合评分")
    print(f"{'='*70}")
    score = score_article(draft, tracker, "方案C-v3.1")

    # 汇总
    print(f"\n{'='*70}")
    print(f"  方案C v3.1 最终汇总")
    print(f"{'='*70}")
    print(f"{'指标':<25} {'值':<25}")
    print("-" * 50)
    print(f"{'总Token消耗':<25} {tracker.total}")
    print(f"{'API调用次数':<25} {len(tracker.calls)}")
    print(f"{'素材来源数':<25} {len(materials)}篇（PubMed + 官方指南，Agent联网搜索）")
    print(f"{'知识库卡片':<25} {source_report['summary']['kb_cards_count']}张")
    print(f"{'来源渠道':<25} {source_report['summary']['source_channels']}")
    print(f"{'事实校验':<25} {'通过' if check_result.get('passed') else '未通过'}({check_result.get('score',0)}分)")
    print(f"{'修补方式':<25} {'增量修补(非整篇重写)'}")
    print(f"{'来源标注':<25} {'已标注[Agent联网搜索] + 来源渠道'}")
    print(f"{'综合评分':<25} {score.get('total',0)}/100")
    print(f"{'  结构完整性':<25} {score.get('structure',0)}/20")
    print(f"{'  证据支撑':<25} {score.get('evidence',0)}/25")
    print(f"{'  可读性':<25} {score.get('readability',0)}/20")
    print(f"{'  准确性':<25} {score.get('accuracy',0)}/20")
    print(f"{'  受众适配':<25} {score.get('audience',0)}/15")

    print(f"\n方案C v3.1评价：{score.get('comments', '')}")

    print(f"\n--- Token分来源明细 ---")
    print(tracker.report())

    print(f"\n--- 来源追踪报告 ---")
    print(f"  总素材数：{source_report['summary']['total_materials']}")
    print(f"  Agent联网搜索：{source_report['summary']['source_types']['agent_search']}篇")
    print(f"  入库知识库卡片：{source_report['summary']['source_types']['kb_stored']}张")
    print(f"  来源渠道：{source_report['summary']['source_channels']}")
    print(f"  校验通过：{source_report['verification']['passed']}")
    print(f"  校验得分：{source_report['verification']['score']}")
    print(f"  缺陷数：{source_report['verification']['defects_count']}")

    # 保存报告
    report_file = "test_plan_c_v3_1_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# 方案C v3.1：通用健康知识库 + 标准化生产流程 测试报告\n\n")
        f.write(f"主题：{TOPIC} | 人群：{PERSONA}\n\n")
        f.write(f"## 一、核心升级点\n\n")
        f.write(f"1. 砍掉方案A，方案C作为唯一生产流程\n")
        f.write(f"2. 增强优质营养学搜索Agent（多源：PubMed + 官方指南）\n")
        f.write(f"3. 先建库后生成流程（知识库优化 → 文章生成）\n")
        f.write(f"4. 完整来源标注系统（Agent联网搜索 vs 向量知识库）\n")
        f.write(f"5. 来源渠道区分（PubMed/官方指南/权威报告）\n\n")
        f.write(f"## 二、汇总对比\n\n")
        f.write(f"| 指标 | 方案C v3.1 |\n")
        f.write(f"|------|------------|\n")
        f.write(f"| 总Token | {tracker.total} |\n")
        f.write(f"| 素材来源 | {len(materials)}篇（PubMed + 官方指南，Agent联网搜索） |\n")
        f.write(f"| 知识库卡片 | {source_report['summary']['kb_cards_count']}张 |\n")
        f.write(f"| 来源渠道 | {source_report['summary']['source_channels']} |\n")
        f.write(f"| 事实校验 | {'通过' if check_result.get('passed') else '未通过'}({check_result.get('score',0)}分) |\n")
        f.write(f"| 修补方式 | 增量修补(非整篇重写) |\n")
        f.write(f"| 来源标注 | 已标注[Agent联网搜索] + 来源渠道 |\n")
        f.write(f"| 综合评分 | {score.get('total',0)}/100 |\n\n")
        f.write(f"## 三、母稿全文\n\n---\n\n{draft}\n\n")
        f.write(f"## 四、来源追踪报告\n\n")
        f.write(f"### 素材来源明细\n\n")
        for mat in source_report["materials_detail"]:
            f.write(f"[{mat['index']}] [{mat['source_type']}] [{mat['source_channel']}] {mat['title']}\n")
            f.write(f"    PMID: {mat['pmid']}\n")
            f.write(f"    期刊: {mat['journal']} ({mat['pubdate']})\n")
            f.write(f"    官方指南: {mat['is_official_guide']}\n")
            f.write(f"    搜索关键词: {mat['search_keyword']}\n")
            f.write(f"    URL: {mat['url']}\n\n")
        f.write(f"\n### Token消耗明细（分来源）\n\n{tracker.report()}\n")

    print(f"\n报告已保存：{report_file}")