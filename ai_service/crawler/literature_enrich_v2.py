# -*- coding: utf-8 -*-
"""
向量知识库扩展完善脚本 V2
========================
在 V1 基础上新增：
  1. PubMed 直采（E-utilities，覆盖之前未抓的主题）
  2. Semantic Scholar（含 TLDR 摘要，限流重试）
  3. 通用营养主题（膳食模式、微量元素、维生素、肠道健康等）
  4. 更多细分主题（女性更年期、素食者、高血压、心血管、肿瘤预防）

复用 V1 的去重和入库逻辑。
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional

AI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)

from config.settings import settings
from crawler.compliance import wait_before_request  # 三档限速：NCBI 等高信任域名

logger = logging.getLogger(__name__)


# ============================================================
# 一、扩展主题配置（含通用营养 + 细分人群）
# ============================================================
EXTENDED_TOPICS = [
    # === 通用营养主题（新增）===
    {"group": "普通人", "topic": "地中海膳食模式与心血管健康",
     "keywords": ["Mediterranean diet cardiovascular disease meta-analysis",
                  "Mediterranean dietary pattern mortality risk reduction"]},
    {"group": "普通人", "topic": "DASH饮食与高血压管理",
     "keywords": ["DASH diet hypertension blood pressure meta-analysis",
                  "Dietary Approaches Stop Hypertension sodium reduction"]},
    {"group": "普通人", "topic": "间歇性断食与代谢健康",
     "keywords": ["intermittent fasting metabolic health weight loss",
                  "time restricted eating insulin sensitivity"]},
    {"group": "普通人", "topic": "膳食纤维与肠道微生态",
     "keywords": ["dietary fiber gut microbiome short chain fatty acids",
                  "fiber intake colorectal cancer prevention meta-analysis"]},
    {"group": "普通人", "topic": "维生素D缺乏与慢性病",
     "keywords": ["vitamin D deficiency chronic disease mortality",
                  "vitamin D supplementation cancer cardiovascular prevention"]},
    {"group": "普通人", "topic": "益生菌与免疫健康",
     "keywords": ["probiotics immune function meta-analysis",
                  "Lactobacillus Bifidobacterium gut immunity clinical trial"]},
    {"group": "普通人", "topic": "微量元素锌与免疫功能",
     "keywords": ["zinc supplementation immune function common cold",
                  "zinc deficiency immune response elderly"]},
    {"group": "普通人", "topic": "铁缺乏与贫血防治",
     "keywords": ["iron deficiency anemia treatment supplementation",
                  "iron absorption enhancers inhibitors diet"]},
    {"group": "普通人", "topic": "钠钾平衡与血压",
     "keywords": ["sodium potassium ratio blood pressure",
                  "potassium intake hypertension stroke risk"]},
    {"group": "普通人", "topic": "抗氧化物质与衰老",
     "keywords": ["dietary antioxidants aging oxidative stress",
                  "polyphenols flavonoids chronic disease prevention"]},

    # === 健身人群扩展 ===
    {"group": "健身人群", "topic": "训练窗口期营养时机",
     "keywords": ["nutrient timing pre post workout protein",
                  "anabolic window protein synthesis muscle"]},
    {"group": "健身人群", "topic": "碳水化合物与运动表现",
     "keywords": ["carbohydrate loading endurance performance",
                  "glycogen replenishment post exercise carbs"]},
    {"group": "健身人群", "topic": "水合状态与运动表现",
     "keywords": ["hydration dehydration exercise performance",
                  "fluid replacement athletes sweat electrolyte"]},
    {"group": "健身人群", "topic": "HMB与肌肉保护",
     "keywords": ["HMB beta hydroxy beta methylbutyrate muscle damage",
                  "HMB supplementation lean mass preservation"]},
    {"group": "健身人群", "topic": "柑橘苷与脂肪氧化",
     "keywords": ["citrus aurantium synephrine fat oxidation",
                  "bitter orange extract weight loss safety"]},

    # === 孕妇/哺乳期扩展 ===
    {"group": "孕妇", "topic": "孕期体重增长指南",
     "keywords": ["gestational weight gain guidelines IOM",
                  "pregnancy weight gain outcomes BMI"]},
    {"group": "孕妇", "topic": "孕期碘需求与甲状腺",
     "keywords": ["iodine requirement pregnancy thyroid function",
                  "pregnancy iodine deficiency fetal development"]},
    {"group": "孕妇", "topic": "哺乳期营养与乳汁成分",
     "keywords": ["lactation nutrition breast milk composition",
                  "breastfeeding maternal diet DHA transfer"]},
    {"group": "孕妇", "topic": "孕期钙需求与骨骼",
     "keywords": ["calcium requirement pregnancy fetal bone",
                  "pregnancy calcium supplementation preeclampsia"]},

    # === 老年人扩展 ===
    {"group": "老年人", "topic": "老年维生素D与跌倒预防",
     "keywords": ["vitamin D supplementation falls elderly meta-analysis",
                  "older adults vitamin D fracture prevention"]},
    {"group": "老年人", "topic": "老年维生素B12缺乏",
     "keywords": ["vitamin B12 deficiency elderly cognitive",
                  "B12 malabsorption aging supplementation"]},
    {"group": "老年人", "topic": "老年骨密度与钙补充",
     "keywords": ["calcium supplementation bone density elderly",
                  "older adults calcium vitamin D fracture"]},
    {"group": "老年人", "topic": "老年认知衰退与地中海饮食",
     "keywords": ["Mediterranean diet cognitive decline elderly",
                  "MIND diet Alzheimer dementia prevention"]},

    # === 青少年扩展 ===
    {"group": "青少年", "topic": "青少年铁缺乏与学习能力",
     "keywords": ["adolescent iron deficiency anemia cognition",
                  "teenage girls iron supplementation academic"]},
    {"group": "青少年", "topic": "青少年早餐与认知表现",
     "keywords": ["breakfast adolescent cognition academic performance",
                  "school breakfast program children learning"]},
    {"group": "青少年", "topic": "青少年含糖饮料与肥胖",
     "keywords": ["sugar sweetened beverages adolescent obesity",
                  "teenager soft drinks metabolic risk"]},

    # === 糖尿病扩展 ===
    {"group": "糖尿病患者", "topic": "糖尿病生酮饮食安全性",
     "keywords": ["ketogenic diet type 2 diabetes safety",
                  "keto diet diabetes glycemic control adverse"]},
    {"group": "糖尿病患者", "topic": "糖尿病膳食纤维与血糖",
     "keywords": ["dietary fiber type 2 diabetes glycemic control",
                  "soluble fiber diabetes HbA1c reduction"]},
    {"group": "糖尿病患者", "topic": "糖尿病地中海饮食干预",
     "keywords": ["Mediterranean diet type 2 diabetes remission",
                  "low carb diet diabetes cardiovascular outcomes"]},

    # === 新增人群 ===
    {"group": "高血压患者", "topic": "高血压DASH饮食实践",
     "keywords": ["DASH diet hypertension implementation",
                  "DASH diet sodium reduction blood pressure"]},
    {"group": "高血压患者", "topic": "高血压钾镁补充",
     "keywords": ["potassium magnesium hypertension supplementation",
                  "electrolyte balance blood pressure regulation"]},
    {"group": "心血管患者", "topic": "心血管疾病Omega-3补充",
     "keywords": ["omega 3 EPA DHA cardiovascular disease prevention",
                  "fish oil supplementation heart failure arrhythmia"]},
    {"group": "心血管患者", "topic": "心血管疾病膳食纤维",
     "keywords": ["dietary fiber cardiovascular disease prevention",
                  "whole grain fiber coronary heart disease"]},
    {"group": "肿瘤预防人群", "topic": "肿瘤预防膳食模式",
     "keywords": ["cancer prevention dietary pattern Mediterranean",
                  "WCRF diet cancer prevention recommendations"]},
    {"group": "肿瘤预防人群", "topic": "十字花科蔬菜与肿瘤",
     "keywords": ["cruciferous vegetables cancer glucosinolates",
                  "broccoli Brassica cancer prevention meta-analysis"]},
    {"group": "素食人群", "topic": "素食者营养完整性",
     "keywords": ["vegetarian vegan nutrient adequacy B12 iron",
                  "plant based diet protein quality amino acid"]},
    {"group": "素食人群", "topic": "素食者骨骼健康",
     "keywords": ["vegan vegetarian bone density fracture risk",
                  "plant based diet calcium vitamin D bone"]},
    {"group": "更年期女性", "topic": "更年期大豆异黄酮",
     "keywords": ["soy isoflavones menopause hot flashes",
                  "phytoestrogen menopausal symptoms meta-analysis"]},
    {"group": "更年期女性", "topic": "更年期钙与骨密度",
     "keywords": ["menopause calcium bone density osteoporosis",
                  "postmenopausal women calcium vitamin D fracture"]},
]


# ============================================================
# 二、PubMed E-utilities 直采
# ============================================================
def search_pubmed_direct(query: str, max_results: int = 5) -> List[dict]:
    """PubMed E-utilities 直采（esearch + esummary + efetch）"""
    try:
        # 1. esearch 获取 PMID 列表
        wait_before_request("eutils.ncbi.nlm.nih.gov")
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results,
                    "retmode": "json", "sort": "relevance"},
            timeout=15)
        if resp.status_code != 200:
            return []
        pmids = resp.json().get("esearchresult", {}).get("idlist", []) or []
        if not pmids:
            return []

        # 2. esummary 获取基本信息
        sresp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            timeout=15)
        if sresp.status_code != 200:
            return []
        result = sresp.json().get("result", {}) or {}

        # 3. efetch 获取摘要（批量）
        abstracts = {}
        try:
            wait_before_request("eutils.ncbi.nlm.nih.gov")
            fresp = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                params={"db": "pubmed", "id": ",".join(pmids),
                        "retmode": "xml", "rettype": "abstract"},
                timeout=20)
            if fresp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(fresp.text, "xml")
                for article in soup.find_all("PubmedArticle"):
                    pmid_tag = article.find("PMID")
                    if pmid_tag:
                        pmid = pmid_tag.get_text()
                        abs_elem = article.find("Abstract")
                        if abs_elem:
                            texts = abs_elem.find_all("AbstractText")
                            abstracts[pmid] = " ".join([t.get_text(strip=True) for t in texts])
        except Exception:
            pass

        results = []
        for pmid in pmids:
            article = result.get(pmid, {}) or {}
            title = article.get("title", "")
            if not title:
                continue
            abstract = abstracts.get(pmid, "")
            if not abstract or len(abstract) < 100:
                abstract = f"研究探讨{title}的相关内容"
            authors_list = article.get("authors", []) or []
            authors = ", ".join([a.get("name", "") for a in authors_list[:3]])
            results.append({
                "id": f"PMID_{pmid}",
                "source_channel": "PubMed",
                "title": title,
                "authors": authors,
                "journal": article.get("fulljournalname", ""),
                "pubdate": article.get("pubdate", "")[:4],
                "content": abstract[:1000],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
            time.sleep(0.3)
        return results
    except Exception as e:
        logger.warning(f"PubMed搜索失败: {e}")
        return []


# ============================================================
# 三、Semantic Scholar（含 TLDR）
# ============================================================
def search_semantic_scholar(query: str, max_results: int = 5) -> List[dict]:
    """Semantic Scholar Graph API（含 TLDR 摘要，限流重试）"""
    for attempt in range(3):
        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": query, "limit": max_results,
                        "fields": "title,abstract,year,tldr,journal,authors,externalIds"},
                timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for p in data.get("data", []) or []:
                    title = p.get("title", "")
                    if not title:
                        continue
                    # 优先用 TLDR，其次 abstract
                    tldr = p.get("tldr")
                    content = ""
                    if tldr and tldr.get("text"):
                        content = tldr["text"]
                    elif p.get("abstract"):
                        content = p["abstract"]
                    if len(content) < 100:
                        content = f"研究探讨{title}的相关内容"
                    authors_list = p.get("authors", []) or []
                    authors = ", ".join([a.get("name", "") for a in authors_list[:3]])
                    ext = p.get("externalIds", {}) or {}
                    doi = ext.get("DOI", "")
                    pmid = ext.get("PubMed", "")
                    card_id = f"SS_{doi or pmid or hashlib.md5(title.encode()).hexdigest()[:10]}"
                    url = f"https://doi.org/{doi}" if doi else (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "")
                    journal = (p.get("journal") or {}).get("name", "") if p.get("journal") else ""
                    results.append({
                        "id": card_id,
                        "source_channel": "Semantic Scholar",
                        "title": title,
                        "authors": authors,
                        "journal": journal,
                        "pubdate": str(p.get("year", "") or ""),
                        "content": content[:1000],
                        "url": url,
                    })
                return results
            elif resp.status_code == 429:
                # 限流，等待后重试
                wait = 5 * (attempt + 1)
                logger.warning(f"Semantic Scholar 限流，等待 {wait}s 后重试")
                time.sleep(wait)
                continue
            else:
                return []
        except Exception as e:
            logger.warning(f"Semantic Scholar 异常: {e}")
            time.sleep(2)
    return []


# ============================================================
# 四、Europe-PMC（复用，扩展新主题）
# ============================================================
def search_europepmc(query: str, max_results: int = 5) -> List[dict]:
    """Europe-PMC REST API"""
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": query, "format": "json", "pageSize": max_results,
                    "resultType": "core"},
            timeout=20)
        if resp.status_code != 200:
            return []
        hits = resp.json().get("resultList", {}).get("result", []) or []
        results = []
        for r in hits:
            pmid = r.get("pmid") or r.get("id", "")
            if not pmid:
                continue
            abstract = r.get("abstractText", "") or ""
            if len(abstract) < 100:
                abstract = f"研究探讨{r.get('title', '')}的相关内容"
            jinfo = r.get("journalInfo", {}) or {}
            journal = (jinfo.get("journal", {}) or {}).get("title", "")
            results.append({
                "id": f"PMID_{pmid}",
                "source_channel": "Europe-PMC",
                "title": r.get("title", ""),
                "authors": r.get("authorString", "")[:150],
                "journal": journal,
                "pubdate": str(r.get("pubYear", "")),
                "content": abstract[:1000],
                "url": f"https://europepmc.org/article/MED/{pmid}",
            })
        return results
    except Exception as e:
        logger.warning(f"Europe-PMC异常: {e}")
        return []


# ============================================================
# 四b、PubMed Central 全文库直采（PMC，E-utilities db=pmc）
# ============================================================
def search_pmc_direct(query: str, max_results: int = 5) -> List[dict]:
    """NCBI PMC 直采（esearch db=pmc + efetch），获取含全文摘要的权威文献"""
    try:
        params = {"db": "pmc", "term": query, "retmax": max_results,
                  "retmode": "json", "sort": "relevance"}
        if settings.PUBMED_EUTILS_EMAIL:
            params["tool"] = "health-assistant"
            params["email"] = settings.PUBMED_EUTILS_EMAIL
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params=params, timeout=15)
        if resp.status_code != 200:
            return []
        pmc_ids = resp.json().get("esearchresult", {}).get("idlist", []) or []
        if not pmc_ids:
            return []

        # efetch 批量取摘要（PMC 全文 XML 中提取 abstract）
        efetch_params = {"db": "pmc", "id": ",".join(pmc_ids), "retmode": "xml"}
        if settings.PUBMED_EUTILS_EMAIL:
            efetch_params["tool"] = "health-assistant"
            efetch_params["email"] = settings.PUBMED_EUTILS_EMAIL
        eresp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params=efetch_params, timeout=20)
        if eresp.status_code != 200:
            return []

        # 解析 PMC XML：article-title / abstract
        import xml.etree.ElementTree as ET
        results = []
        try:
            root = ET.fromstring(eresp.content)
            for article in root.findall(".//article"):
                pmid = article.findtext(".//article-id[@pub-id-type='pmc']") or ""
                if not pmid:
                    pmid = article.findtext(".//article-id[@pub-id-type='pmid']") or ""
                title = article.findtext(".//article-title") or ""
                # 拼接所有 abstract 段落
                abs_parts = []
                for node in article.findall(".//abstract"):
                    for seg in node.itertext():
                        seg = seg.strip()
                        if seg:
                            abs_parts.append(seg)
                abstract = "".join(abs_parts)
                if len(abstract) < 100:
                    abstract = f"研究探讨{title}的相关内容"
                journal = article.findtext(".//journal-title") or ""
                pubdate = article.findtext(".//pub-date/year") or ""
                results.append({
                    "id": f"PMC_{pmid}" if pmid else f"PMC_{len(results)}",
                    "source_channel": "PMC",
                    "title": title,
                    "authors": "",
                    "journal": journal,
                    "pubdate": pubdate,
                    "content": abstract[:1000],
                    "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{pmid}/",
                })
        except ET.ParseError as e:
            logger.warning(f"PMC XML解析失败: {e}")
            return []
        return results
    except Exception as e:
        logger.warning(f"PMC直采异常: {e}")
        return []


# ============================================================
# 四c、Trip Database 循证医学数据库
# ============================================================
def search_trip_database(query: str, max_results: int = 5) -> List[dict]:
    """Trip Database 循证医学文献检索（需要 API Key，未配置时优雅跳过）"""
    api_key = settings.TRIP_DATABASE_API_KEY
    if not api_key:
        logger.info("未配置 TRIP_DATABASE_API_KEY，跳过 Trip Database 数据源")
        return []
    try:
        resp = requests.get(
            "https://www.tripdatabase.com/api/articles/search",
            params={"query": query, "key": api_key, "page": 1,
                    "pageSize": max_results, "type": "EvidenceBasedSynopses"},
            timeout=20)
        if resp.status_code != 200:
            return []
        data = resp.json()
        results = []
        for item in data.get("results", []) or []:
            title = item.get("title", "")
            if not title:
                continue
            abstract = item.get("abstractText", "") or ""
            if len(abstract) < 100:
                abstract = f"循证医学文献探讨{title}的相关证据"
            results.append({
                "id": f"TRIP_{item.get('id', hashlib.md5(title.encode()).hexdigest()[:10])}",
                "source_channel": "Trip-Database",
                "title": title,
                "authors": (item.get("authors") or "")[:150],
                "journal": item.get("journal", ""),
                "pubdate": item.get("publicationDate", "")[:4],
                "content": abstract[:1000],
                "url": item.get("url", ""),
            })
        return results
    except Exception as e:
        logger.warning(f"Trip Database异常: {e}")
        return []


# ============================================================
# 五、官方权威指南补充（手工整理）
# ============================================================
def get_extra_official_cards() -> List[dict]:
    """补充更多权威指南/共识"""
    cards = [
        # 中华医学会指南
        {
            "id": "CMA_DIABETES_2022",
            "source_channel": "中华医学会指南",
            "title": "中国2型糖尿病防治指南(2022版)",
            "authors": "中华医学会糖尿病学分会",
            "journal": "中华糖尿病杂志",
            "pubdate": "2022",
            "content": """【核心循证结论】中国2型糖尿病防治指南建议采用以患者为中心的个体化治疗策略。生活方式干预是基础，包括医学营养治疗(MNT)和运动治疗。推荐糖尿病前期人群进行生活方式干预，可降低2型糖尿病发生风险约40-60%。
【量化临床数据】成人糖尿病患者每日碳水化合物占总能量50-65%，蛋白质15-20%，脂肪20-30%。膳食纤维25-30g/天。限盐<5g/天。每周≥150分钟中等强度有氧运动+2次抗阻训练。HbA1c控制目标一般<7.0%，年轻无并发症可<6.5%。
【适用人群】2型糖尿病及糖尿病前期患者
【局限性/学术争议】老年、有严重并发症者目标可放宽至<8.0%。低碳水饮食(<26%)的长期安全性需更多证据。生酮饮食不常规推荐。""",
            "url": "https://rs.yiigle.com/cmaid/1370574",
            "is_official_guide": True,
            "group": "糖尿病患者",
            "topic": "糖尿病医学营养治疗",
        },
        {
            "id": "CMA_HYPERTENSION_2023",
            "source_channel": "中华医学会指南",
            "title": "中国高血压防治指南(2023版)",
            "authors": "中国高血压防治指南修订委员会",
            "journal": "中华高血压杂志",
            "pubdate": "2023",
            "content": """【核心循证结论】中国高血压防治指南推荐非药物干预为高血压治疗的基础。DASH饮食可降低收缩压8-14mmHg，限盐(<5g/天)可降低4-5mmHg，限酒、减重、运动均有明确降压效果。
【量化临床数据】推荐DASH饮食：富含水果、蔬菜、全谷物、低脂乳制品，减少饱和脂肪和胆固醇。钠<2000mg/天(≈5g盐)，钾3500-4700mg/天。BMI<24kg/m²。每周5-7次、每次30分钟中等强度运动。男性酒精<25g/天，女性<15g/天。
【适用人群】高血压患者及高危人群
【局限性/学术争议】不同人群对盐敏感性差异大。极低钠摄入(<1.5g/天)的安全性有争议。肾功能不全者钾摄入需个体化。""",
            "url": "https://rs.yiigle.com/cmaid/1020031",
            "is_official_guide": True,
            "group": "高血压患者",
            "topic": "高血压DASH饮食实践",
        },
        {
            "id": "CMA_OBESE_2022",
            "source_channel": "中华医学会指南",
            "title": "中国超重/肥胖医学营养治疗指南(2022)",
            "authors": "中国营养学会肥胖预防与控制分会",
            "journal": "中华内分泌代谢杂志",
            "pubdate": "2022",
            "content": """【核心循证结论】推荐限能量平衡膳食(CRD)、高蛋白饮食、轻断食等多种医学营养干预模式。CRD在目标能量基础上减少30%(约500-750kcal/天)，可有效减重并改善代谢。
【量化临床数据】CRD：每日能量减少500-750kcal，三大营养素比例平衡。高蛋白饮食：蛋白质1.2-1.5g/kg(占比20-30%)。5+2轻断食：非断食日正常饮食，断食日500-600kcal。减重目标：6个月减5-10%初始体重。BMI≥28为肥胖，24-28为超重。
【适用人群】超重和肥胖成人(BMI≥24)
【局限性/学术争议】极低能量饮食(<800kcal/天)需医学监督。长期生酮饮食安全性证据不足。代餐食品不能完全替代正餐。""",
            "url": "https://rs.yiigle.com/cmaid/1363727",
            "is_official_guide": True,
            "group": "普通人",
            "topic": "超重肥胖医学营养治疗",
        },
        {
            "id": "CMA_OSTEOPOROSIS_2023",
            "source_channel": "中华医学会指南",
            "title": "原发性骨质疏松症诊疗指南(2023)",
            "authors": "中华医学会骨质疏松和骨矿盐疾病分会",
            "journal": "中华骨质疏松和骨矿盐疾病杂志",
            "pubdate": "2023",
            "content": """【核心循证结论】骨质疏松防治的基础是充足钙和维生素D摄入、规律负重运动和防跌倒。50岁以上人群每日钙摄入推荐1000-1200mg，维生素D 800-1200IU。
【量化临床数据】成人钙RNI 800mg/天，50岁以上1000-1200mg/天。维生素D 400-800IU/天(缺乏者800-2000IU)。绝经后女性和50岁以上男性为高危人群。双能X线骨密度(DXA)T值≤-2.5诊断为骨质疏松。负重运动每周≥3次，每次30分钟。
【适用人群】绝经后女性、50岁以上男性、骨质疏松患者
【局限性/学术争议】单独补钙对骨折预防效果有限，需联合维生素D。钙补充剂可能增加肾结石风险。维生素D最佳水平(20ng/ml vs 30ng/ml)有争议。""",
            "url": "https://rs.yiigle.com/cmaid/1402541",
            "is_official_guide": True,
            "group": "更年期女性",
            "topic": "更年期钙与骨密度",
        },
        # WCRF 肿瘤预防
        {
            "id": "WCRF_CANCER_2018",
            "source_channel": "WCRF国际权威报告",
            "title": "WCRF/AICR饮食、营养、身体活动与癌症预防全球报告(2018第三版)",
            "authors": "World Cancer Research Fund International",
            "journal": "WCRF Continuous Update Project",
            "pubdate": "2018",
            "content": """【核心循证结论】WCRF提出10项癌症预防建议：保持健康体重、多运动、吃富含全谷物蔬菜水果豆类、限制快餐高脂高糖、限制红肉(<500g/周)、避免加工肉、限制含糖饮料、限制酒精、不依赖补剂、母乳喂养。
【量化临床数据】BMI维持在21-23(亚洲<23)。每周至少150分钟中等强度运动。每日≥400g蔬菜水果。红肉<500g/周(熟重)，加工肉尽量不吃。男性酒精<25g/天，女性<15g/天。母乳喂养6个月可降低母亲乳腺癌风险。遵循建议可降低癌症风险约30-40%。
【适用人群】所有成人，特别是肿瘤高风险人群
【局限性/学术争议】特定营养素(如维生素E、硒)的化学预防证据不足。有机食品与癌症风险关系不明确。咖啡与某些癌症(肝癌、子宫内膜癌)风险降低相关。""",
            "url": "https://www.wcrf.org/diet-activity-and-cancer/",
            "is_official_guide": True,
            "group": "肿瘤预防人群",
            "topic": "肿瘤预防膳食模式",
        },
        # 中国居民膳食指南
        {
            "id": "CDG_CHINA_2022",
            "source_channel": "中国居民膳食指南",
            "title": "中国居民膳食指南(2022)核心准则",
            "authors": "中国营养学会",
            "journal": "人民卫生出版社",
            "pubdate": "2022",
            "content": """【核心循证结论】中国居民膳食指南2022提出8项核心准则：食物多样合理搭配、吃动平衡健康体重、多吃蔬果奶豆全谷、适量吃鱼禽蛋瘦肉、少盐少油控糖限酒、规律进餐足量饮水、会烹会选会看标签、公筷分餐杜绝浪费。
【量化临床数据】成人每日：谷薯类200-300g(含全谷杂豆50-150g)、蔬菜≥300g(深色占1/2)、水果200-350g、奶及奶制品300-500g、大豆及坚果25-35g、动物性食物120-200g(每周鱼类2次)、油25-30g、盐<5g、糖<25g(添加糖)、水1500-1700ml。每周累计≥150分钟中等强度运动。BMI 18.5-23.9。
【适用人群】2岁以上健康人群
【局限性/学术争议】不同地区饮食习惯差异大需本地化调整。特殊人群(孕妇、婴幼儿、老人)有专门指南。膳食指南不针对疾病治疗。""",
            "url": "http://dg.cnsoc.org/",
            "is_official_guide": True,
            "group": "普通人",
            "topic": "中国居民膳食指南",
        },
        # 中国孕期妇女指南
        {
            "id": "CDG_PREGNANCY_2022",
            "source_channel": "中国居民膳食指南",
            "title": "中国孕期妇女膳食指南(2022)",
            "authors": "中国营养学会",
            "journal": "人民卫生出版社",
            "pubdate": "2022",
            "content": """【核心循证结论】孕期营养指南核心：补充叶酸、常吃含铁食物、保证主食(含全谷物)、适量奶制品、适度运动、戒烟戒酒。孕中晚期适当增加食物量。
【量化临床数据】孕早期：叶酸400μg/天(从孕前3个月开始)。孕中晚期：每日增加能量300-450kcal，蛋白质15-30g。钙1000-1200mg/天，铁24-29mg/天。每周2-3次鱼类(含DHA)。孕中晚期适度运动30分钟/天。孕期体重增长：正常BMI增8-14kg，超重7-11kg，肥胖5-9kg。
【适用人群】备孕及孕期女性
【局限性/学术争议】叶酸MTHFR基因突变者建议活性叶酸。多胎妊娠营养需求更高。妊娠期糖尿病需个体化饮食方案。""",
            "url": "http://dg.cnsoc.org/",
            "is_official_guide": True,
            "group": "孕妇",
            "topic": "孕期膳食指南",
        },
        # 中国老年人膳食指南
        {
            "id": "CDG_ELDERLY_2022",
            "source_channel": "中国居民膳食指南",
            "title": "中国老年人膳食指南(2022)",
            "authors": "中国营养学会",
            "journal": "人民卫生出版社",
            "pubdate": "2022",
            "content": """【核心循证结论】老年人膳食核心：食物品种丰富、主动足量饮水、规律进餐、摄入充足动物性食物、鼓励户外活动、定期测量体重预防肌少症和营养不良。
【量化临床数据】65岁以上每日：食物品种≥12种/天(每周≥25种)。蛋白质1.0-1.2g/kg(预防肌少症1.2-1.5g/kg)。水1500-1700ml(主动饮水)。奶制品300-400g。动物性食物120-150g。每周≥150分钟中等强度运动+2次抗阻训练+3次平衡训练。BMI 20.0-26.9(略宽于成人)。
【适用人群】65岁及以上老年人
【局限性/学术争议】咀嚼吞咽功能下降者需调整食物质地。多种慢性病者需个体化方案。维生素D补充对老年人尤为重要(缺乏率>40%)。""",
            "url": "http://dg.cnsoc.org/",
            "is_official_guide": True,
            "group": "老年人",
            "topic": "老年人膳食指南",
        },
        # 中国婴幼儿喂养指南
        {
            "id": "CDG_INFANT_2022",
            "source_channel": "中国居民膳食指南",
            "title": "中国婴幼儿喂养指南(2022)",
            "authors": "中国营养学会",
            "journal": "人民卫生出版社",
            "pubdate": "2022",
            "content": """【核心循证结论】0-6月龄：纯母乳喂养。6-12月龄：继续母乳，逐步添加辅食。1-3岁：均衡饮食，培养良好饮食习惯。
【量化临床数据】0-6月龄：纯母乳喂养，按需哺乳(每日8-12次)。6月龄起添加富含铁的辅食(强化铁米粉、肉泥)。7-12月龄：每日奶量600-800ml，逐渐过渡到3餐+2加餐。1-3岁：每日奶量350-500g，3餐+2加餐，食物多样化(每周≥12种)。
【适用人群】0-3岁婴幼儿及其照护者
【局限性/学术争议】无法母乳喂养者选择配方奶。辅食添加顺序近年观点从"谷物优先"转向"铁丰富食物优先"。1岁内不加盐糖。""",
            "url": "http://dg.cnsoc.org/",
            "is_official_guide": True,
            "group": "普通人",
            "topic": "婴幼儿喂养指南",
        },
    ]
    return cards


# ============================================================
# 六、知识卡片生成
# ============================================================
def make_card_from_literature(mat: dict, group: str, topic: str) -> Optional[dict]:
    content = mat.get("content", "") or ""
    if len(content) < 100:
        return None
    truncated = content[:480]
    card_id = mat.get("id", "")
    if not card_id:
        raw = f"{mat.get('title','')}_{group}_{topic}"
        card_id = f"LIT_{hashlib.md5(raw.encode()).hexdigest()[:10]}"
    return {
        "card_id": card_id,
        "title": mat.get("title", ""),
        "group": group,
        "topic": topic,
        "source_channel": mat.get("source_channel", "未知"),
        "source_url": mat.get("url", ""),
        "authors": mat.get("authors", ""),
        "journal": mat.get("journal", ""),
        "pubdate": mat.get("pubdate", ""),
        "purified_content": truncated,
        "is_official_guide": mat.get("is_official_guide", False),
        "ingest_time": datetime.now().isoformat(),
        "version": 1,
    }


def make_card_from_official(card_data: dict) -> dict:
    return {
        "card_id": card_data["id"],
        "title": card_data["title"],
        "group": card_data.get("group", "普通人"),
        "topic": card_data.get("topic", "通用营养"),
        "source_channel": card_data.get("source_channel", "官方指南"),
        "source_url": card_data.get("url", ""),
        "authors": card_data.get("authors", ""),
        "journal": card_data.get("journal", ""),
        "pubdate": card_data.get("pubdate", ""),
        "purified_content": card_data["content"],
        "is_official_guide": card_data.get("is_official_guide", True),
        "ingest_time": datetime.now().isoformat(),
        "version": 1,
    }


# ============================================================
# 七、去重（V2: 四层去重漏斗，由 services/kb_dedup_service 统一提供）
#     层1 group+topic 元数据硬过滤 → 层2 BGE 向量余弦 → 层3 分级策略 → 层4 双层存储
# ============================================================


# ============================================================
# 八、入库
# ============================================================
CROWD_MAP = {
    "健身人群": "健身人群", "老年人": "老年人", "孕妇": "孕妇",
    "青少年": "青少年", "糖尿病患者": "糖尿病患者", "普通人": "普通人",
    "高血压患者": "高血压患者", "心血管患者": "心血管患者",
    "肿瘤预防人群": "肿瘤预防人群", "素食人群": "素食人群",
    "更年期女性": "更年期女性",
}


def ingest_to_chromadb(cards: List[dict], retriever) -> int:
    """文献入库：四层去重漏斗 + 双层存储（由 KBDedupService.check_literature_ingest 驱动）"""
    from services.kb_dedup_service import KBDedupService

    dedup_svc = KBDedupService(retriever=retriever, llm=None)
    existing_ids = set()
    try:
        all_meta = retriever.collection.get(include=["metadatas"])
        for m in all_meta.get("metadatas", []) or []:
            cid = m.get("card_id", "")
            if cid:
                existing_ids.add(cid)
    except Exception:
        pass
    print(f"  已有卡片: {len(existing_ids)} 张")

    new_cards = []
    dropped = 0
    for card in cards:
        cid = card["card_id"]
        if cid in existing_ids:
            dropped += 1
            continue
        # 组装文档（展示版/完整版双层拆分在服务内部处理）
        doc = f"【标题】{card['title']}\n【来源】{card.get('source_channel','')}\n{card['purified_content']}"
        display_doc, full_doc = dedup_svc._split_dual_layer(doc)
        crowd = CROWD_MAP.get(card.get("group", "普通人"), "普通人")
        category = "crowd_specific"
        if card.get("is_official_guide"):
            category = "dietary_guideline"
        if card.get("group") == "普通人":
            category = "nutrition_standard"
        meta = {
            "category": category,
            "source": card.get("source_channel", ""),
            "target_crowd": crowd,
            "card_id": cid,
            "group": card.get("group", "普通人"),
            "topic": card.get("topic", ""),
            "source_channel": card.get("source_channel", ""),
            "source_url": card.get("source_url", ""),
            "is_official_guide": "True" if card.get("is_official_guide") else "False",
            "source_type": "literature",
            "journal": card.get("journal", ""),
            "pubdate": card.get("pubdate", ""),
        }
        meta = {k: v for k, v in meta.items() if v is not None and v != ""}

        result = dedup_svc.check_literature_ingest(
            card=card, display_doc=display_doc, full_doc=full_doc,
            meta=meta, doc_id=cid,
        )
        if result["action"] in ("new", "variant"):
            new_cards.append(cid)
        else:
            dropped += 1

    print(f"  去重后需导入: {len(new_cards)} 张（丢弃 {dropped} 张重复）")
    return len(new_cards)


# ============================================================
# 九、主流程
# ============================================================
def main():
    import argparse
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(description="向量知识库扩展完善V2")
    parser.add_argument("--skip-pubmed", action="store_true")
    parser.add_argument("--skip-ss", action="store_true")
    parser.add_argument("--skip-pmc", action="store_true")
    parser.add_argument("--skip-pmc-direct", action="store_true")
    parser.add_argument("--skip-trip", action="store_true")
    parser.add_argument("--skip-official", action="store_true")
    parser.add_argument("--max-per-topic", type=int, default=5)
    args = parser.parse_args()

    print("=" * 70)
    print("向量知识库扩展完善V2")
    print(f"主题数: {len(EXTENDED_TOPICS)}")
    print("=" * 70)

    all_cards = []

    # 1. PubMed 直采
    if not args.skip_pubmed:
        print("\n【1】PubMed 直采")
        cnt = 0
        for topic in EXTENDED_TOPICS:
            print(f"\n  [{topic['group']}] {topic['topic']}")
            for kw in topic["keywords"]:
                results = search_pubmed_direct(kw, max_results=args.max_per_topic // 2 + 1)
                print(f"    {kw[:50]}... → {len(results)}篇")
                for mat in results:
                    card = make_card_from_literature(mat, topic["group"], topic["topic"])
                    if card:
                        all_cards.append(card)
                        cnt += 1
                time.sleep(0.4)
        print(f"\n  PubMed 小计: {cnt} 张")

    # 2. Semantic Scholar
    if not args.skip_ss:
        print("\n【2】Semantic Scholar")
        cnt = 0
        for topic in EXTENDED_TOPICS:
            print(f"\n  [{topic['group']}] {topic['topic']}")
            for kw in topic["keywords"]:
                results = search_semantic_scholar(kw, max_results=args.max_per_topic // 2 + 1)
                print(f"    {kw[:50]}... → {len(results)}篇")
                for mat in results:
                    card = make_card_from_literature(mat, topic["group"], topic["topic"])
                    if card:
                        all_cards.append(card)
                        cnt += 1
                time.sleep(1.0)  # Semantic Scholar 限流更严格
        print(f"\n  Semantic Scholar 小计: {cnt} 张")

    # 3. Europe-PMC（扩展主题）
    if not args.skip_pmc:
        print("\n【3】Europe-PMC 扩展主题")
        cnt = 0
        for topic in EXTENDED_TOPICS:
            print(f"\n  [{topic['group']}] {topic['topic']}")
            for kw in topic["keywords"]:
                results = search_europepmc(kw, max_results=args.max_per_topic // 2 + 1)
                print(f"    {kw[:50]}... → {len(results)}篇")
                for mat in results:
                    card = make_card_from_literature(mat, topic["group"], topic["topic"])
                    if card:
                        all_cards.append(card)
                        cnt += 1
                time.sleep(0.5)
        print(f"\n  Europe-PMC 小计: {cnt} 张")

    # 4. PMC 全文库直采
    if not args.skip_pmc_direct:
        print("\n【4】PMC 全文库直采")
        cnt = 0
        for topic in EXTENDED_TOPICS:
            print(f"\n  [{topic['group']}] {topic['topic']}")
            for kw in topic["keywords"]:
                results = search_pmc_direct(kw, max_results=args.max_per_topic // 2 + 1)
                print(f"    {kw[:50]}... → {len(results)}篇")
                for mat in results:
                    card = make_card_from_literature(mat, topic["group"], topic["topic"])
                    if card:
                        all_cards.append(card)
                        cnt += 1
                time.sleep(0.5)  # 遵守 NCBI 每秒 ≤3 次的限速要求
        print(f"\n  PMC 小计: {cnt} 张")

    # 5. Trip Database 循证医学库
    if not args.skip_trip:
        print("\n【5】Trip Database 循证医学库")
        cnt = 0
        for topic in EXTENDED_TOPICS:
            print(f"\n  [{topic['group']}] {topic['topic']}")
            for kw in topic["keywords"]:
                results = search_trip_database(kw, max_results=args.max_per_topic // 2 + 1)
                print(f"    {kw[:50]}... → {len(results)}篇")
                for mat in results:
                    card = make_card_from_literature(mat, topic["group"], topic["topic"])
                    if card:
                        all_cards.append(card)
                        cnt += 1
                time.sleep(1.0)
        print(f"\n  Trip Database 小计: {cnt} 张")

    # 6. 官方权威指南
    if not args.skip_official:
        print("\n【6】官方权威指南（手工整理）")
        official_cards = get_extra_official_cards()
        for c in official_cards:
            all_cards.append(make_card_from_official(c))
        print(f"  官方指南: {len(official_cards)} 张")

    print(f"\n{'=' * 70}")
    print(f"总计生成卡片: {len(all_cards)} 张")
    print(f"{'=' * 70}")

    # 统计
    by_source, by_group = {}, {}
    for c in all_cards:
        s = c.get("source_channel", "未知")
        by_source[s] = by_source.get(s, 0) + 1
        g = c.get("group", "未知")
        by_group[g] = by_group.get(g, 0) + 1
    print("\n按来源:")
    for k, v in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print("\n按人群:")
    for k, v in sorted(by_group.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    # 入库
    print(f"\n{'=' * 70}")
    print("【5】入库 ChromaDB")
    print(f"{'=' * 70}")
    try:
        from vector.retriever import retriever
    except ImportError as e:
        print(f"⚠️ 无法导入 retriever: {e}")
        return

    before = retriever.count()
    print(f"导入前: {before} 条")
    imported = ingest_to_chromadb(all_cards, retriever)
    after = retriever.count()
    print(f"\n导入完成: 新增 {imported} 条")
    print(f"导入后: {after} 条 (净增 {after - before})")

    # 保存
    output_path = os.path.join(AI_DIR, "knowledge_base", "enriched_cards_v2.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_cards, f, ensure_ascii=False, indent=2)
    print(f"\n新增卡片已保存: {output_path}")

    print(f"\n{'=' * 70}")
    print("向量知识库扩展完善V2完成")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
