# -*- coding: utf-8 -*-
"""
v3.2 双模型流水线 — 母稿生成（本地Ollama搭框架 + 云端API外扩）
============================================================
Stage 1: Ollama本地大模型 + 向量知识库 → 搭建母稿框架
Stage 2: DeepSeek云端API + 联网搜索 → 外扩补强
Stage 3: Ollama本地大模型 → 格式校验

Ollama未就绪时，Stage 1/3自动降级为云端API
"""
import sys
import os
import json
import time
import re
import requests
from datetime import datetime

# 路径设置
AI_SERVICE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AI_SERVICE_DIR)
os.chdir(AI_SERVICE_DIR)

from config.settings import settings

# ======================== 配置 ========================
# 云端API
DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
DEEPSEEK_API_BASE = settings.DEEPSEEK_API_BASE or "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = settings.DEEPSEEK_MODEL or "deepseek-chat"

# Ollama本地API
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-7b-q4km")  # 本地导入的gguf模型（D盘存储）

# 本地模型上下文自适应策略：优先8192，资源不足自动降级（6G显存兜底2048）
# 说明：4096上下文对"素材+完整框架输出"不足（实测生成截断），故提到8192；
#      本机Ollama在超大上下文下可通过CPU卸载兜底运行，8192可稳定跑通。
NUM_CTX_TIERS = [8192, 6144, 4096, 2048]    # 从高到低的档位
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))  # 目标上下文（可用环境变量覆盖）
# 资源不足类错误（显存/OOM等）→ 降级到更小上下文可缓解
_RESOURCE_ERR_MSG = ("memory", "oom", "vram", "allocation", "no space", "capacity", "resource")
# 提示词超长类错误（prompt超过上下文长度）→ 降级只会更糟，直接失败
_PROMPT_TOO_LONG_MSG = ("exceeds maximum context", "context length", "prompt token count",
                        "too long", "sequence too long", "window too small")

# 输出目录（D盘，避免C盘空间不足）
OUTPUT_DIR = os.getenv("PIPELINE_OUTPUT_DIR", os.path.join(AI_SERVICE_DIR, "test_results", "v32_pipeline"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ======================== Ollama可用性检测 ========================
def check_ollama():
    """检测Ollama是否可用"""
    try:
        resp = requests.get(f"{OLLAMA_API_BASE}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            print(f"  ✓ Ollama可用，已安装模型：{model_names}")
            if OLLAMA_MODEL not in str(model_names):
                print(f"  ⚠ 目标模型 {OLLAMA_MODEL} 未安装，可用的有：{model_names}")
                if model_names:
                    return True, model_names[0]  # 用第一个可用模型
            return True, OLLAMA_MODEL
        return False, None
    except Exception as e:
        print(f"  ✗ Ollama不可用：{e}")
        return False, None


# ======================== 本地大模型调用（Ollama） ========================
def call_ollama(prompt, system, model_name, tracker, label, temp=0.3, max_tokens=1200):
    """
    调用Ollama本地大模型，num_ctx自适应降级策略：
      优先使用目标上下文（默认4096），若显存/资源不足则自动降到3072→2048。
    返回生成内容；全部档位失败返回None。
    """
    headers = {"Content-Type": "application/json"}
    # 构建档位列表：不超过目标值，从高到低
    tiers = [c for c in NUM_CTX_TIERS if c <= OLLAMA_NUM_CTX] or [NUM_CTX_TIERS[-1]]
    last_err = None
    for num_ctx in tiers:
        payload = {
            "model": model_name,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temp, "num_predict": max_tokens, "num_ctx": num_ctx}
        }
        for attempt in range(2):
            try:
                resp = requests.post(f"{OLLAMA_API_BASE}/api/chat",
                                   headers=headers, json=payload, timeout=300)
                data = resp.json()
                if resp.status_code != 200:
                    raise RuntimeError(data.get("error", f"HTTP {resp.status_code}"))
                content = data.get("message", {}).get("content", "")
                # Ollama不返回token统计，用字符数估算
                est_tokens = len(content) // 3
                tracker["total"] += est_tokens
                tracker["calls"] += 1
                tracker["local_calls"] += 1
                return content
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                # 提示词超长：降级只会更糟（更小上下文更放不下），直接失败
                if any(k in msg for k in _PROMPT_TOO_LONG_MSG):
                    print(f"    ✗ [{label}] 提示词超过num_ctx={num_ctx}长度：{e}")
                    return None
                # 资源不足类错误（显存/OOM/上下文容量）→ 立即降级到更小的档位
                if any(k in msg for k in _RESOURCE_ERR_MSG):
                    print(f"    ⚠ [{label}] num_ctx={num_ctx} 资源不足（{e}），自动降级上下文...")
                    break
                if attempt < 1:
                    time.sleep(2)
                else:
                    print(f"    ✗ Ollama调用失败[{label}] num_ctx={num_ctx}：{e}")
                    break
    print(f"    ✗ Ollama全部档位失败[{label}]：{last_err}")
    return None


# ======================== 云端API调用 ========================
def call_cloud(prompt, system, tracker, label, temp=0.7, max_tokens=3000):
    """调用DeepSeek云端API"""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": prompt}],
        "temperature": temp,
        "max_tokens": max_tokens
    }
    for attempt in range(3):
        try:
            resp = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions",
                               headers=headers, json=payload, timeout=180)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            tracker["total"] += usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)
            tracker["calls"] += 1
            tracker["cloud_calls"] += 1
            return content
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                print(f"    ✗ 云端调用失败[{label}]：{e}")
                return None


# ======================== 向量知识库检索 ========================
# 细分人群补充检索：大主题文章（如"青少年饮食"）需在内部章节覆盖细分人群，
# 主查询往往命中不足细分卡片，故按 sub_group 元数据精确拉取各细分人群卡片。
# 键为人群分组，值为该人群的细分人群标签（与知识库卡片 sub_group 字段对应）。
SUB_GROUP_LABELS = {
    "青少年": ["普通青少年", "体育特长生", "素食人群", "乳糖不耐受", "肥胖青少年", "睡眠运动指南"],
    # 预留：其他人群细分标签完善后在此扩展
    # "老年人": [...], "糖尿病患者": [...]
}

def retrieve_from_kb(query, group, top_n=10):
    """从ChromaDB检索知识卡片（主查询 + 细分人群补充检索，细分卡片优先）"""
    try:
        from vector.retriever import retriever
        
        crowd_mapping = {
            "普通人": "普通人", "健身用户": "健身人群", "孕妇": "孕妇",
            "青少年": "青少年", "老年人": "老年人", "糖尿病患者": "糖尿病患者"
        }
        target_crowd = crowd_mapping.get(group, None)
        
        results = retriever.hybrid_retrieve(query, top_k=top_n, target_crowd=target_crowd)
        
        # 细分人群补充检索：按 sub_group 元数据精确拉取，确保细分章节素材充足
        for sg_label in SUB_GROUP_LABELS.get(group, []):
            try:
                sg_docs = retriever.collection.get(
                    where={"sub_group": sg_label}, include=["documents", "metadatas"])
                docs = sg_docs.get("documents", []) or []
                metas = sg_docs.get("metadatas", []) or []
                for doc, meta in zip(docs, metas):
                    results.append({"content": doc, "similarity": 0.99, "metadata": meta})
            except Exception:
                continue
        
        cards = []
        seen_card_ids = set()
        for r in results:
            meta = r.get("metadata", {})
            # 从文档内容中解析原文标题（文档格式：【标题】xxx\n内容...）
            content = r.get("content", "")
            orig_title_m = re.match(r"【标题】(.+?)(?:\n|$)", content)
            orig_title = orig_title_m.group(1).strip() if orig_title_m else ""
            # 只取有card_id的（即我们导入的知识卡片）
            if meta.get("card_id"):
                cid = meta.get("card_id", "")
                if cid and cid in seen_card_ids:
                    continue
                if cid:
                    seen_card_ids.add(cid)
                cards.append({
                    "card_id": cid,
                    "title": meta.get("topic", "") or orig_title or content[:50],
                    "content": content,
                    "group": meta.get("group", ""),
                    "sub_group": meta.get("sub_group", ""),   # 细分人群标签（如：体育特长生/素食人群/乳糖不耐受）
                    "source_channel": meta.get("source_channel", ""),   # 来源渠道：PubMed/官方指南
                    "source_type": meta.get("source_type", "向量知识库"),  # 来源类型
                    "orig_title": orig_title,                          # 原文标题（文献真实标题）
                    "journal": meta.get("journal", ""),                # 期刊/指南名
                    "authors": meta.get("authors", ""),
                    "pubdate": meta.get("pubdate", ""),
                    "source_url": meta.get("source_url", ""),          # 原文链接（可溯源）
                    "ingest_time": meta.get("ingest_time", ""),        # 入库时间
                    "similarity": r.get("similarity", 0)
                })
            else:
                # 旧数据也保留（来源取meta.source，如"中国居民膳食指南2022"）
                cards.append({
                    "card_id": meta.get("source", "legacy"),
                    "title": meta.get("source", ""),
                    "content": content,
                    "group": "",
                    "sub_group": meta.get("sub_group", ""),
                    "source_channel": meta.get("source", "本地知识库"),
                    "source_type": "向量知识库",
                    "orig_title": orig_title,
                    "journal": meta.get("source", ""),
                    "authors": "",
                    "pubdate": "",
                    "source_url": meta.get("source_url", ""),
                    "ingest_time": meta.get("ingest_time", ""),
                    "similarity": r.get("similarity", 0)
                })
        
        # 按标题二次去重（同一主题多张相似卡片时保留相似度最高者）
        seen_titles = {}
        for c in cards:
            title = c.get("title", "") or ""
            if title and title in seen_titles:
                if c.get("similarity", 0) > seen_titles[title].get("similarity", 0):
                    seen_titles[title] = c
            else:
                seen_titles[title] = c
        cards = list(seen_titles.values())

        # 通用与细分卡片交错排序：主体素材（通用）与细分章节素材（细分）均衡进入Stage1
        # 模式：通用2张 + 细分2张 交替，保证"大主题为主 + 细分章节为辅"的素材结构
        general = [c for c in cards if not c.get("sub_group")]
        subs = [c for c in cards if c.get("sub_group")]
        general.sort(key=lambda c: -c.get("similarity", 0))
        subs.sort(key=lambda c: -c.get("similarity", 0))
        merged = []
        gi, si = 0, 0
        while gi < len(general) and si < len(subs):
            merged.append(general[gi]); gi += 1
            if gi < len(general):
                merged.append(general[gi]); gi += 1
            merged.append(subs[si]); si += 1
        merged.extend(general[gi:])
        merged.extend(subs[si:])
        return merged[:top_n * 2]
    except Exception as e:
        print(f"  ✗ 知识库检索失败：{e}")
        return []


# ======================== 文献联网搜索（多源回退） ========================
# 搜索链：PubMed → Europe-PMC → Semantic Scholar → Crossref
#   - 任一源请求失败（国内网络对 NCBI 常超时，且旧代码 except: return [] 静默吞异常）
#     自动切换到下一源，避免"联网文献恒为 0"导致 Stage2 无 PMID 白名单可用
#   - 每个源返回 (items, ok, error)：ok=False=网络不可达可切源；ok=True=API已响应
#   - 统一文献结构含 pmid/doi 字段：有 PMID 用 PMID 溯源；无 PMID 保留 DOI，禁止模型编造 PMID
_LIT_TIMEOUT = 10          # 单源单请求超时（秒），快速失败以切源
_LIT_HEADERS = {"User-Agent": "HealthAssistant/1.0 (mailto:health-assistant@local)"}
LITERATURE_SOURCES = ["PubMed", "Europe-PMC", "Semantic Scholar", "Crossref"]


def _fetch_json(url, params, timeout=_LIT_TIMEOUT, headers=None):
    """GET 请求并解析 JSON。返回 (data, error)；error=None 表示成功。"""
    try:
        resp = requests.get(url, params=params, timeout=timeout,
                            headers=headers or _LIT_HEADERS)
        if resp.status_code != 200:
            return None, f"HTTP {resp.status_code}"
        return resp.json(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _normalize_literature(id_, title, authors, journal, pubdate, content,
                          source_api, pmid="", doi="", url=""):
    """统一文献素材结构，补齐 pmid/doi 字段便于 PMID 白名单与溯源。"""
    if not pmid and id_.startswith("PMID_"):
        pmid = id_[5:]
    if not doi and id_.startswith("DOI_"):
        doi = id_[4:]
    return {
        "id": id_, "pmid": pmid, "doi": doi,
        "title": title or "", "authors": authors or "",
        "journal": journal or "", "pubdate": str(pubdate or ""),
        "content": content or "", "source_api": source_api,
        "source_channel": source_api, "url": url or "",
    }


def search_pubmed_online(keyword, max_results=4, exclude_ids=None):
    """PubMed E-utilities（主源）：esearch + esummary 两跳即返回。
    不做 efetch 摘要二次拉取（NCBI 国内常超时，摘要非白名单机制必需）。"""
    data, err = _fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        {"db": "pubmed", "term": keyword, "retmax": max_results,
         "retmode": "json", "sort": "relevance"})
    if err:
        return [], False, f"PubMed不可达（{err}）"
    pmids = data.get("esearchresult", {}).get("idlist", []) or []
    if not pmids:
        return [], True, "无结果"
    sdata, serr = _fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
        {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
    if serr:
        return [], False, f"PubMed esummary失败（{serr}）"
    result = sdata.get("result", {}) or {}
    items = []
    for pmid in pmids:
        a = result.get(pmid, {}) or {}
        title = a.get("title", "")
        if not title:
            continue
        authors = ", ".join([x.get("name", "") for x in (a.get("authors") or [])[:3]])
        items.append(_normalize_literature(
            id_=f"PMID_{pmid}", pmid=pmid, title=title, authors=authors,
            journal=a.get("fulljournalname", ""),
            pubdate=(a.get("pubdate") or "")[:4],
            content=f"研究探讨{title}的相关内容",
            source_api="PubMed",
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"))
    return items, True, None


def search_europepmc_online(keyword, max_results=4, exclude_ids=None):
    """Europe-PMC REST API（回退源1）：单请求即返回摘要+期刊，命中即含真实 PMID。"""
    data, err = _fetch_json(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        {"query": keyword, "format": "json", "pageSize": max_results,
         "resultType": "core", "sort": "P_PDATE_D desc"})
    if err:
        return [], False, f"Europe-PMC不可达（{err}）"
    hits = data.get("resultList", {}).get("result", []) or []
    items = []
    for r in hits:
        pmid = r.get("pmid") or (r.get("id", "") if r.get("source") == "MED" else "")
        if not pmid:
            continue
        jinfo = r.get("journalInfo", {}) or {}
        journal = (jinfo.get("journal", {}) or {}).get("title", "")
        abstract = r.get("abstractText", "") or ""
        if len(abstract) < 100:
            abstract = f"研究探讨{r.get('title', '')}的相关内容"
        items.append(_normalize_literature(
            id_=f"PMID_{pmid}", pmid=pmid, title=r.get("title", ""),
            authors=r.get("authorString", "")[:150], journal=journal,
            pubdate=str(r.get("pubYear", "") or ""), content=abstract[:1000],
            source_api="Europe-PMC", url=f"https://europepmc.org/article/MED/{pmid}"))
    return items, True, None


def search_semanticscholar_online(keyword, max_results=4, exclude_ids=None):
    """Semantic Scholar Graph API（回退源2）：externalIds 含 PubMed 编号时直接作为 PMID。"""
    data, err = _fetch_json(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        {"query": keyword, "limit": max_results,
         "fields": "title,year,venue,authors,abstract,externalIds,tldr"},
        timeout=12)
    if err:
        return [], False, f"Semantic Scholar不可达（{err}）"
    items = []
    for p in data.get("data", []) or []:
        title = p.get("title", "") or ""
        if not title:
            continue
        ext = p.get("externalIds", {}) or {}
        pmid, doi = ext.get("PubMed", "") or "", ext.get("DOI", "") or ""
        if not pmid and not doi:
            continue  # 无 PMID/DOI 的文献无法溯源，丢弃
        tldr = p.get("tldr") or {}
        abstract = tldr.get("text") or p.get("abstract") or ""
        if len(abstract) < 100:
            abstract = f"研究探讨{title}的相关内容"
        authors = ", ".join([a.get("name", "") for a in (p.get("authors") or [])[:3]])
        if pmid:
            lid, url = f"PMID_{pmid}", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        else:
            lid, url = f"DOI_{doi}", f"https://doi.org/{doi}"
        items.append(_normalize_literature(
            id_=lid, pmid=pmid, doi=doi, title=title, authors=authors,
            journal=p.get("venue", "") or "", pubdate=str(p.get("year", "") or ""),
            content=abstract[:1000], source_api="Semantic Scholar", url=url))
    return items, True, None


def _doi_to_pmid(doi):
    """用 Europe-PMC 将 Crossref 的 DOI 解析为 PMID（解析失败返回空串，保留 DOI 溯源）。"""
    data, err = _fetch_json(
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
        {"query": f'DOI:"{doi}" AND SRC:MED', "format": "json", "pageSize": 1},
        timeout=8)
    if err:
        return ""
    hits = data.get("resultList", {}).get("result", []) or []
    return (hits[0].get("pmid", "") or "") if hits else ""


def search_crossref_online(keyword, max_results=4, exclude_ids=None):
    """Crossref REST API（回退源3）：仅含 DOI，逐条尝试解析为 PMID，失败保留 DOI 溯源。"""
    data, err = _fetch_json(
        "https://api.crossref.org/works",
        {"query": keyword, "rows": max_results,
         "select": "DOI,title,author,container-title,issued,abstract,type"})
    if err:
        return [], False, f"Crossref不可达（{err}）"
    items = []
    for it in data.get("message", {}).get("items", []) or []:
        title = (it.get("title") or [""])[0]
        doi = it.get("DOI", "") or ""
        if not title or not doi:
            continue
        journal = (it.get("container-title") or [""])[0]
        year = ""
        dp = ((it.get("issued", {}) or {}).get("date-parts") or [])
        if dp and dp[0]:
            year = str(dp[0][0])
        authors = ", ".join([
            " ".join(x for x in (a.get("given", ""), a.get("family", "")) if x)
            for a in (it.get("author") or [])[:3]])
        abstract = re.sub(r"<[^>]+>", " ", it.get("abstract", "") or "").strip()
        if len(abstract) < 100:
            abstract = f"研究探讨{title}的相关内容"
        pmid = _doi_to_pmid(doi)
        items.append(_normalize_literature(
            id_=f"PMID_{pmid}" if pmid else f"DOI_{doi}", pmid=pmid, doi=doi,
            title=title, authors=authors, journal=journal, pubdate=year,
            content=abstract[:1000], source_api="Crossref",
            url=f"https://doi.org/{doi}"))
        time.sleep(0.3)
    return items, True, None


def search_literature_online(keyword, max_results=3, exclude_ids=None):
    """多源回退联网搜索（PubMed → Europe-PMC → Semantic Scholar → Crossref）。
    任一源网络不可达即切下一源；首个命中的源返回其文献（避免多源噪声）。
    返回 (results, used_source)；used_source 为空表示全部不可达/无结果。"""
    exclude_ids = exclude_ids or set()
    chain = [
        ("PubMed", search_pubmed_online),
        ("Europe-PMC", search_europepmc_online),
        ("Semantic Scholar", search_semanticscholar_online),
        ("Crossref", search_crossref_online),
    ]
    results, seen_pmids, seen_dois, seen_titles = [], set(), set(), set()
    for src_name, fn in chain:
        items, ok, error = fn(keyword, max_results=max_results, exclude_ids=exclude_ids)
        if not ok:
            print(f"    ⚠ [{src_name}] {error}，切换下一源")
            continue
        if not items:
            print(f"    - [{src_name}] 无相关文献")
            continue
        print(f"    ✓ [{src_name}] 命中 {len(items)} 篇")
        added = 0
        for it in items:
            pmid, doi, title = it.get("pmid", ""), it.get("doi", ""), (it.get("title") or "").strip()
            if (pmid and pmid in seen_pmids) or (not pmid and doi and doi in seen_dois) \
               or (not pmid and not doi and title and title in seen_titles):
                continue
            if pmid:
                seen_pmids.add(pmid)
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)
            results.append(it)
            added += 1
        if added > 0:
            return results, src_name
        time.sleep(0.5)
    return results, ""


# ======================== Europe-PMC PMID二次校验（医学专项第二层校验）========================
def verify_pmid_europepmc(pmid):
    """
    通过Europe-PMC API二次校验PMID真实性（第二层校验）。
    聚合PubMed、预印本medRxiv、临床试验数据，兼容PMID/DOI检索。
    返回：True=真实文献 / False=无效 / None=网络失败（不阻断流程）
    """
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json", "pageSize": 1},
            timeout=10
        )
        data = resp.json()
        return data.get("hitCount", 0) > 0
    except Exception as e:
        print(f"    ⚠ Europe-PMC校验网络异常（PMID:{pmid}）：{e}")
        return None


def verify_pmids_in_article(article, verified_pmids_set):
    """
    扫描文章中所有PMID编号，双重校验真实性（方案A+Europe-PMC第二层）：
    第一层：是否在PubMed API已获取的PMID集合中（白名单）
    第二层：不在白名单中的，通过Europe-PMC复核（兼容预印本medRxiv、临床试验）
    两层都校验失败 = 大模型幻觉，自动从参考文献剔除
    """
    # 提取文章中所有PMID编号
    found_pmids = set(re.findall(r'PMID[:_]?\s*(\d{6,9})', article))
    if not found_pmids:
        return article, {"total": 0, "verified": 0, "fake": [], "cleaned": False, "second_check": 0}

    # 第一层：白名单校验（PubMed API已获取的PMID）
    confirmed_pmids = set()
    unconfirmed_pmids = []
    for p in found_pmids:
        if p in verified_pmids_set:
            confirmed_pmids.add(p)
        else:
            unconfirmed_pmids.append(p)

    # 第二层：Europe-PMC复核未确认的PMID（双重排查虚假编号）
    verified_count = len(confirmed_pmids)
    second_check_count = 0
    for p in unconfirmed_pmids:
        second_check_count += 1
        result = verify_pmid_europepmc(p)
        if result is True:
            confirmed_pmids.add(p)
            print(f"  ✓ Europe-PMC复核通过（第二层校验）：PMID:{p}")
        elif result is None:
            # 网络失败，保守放行（进入参考列表但标记待人工核查）
            confirmed_pmids.add(p)
            print(f"  ⚠ Europe-PMC网络失败，PMID:{p} 暂放行待人工核查")

    fake_pmids = [p for p in found_pmids if p not in confirmed_pmids]
    verified_count = len(found_pmids) - len(fake_pmids)

    cleaned_article = article
    if fake_pmids:
        print(f"  ⚠ 发现{len(fake_pmids)}个虚假PMID（大模型幻觉）：PMID_{', PMID_'.join(fake_pmids[:5])}")
        # 从参考文献列表中剔除虚假PMID行
        lines = cleaned_article.split('\n')
        cleaned_lines = []
        for line in lines:
            # 如果该行包含虚假PMID，跳过
            if any(f"PMID_{p}" in line or f"PMID:{p}" in line or f"PMID:{p}" in line for p in fake_pmids):
                print(f"    剔除虚假文献：{line.strip()[:60]}...")
                continue
            cleaned_lines.append(line)
        cleaned_article = '\n'.join(cleaned_lines)

    return cleaned_article, {"total": len(found_pmids), "verified": verified_count,
                              "fake": fake_pmids, "cleaned": len(fake_pmids) > 0,
                              "second_check": second_check_count}


# ======================== 清理占位标记（方案C：参考文献标准化）========================
def clean_placeholders(article):
    """清除[待扩展]等占位标记，替换为实际内容提示或直接移除"""
    placeholders = ['[待扩展]', '【待扩展】', '[待补充]', '【待补充】', '[TODO]', '【TODO】']
    cleaned = article
    for ph in placeholders:
        if ph in cleaned:
            print(f"  清理占位标记：{ph}")
            cleaned = cleaned.replace(ph, '（详见下方深度拓展）')
    return cleaned


# ======================== 参考文献标准化（方案C）========================
def standardize_references(article, web_materials):
    """将参考文献统一为标准格式，确保所有外文文献可溯源"""
    # 找到参考文献区块
    ref_match = re.search(r'【#REF_LIST#】(.*?)(?:【#|$)', article, re.DOTALL)
    if not ref_match:
        return article

    ref_section = ref_match.group(1)
    lines = ref_section.strip().split('\n')

    # 收集所有真实可溯源的参考文献
    ref_items = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('【#'):
            continue
        # 保留有效参考文献行（有序号开头）
        if re.match(r'^\[\d+\]', line):
            ref_items.append(line)

    # 补充联网文献的标准引用格式（APA医学格式）
    # 有 PMID 用 PMID 溯源；无 PMID（如 Crossref 仅 DOI）用 DOI 溯源，不再错误地写成 PMID:DOI_xxx
    for m in web_materials:
        pmid_num = m.get("pmid", "")
        doi = m.get("doi", "")
        authors = m.get("authors", "Unknown")
        title = m.get("title", "")
        journal = m.get("journal", "")
        pubdate = m.get("pubdate", "")
        if pmid_num:
            ref_line = f"[{len(ref_items)+1}] {authors}. {title}. {journal}. {pubdate}. PMID:{pmid_num}"
            dup_key = f"PMID:{pmid_num}"
        elif doi:
            ref_line = f"[{len(ref_items)+1}] {authors}. {title}. {journal}. {pubdate}. DOI:{doi}"
            dup_key = f"DOI:{doi}"
        else:
            continue

        # 检查是否已存在相同PMID/DOI
        if not any(dup_key in r for r in ref_items):
            ref_items.append(ref_line)

    # 重建参考文献区块
    new_ref = "【#REF_LIST#】\n" + "\n".join(ref_items) + "\n"
    article = article[:ref_match.start()] + new_ref + article[ref_match.end():]

    return article


# ======================== 闸门2：主题相关性强制过滤 ========================
# 人群级过滤配置（可扩展）
GATE2_CONFIG = {
    "青少年": {
        "required_keywords": ["calcium", "bone", "height", "growth", "vitamin d", "adolescent",
                              "bone mass", "peak bone", "dairy", "vitamin-d", "calcium intake"],
        "required_hits": 2,                    # 标题/摘要至少命中 N 个关键词
        "exclude_topics": ["genetic", "syndrome", "infant", "infancy", "pregnant", "pregnancy",
                           "elderly", "geriatric", "menopause", "postmenopaus", "premenopaus",
                           "congenital", "hereditary", "mutation", "disorder", "disease"],
        "population_terms": ["adolescent", "children", "school-age", "school aged", "schoolchild",
                             "teen", "youth", "child", "adolescents", "pediatric"],
        "exclude_population": ["infant", "newborn", "pregnant", "elderly", "geriatric",
                               "postmenopaus", "premenopaus", "older adult"],
    },
    "默认": {
        "required_keywords": [],
        "required_hits": 0,
        "exclude_topics": ["genetic", "syndrome", "congenital", "hereditary", "mutation"],
        "population_terms": [],
        "exclude_population": [],
    },
}


def gate2_topic_filter(web_materials, group):
    """
    闸门2：主题相关性强制过滤（文献级）。
    只保留与目标人群+主题强相关的文献，自动丢弃：
      - 遗传病/罕见病/综合征主题
      - 婴幼儿/孕妇/中老年等非目标人群
    要求标题或摘要命中人群词 + 主题关键词。
    返回过滤后的文献列表和剔除记录。
    """
    cfg = GATE2_CONFIG.get(group, GATE2_CONFIG["默认"])
    kept = []
    dropped = []

    for m in web_materials:
        title = m.get("title", "") or ""
        content = m.get("content", "") or ""
        full_text = (title + " " + content).lower()

        # ① 主题黑名单：命中即丢弃（遗传病、非目标人群）
        hit_exclude = [kw for kw in cfg["exclude_topics"] if kw in full_text]
        if hit_exclude:
            dropped.append({"id": m.get("id", ""), "title": title,
                            "reason": f"命中主题黑名单: {hit_exclude[:2]}"})
            continue

        # ② 人群筛选：标题/摘要中出现目标人群词才保留
        hit_pop = [kw for kw in cfg["population_terms"] if kw in full_text]
        if cfg["population_terms"] and not hit_pop:
            dropped.append({"id": m.get("id", ""), "title": title,
                            "reason": "摘要无目标人群特征词"})
            continue

        # ③ 关键词匹配：命中 required_hits 个主题关键词
        hit_kw = [kw for kw in cfg["required_keywords"] if kw in full_text]
        if cfg["required_keywords"] and len(hit_kw) < cfg["required_hits"]:
            dropped.append({"id": m.get("id", ""), "title": title,
                            "reason": f"主题关键词命中不足({len(hit_kw)}/{cfg['required_hits']}): {hit_kw}"})
            continue

        kept.append(m)

    return kept, dropped


# ======================== 闸门3：本地知识库预处理 ========================
def gate3_kb_preprocess(kb_cards, group):
    """
    闸门3：本地知识库预处理。
    1. 批量去重：按卡片标题去重，保留相似度最高的
    2. 内容筛查：删除遗传病/孕期营养等与目标人群无关的卡片
    3. 返回预处理后的卡片和统计
    """
    cfg = GATE2_CONFIG.get(group, GATE2_CONFIG["默认"])

    # ① 批量去重（按 title）
    seen_titles = {}
    deduped = []
    for c in kb_cards:
        title = c.get("title", "") or ""
        if not title:
            continue
        if title in seen_titles:
            # 保留相似度更高的
            if c.get("similarity", 0) > seen_titles[title].get("similarity", 0):
                seen_titles[title] = c
        else:
            seen_titles[title] = c
    deduped = list(seen_titles.values())

    # ② 内容筛查：排除遗传病/综合征/婴儿等无关卡片
    # 人群自适应：目标人群自身的营养主题不剔除（孕妇保留孕期/哺乳，老年人保留老年/绝经）
    screened = []
    dropped_titles = []
    exclude_words = ["遗传病", "基因突变", "综合征", "新生儿", "婴儿"]
    if cfg["exclude_topics"]:
        exclude_words.extend(cfg["exclude_topics"])
    if group in ("孕妇", "孕早期", "孕中期", "孕晚期"):
        exclude_words = [w for w in exclude_words if w not in ("孕期", "孕妇", "哺乳")]
    if group in ("老年人", "老年"):
        exclude_words = [w for w in exclude_words if w not in ("老年", "绝经")]
    for c in deduped:
        title = c.get("title", "") or ""
        content = c.get("content", "") or ""
        text = title + " " + content
        if any(w in text for w in exclude_words):
            dropped_titles.append(title)
            continue
        screened.append(c)

    return screened, {
        "original": len(kb_cards),
        "after_dedup": len(deduped),
        "after_screen": len(screened),
        "dropped": dropped_titles,
    }


# ======================== 闸门4：Stage1 截断检测与自动重生成 ========================
def gate4_check_truncation(framework):
    """
    闸门4：检测 Stage-1 本地模型输出末尾是否截断残缺。
    判定规则：
      1. 末尾3个结论标签（CONCLUDE_FAST/DEEP/ALL）任一缺失 → 截断
      2. 最后一个板块（REF_LIST）无参考文献行 → 截断
      3. 末尾句子以未闭合标点/半句话收尾 → 截断
    返回 (是否截断, 原因列表)
    """
    if not framework:
        return True, ["框架为空"]

    issues = []
    # 规则1：结论标签缺失
    for tag in ["【#CONCLUDE_FAST#】", "【#CONCLUDE_DEEP#】", "【#CONCLUDE_ALL#】",
                "【#REF_LIST#】"]:
        if tag not in framework:
            issues.append(f"缺少{tag}")

    # 规则2：REF_LIST 无有效参考文献行
    ref_match = re.search(r'【#REF_LIST#】([\s\S]*)$', framework)
    if ref_match:
        ref_body = ref_match.group(1).strip()
        if not re.search(r'\[(\d+)\]', ref_body):
            issues.append("REF_LIST无参考文献条目")
        # 若截断到 REF_LIST 中间（只有标题无内容）
        elif len(ref_body) < 10:
            issues.append("REF_LIST内容过短（疑似截断）")

    # 规则3：末尾句子不完整（以冒号/逗号/破折号/中文冒号收尾）
    tail = framework.strip()
    if tail and tail[-1] in "：:,，、;；—…":
        issues.append("末尾句子未闭合（疑似截断）")

    return len(issues) > 0, issues


def gate4_regenerate_framework(kb_cards, persona, topic, use_ollama, ollama_model, tracker,
                               max_retries=2):
    """闸门4：生成框架 + 截断检测 + 自动重生成（最多重试2次）"""
    attempt = 0
    while attempt <= max_retries:
        if attempt > 0:
            print(f"  ↻ 检测到截断，第{attempt}次重新生成...")
        framework = stage1_build_framework(kb_cards, persona, topic,
                                           use_ollama, ollama_model, tracker)
        if not framework:
            return None, "框架生成失败"
        truncated, reasons = gate4_check_truncation(framework)
        if not truncated:
            print(f"  ✓ Stage1完整性检测通过（第{attempt+1}次生成）")
            return framework, None
        print(f"  ⚠ Stage1截断检测：{reasons}")
        attempt += 1
    print(f"  ✗ Stage1连续{max_retries+1}次截断，使用最后一次结果并标记待补全")
    return framework, f"Stage1连续{max_retries+1}次截断"


# ======================== 闸门5：终稿引用自检 ========================
def gate5_reference_audit(article):
    """
    闸门5：终稿引用自检。
    1. 提取正文上角标引用编号 [n] 与内嵌引用 PMID:xxx（两种格式都识别）
    2. 校验一一对应：正文引用过的文献必须存在于参考文献；参考文献中未被正文引用的 = 无关文献，剔除
    3. 参考文献排序（优先级：国内官方指南 > 国际立场声明 > RCT > 综述/其他）
    返回 (修复后文章, 审计报告)
    """
    if not article:
        return article, {"status": "empty"}

    # ① 提取正文引用编号（排除 REF_LIST 区块内的 [n]）与内嵌PMID引用
    ref_section_start = article.find("【#REF_LIST#】")
    body = article[:ref_section_start] if ref_section_start != -1 else article
    ref_section = article[ref_section_start:] if ref_section_start != -1 else ""

    cited_in_body = set()
    for m in re.finditer(r'\[(\d{1,3})\]', body):
        cited_in_body.add(int(m.group(1)))

    # ①b 正文内嵌PMID引用（如：（Ganmaa et al., 2023, PMID:36441522））
    cited_pmids_in_body = set(re.findall(r'PMID[:_]?\s*(\d{6,9})', body))

    # ② 解析参考文献列表（含每条文献的PMID）
    ref_entries = []
    for m in re.finditer(r'^\[(\d+)\]\s*(.+)$', ref_section, re.MULTILINE):
        num = int(m.group(1))
        pmid_m = re.search(r'PMID[:_]?\s*(\d{6,9})', m.group(2))
        ref_entries.append({"num": num, "text": m.group(2).strip(),
                            "pmid": pmid_m.group(1) if pmid_m else None})

    ref_nums = {e["num"] for e in ref_entries}

    # ③ 判断文献是否被正文引用（编号角标 或 内嵌PMID 任一命中即视为已引用）
    #    官方权威指南（膳食指南/WHO等）属于权威来源声明，即使无角标引用也必须保留
    def is_official_guide_entry(e):
        return bool(re.search(r'膳食指南|膳食营养|Guideline|WHO|世界卫生组织|中国营养学会', e["text"]))
    def is_cited(e):
        if is_official_guide_entry(e):
            return True
        if e["num"] in cited_in_body:
            return True
        if e["pmid"] and e["pmid"] in cited_pmids_in_body:
            return True
        return False

    # ④ 剔除未被正文引用的无关文献（保留被引用的）
    kept_entries = [e for e in ref_entries if is_cited(e)]
    removed_entries = [e for e in ref_entries if not is_cited(e)]
    missing = sorted([n for n in cited_in_body if n not in ref_nums])

    # ⑤ 参考文献排序：指南 > 立场声明 > RCT > 综述
    def ref_priority(e):
        t = e["text"]
        if re.search(r'膳食指南|膳食营养|指南|Guideline|中国营养学会|WHO|世界卫生组织', t):
            return 0   # 国内官方指南 / 国际权威指南
        if re.search(r'立场声明|position paper|position statement|Position', t):
            return 1   # 国际立场声明
        if re.search(r'randomized|RCT|随机对照|trial|Trial', t):
            return 2   # RCT随机对照试验
        return 3       # 综述/其他

    kept_entries.sort(key=lambda e: (ref_priority(e), e["num"]))
    # 重新编号（保证正文角标与文末编号一致）
    renumbered = []
    mapping = {}
    for new_num, e in enumerate(kept_entries, start=1):
        mapping[e["num"]] = new_num
        renumbered.append({"num": new_num, "text": e["text"]})

    # ⑥ 重建正文角标（将旧编号映射为新编号）——仅替换正文部分
    def replace_cite(m):
        old = int(m.group(1))
        if old in mapping:
            return f"[{mapping[old]}]"
        return m.group(0)
    new_body = re.sub(r'\[(\d{1,3})\]', replace_cite, body)

    # ⑦ 重建参考文献区块
    new_ref = "【#REF_LIST#】\n" + "\n".join(f"[{e['num']}] {e['text']}" for e in renumbered) + "\n"
    repaired = new_body + "\n\n" + new_ref

    report = {
        "status": "ok",
        "cited_in_body": len(cited_in_body),
        "cited_pmids_in_body": len(cited_pmids_in_body),
        "ref_total": len(ref_entries),
        "uncited_removed": [f"[{e['num']}] {e['text'][:50]}" for e in removed_entries],
        "missing_citations": missing,
        "ref_final": len(renumbered),
    }
    return repaired, report


# ======================== 官方权威指南补充（闸门5延伸） ========================
OFFICIAL_GUIDES = [
    {"match": ["中国居民膳食指南", "膳食指南"], "ref": "中国营养学会. 中国居民膳食指南2022. 北京: 人民卫生出版社. 2022."},
    {"match": ["WHO", "世界卫生组织"], "ref": "World Health Organization (WHO). Healthy diet. 2020. https://www.who.int/news-room/fact-sheets/detail/healthy-diet"},
    {"match": ["中国学龄儿童膳食指南"], "ref": "中国营养学会. 中国学龄儿童膳食指南2022. 北京: 人民卫生出版社. 2022."},
]


def ensure_official_guides(article):
    """
    将母稿META区块声明的官方权威指南补充进参考文献（若缺失）。
    优先级：国内官方指南 > 国际权威指南（WHO等），追加到REF_LIST最前。
    返回 (补充后文章, 已补充指南列表)
    """
    if not article:
        return article, []
    # 解析 META 中"权威来源"声明
    meta_m = re.search(r'【#META#】([\s\S]*?)(?:【#ALL_INTRO#】|$)', article)
    declared = ""
    if meta_m:
        src_m = re.search(r'权威来源[:：]\s*(.+)', meta_m.group(1))
        if src_m:
            declared = src_m.group(1).strip()
    if not declared:
        return article, []

    # 当前REF_LIST已有的内容（判断是否已包含指南）
    ref_m = re.search(r'【#REF_LIST#】([\s\S]*)$', article)
    ref_body = ref_m.group(1) if ref_m else ""

    added = []
    for guide in OFFICIAL_GUIDES:
        # META 声明中包含该指南关键词 且 REF_LIST 中尚未出现
        if any(k in declared for k in guide["match"]) and \
           not any(k in ref_body for k in guide["match"]):
            added.append(guide["ref"])
            print(f"  ✓ 补充官方权威指南至参考文献：{guide['ref'][:40]}...")

    if not added:
        return article, []

    # 重建 REF_LIST：官方指南插到最前，原有文献编号整体顺延
    body_part = article[:ref_m.start()]
    ref_body_part = article[ref_m.start():]
    guide_lines = "\n".join(f"[{i+1}] {r}" for i, r in enumerate(added))
    # 原文献行重新编号（顺延 len(added)），避免与指南编号冲突
    offset = len(added)
    renumbered_lines = []
    for line in ref_body_part.split("\n"):
        line = line.rstrip()
        m = re.match(r'^\[(\d+)\]\s*(.*)$', line)
        if m:
            renumbered_lines.append(f"[{int(m.group(1)) + offset}] {m.group(2)}")
        else:
            renumbered_lines.append(line)
    new_ref = "【#REF_LIST#】\n" + guide_lines + "\n" + "\n".join(renumbered_lines).lstrip("\n")
    # 正文角标同步偏移（+len(added)），保证 [n] 仍指向正确的文献
    shift = offset

    def shift_cite(m):
        return f"[{int(m.group(1)) + shift}]"

    new_body = re.sub(r'\[(\d{1,3})\]', shift_cite, body_part)
    return new_body + "\n" + new_ref, added


# ======================== 提示词模板 ========================
SYSTEM_STAGE1 = """你是营养学科普文章写作专家，为健康助手撰写科普文章母稿。所有输出必须遵守以下规则：
1. 严格固定文章板块标签，板块顺序不可调换、标签字符不允许修改、删减或者新增；
2. 【#标记名#】必须独占完整一行，必须使用【】符号包裹，该行不能附带空格、文字、符号；
3. 仅基于提供的本地知识库素材生成完整正文，不引入外网文献、不编造PMID编号；
4. 必须生成完整正文内容，每个板块都要有实质内容，禁止只写提纲或一句话带过；
5. 三层内容禁止同质化：速读卡纯实操、深度文讲原理、综述文做学术；
6. 禁止使用[待扩展]等占位标记，内容不够的部分用知识库已有信息充分展开；
7. 禁止使用绝对化表述（一定、根治、百分百、特效）；
8. 涉及疾病膳食建议需标注：建议咨询医生或营养师；
9. 参考文献只列知识库中真实存在的资料，格式：[序号] 机构/作者. 文献名称. 出版物. 年份。"""

SYSTEM_STAGE2 = """你是营养学文献检索专家，仅负责补充外文文献素材。所有输出必须遵守以下规则：
1. 严禁修改、打乱、新增、删减原有文章框架与标签结构，只在现有板块内补充外文文献数据；
2. 所有【#标记名#】必须保持原样，独占完整一行；
3. 只能使用下方提供的联网检索文献，严禁编造任何PMID编号、虚构论文标题或期刊名称；
4. 参考文献列表中只能出现下方提供的联网文献，禁止自行添加任何不在素材列表中的文献；
5. 如果素材列表中没有的文献，绝对不能在正文中引用或出现在参考文献中；
6. 外文文献的随机对照试验、机构立场声明、流行病学数据放入综述层级与进阶拓展板块；
7. 生活化实操建议保留在基础正文和速读板块，不添加外文试验细节到速读卡；
8. 外网最新研究和本地知识库观点冲突时，优先采信更新年份更高的文献；冲突放入学术争议板块；
9. 参考文献格式：[序号] 作者. 文献名称. 期刊. 年份. PMID:编号；
10. 三层摘要、三层结语必须拉开难度差距，浅层偏向实操，深层偏向学术循证。"""

SYSTEM_STAGE3 = """你是格式校验专家。检查文章的母稿格式是否合规。"""


def build_mother_format(persona, topic):
    return f"""板块清单（顺序不可调换）：
【总则】下方"板块清单"中的板块定位文字（如"通用引言""共识基础内容""深度拓展""学术争议"等）仅用于说明各【#标记#】之间应写什么内容；正文中仅"深度拓展""学术争议""综述结论"可作为独立标题行（不编号），其余定位文字（尤其"通用引言""共识基础内容"）严禁原样写入正文。
【#META#】
标题：{topic}
人群标签：{persona}
分类：慢病管理/运动营养/消化健康/母婴营养/老年营养/青少年营养
阅读时长_速读：约1分钟
阅读时长_深度：约3分钟
阅读时长_综述：约5分钟
权威来源：中国居民膳食指南2022、WHO/FAO国际指南、相关营养学研究

【字数弹性规则】各板块字数以参考值为准，允许±50%上下浮动（最多不超过100%），内容表达完整优先；全文总字数控制在3000~6000字，严禁超过8000字。

【#ALL_INTRO#】通用引言（2~3句话）：点明{persona}人群核心痛点+1条流行病学数据

【#SUMMARY_FAST#】速读卡摘要：20-60字（参考约40字），纯实操行动建议（零基础用户）

【#SUMMARY_DEEP#】深度文摘要：40-90字（参考约60字），核心饮食调理方向（进阶读者）

【#SUMMARY_ALL#】综述摘要：50-120字（参考约80字），包含学界共识与现存分歧（专业读者）

【#COMMON_BEGIN#】共识基础内容（400~900字，参考约600字）：底层原理、每日营养素需求量、食物来源清单、通用行动清单
一级标题：一、二、三；二级标题：（一）（二）（三）
【#COMMON_END#】

【#DEEP_PLUS_BEGIN#】深度拓展（600~1350字，参考约900字）：特殊人群、细分场景深度拓展
格式（务必遵守，防止编号冲突）：板块标题单独一行写"深度拓展"（不编号）；其下仅用二级标题"（一）特殊人群"、"（二）细分场景深度拓展"；细分人群/场景条目用加粗短句或直接段落（禁止再用"一、""二、"一级编号，避免与前面共识板块编号重复）
【#DEEP_PLUS_END#】

【#DEBATE_ZONE_BEGIN#】学术争议（200~600字，参考约300字）：未统一的争议点，分点罗列分歧双方观点
【#DEBATE_ZONE_END#】

【#CONCLUDE_FAST#】速读卡结论：1~2句简洁行动纲领

【#CONCLUDE_DEEP#】深度文结论：内容总结+核心膳食建议

【#CONCLUDE_ALL#】综述结论：循证共识总结+研究局限与未来方向

【#REF_LIST#】参考文献6~8条：[序号] 作者. 文献名称. 出版物. 年份"""


# ======================== Stage 1: 本地搭框架 ========================
def stage1_build_framework(kb_cards, persona, topic, use_ollama, ollama_model, tracker):
    """Stage 1: 本地大模型搭建框架"""
    print("\n--- Stage 1: 搭建框架 ---")
    mode = "Ollama本地" if use_ollama else "云端降级"
    print(f"  模式：{mode}")
    
    # 构建素材文本（num_ctx=4096自适应）：
    #   细分人群卡片全部进入素材（保证文章细分章节素材全覆盖）
    #   再补充通用主体卡片（前4张，支撑文章主体内容）
    #   素材总量控制在14张以内，适配4096上下文
    sub_cards = [c for c in kb_cards if c.get("sub_group")]
    gen_cards = [c for c in kb_cards if not c.get("sub_group")]
    top_cards = (sub_cards + gen_cards[:4])[:14]
    materials = "【本地知识库素材（每张卡片均备注来源与细分人群，仅做参考，不写入正文）】\n"
    for i, c in enumerate(top_cards):
        source_note = ""
        if c.get("sub_group"):
            source_note += f" | 细分人群：{c['sub_group']}"
        if c.get("source_channel"):
            source_note += f" | 来源渠道：{c['source_channel']}"
        if c.get("orig_title"):
            source_note += f" | 原文：{c['orig_title'][:40]}"
        if c.get("ingest_time"):
            source_note += f" | 入库：{c['ingest_time'][:10]}"
        content_len = 120 if c.get("sub_group") else 150
        materials += f"\n[{i+1}] {c.get('title','')}{source_note}\n内容：{c.get('content','')[:content_len]}\n"
    
    prompt = f"""请根据以下本地知识库素材，为「{topic}」生成一篇完整的科普文章正文。
目标人群：{persona}。
文章定位：以{persona}整体为写作对象，主题覆盖全人群通用要点；细分人群（如素材中标注"细分人群"的卡片）不作为独立文章主题，而是在文章【#DEEP_PLUS_BEGIN#】板块的特殊人群章节内按细分人群逐一展开。
{persona}常见细分人群（仅展开素材中实际出现的细分人群，禁止凭空杜撰与{persona}无关的人群）：严格按上方知识库素材中标注"细分人群"的卡片逐一展开。

{materials}

【生成要求】
1. 仅基于上述知识库素材生成完整正文，不引入外部文献
2. 所有标签齐全、板块顺序正确
3. 三层难度递进：速读卡(纯实操)→深度文(原理+清单)→综述文(学术循证)
4. 每个板块必须有实质内容，禁止只写提纲，禁止使用[待扩展]占位标记
5. 深度拓展板块的特殊人群章节：按细分人群逐一展开（如"体育特长生需额外补充…"、"素食者需注意…"、"乳糖不耐受者可采用…"），每个细分人群给出针对性建议
6. 学术争议板块要列出知识库中存在的分歧观点
7. 参考文献只列知识库中真实存在的资料
8. 涉及细化知识点（如菠菜草酸焯水、负重运动清单、尿钙流失机制等）要充分展开

{build_mother_format(persona, topic)}"""
    
    if use_ollama:
        framework = call_ollama(prompt, SYSTEM_STAGE1, ollama_model, tracker,
                               "Stage1框架", temp=0.3, max_tokens=2500)
    else:
        framework = call_cloud(prompt, SYSTEM_STAGE1, tracker,
                              "Stage1框架", temp=0.5, max_tokens=3000)
    
    if framework:
        print(f"  ✓ 框架完成：{len(framework)}字")
    return framework


# ======================== Stage 2: 云端外扩 ========================
def stage2_expand(framework, web_materials, persona, topic, tracker):
    """Stage 2: 云端API外扩补强"""
    print("\n--- Stage 2: 云端外扩 ---")
    
    # 构建联网素材文本 + 明确列出可用文献清单（防止云端编造）
    # 有 PMID 用 PMID 标注；无 PMID（如 Crossref 仅 DOI）用 DOI 标注，禁止模型为其编造 PMID
    web_text = "【联网搜索新素材（仅限以下文献，禁止添加其他任何文献）】\n"
    for i, m in enumerate(web_materials):
        if m.get("pmid"):
            ref_id = f"PMID:{m['pmid']}"
        elif m.get("doi"):
            ref_id = f"DOI:{m['doi']}"
        else:
            ref_id = m.get("id", "")
        web_text += f"\n[{i+1}] {ref_id}\n标题：{m.get('title','')}\n作者：{m.get('authors','')}\n期刊：{m.get('journal','')}\n年份：{m.get('pubdate','')}\n内容：{m.get('content','')[:300]}\n"

    # 明确列出允许引用的PMID白名单（无PMID的文献仅以DOI标注，不允许为其编造PMID）
    allowed_pmids = [m.get("pmid", "") for m in web_materials if m.get("pmid")]
    allowed_pmids_str = ", ".join([f"PMID:{p}" for p in allowed_pmids]) if allowed_pmids else "（无，仅可引用上方以 DOI 标注的文献）"
    
    prompt = f"""以下是一篇关于「{topic}」的科普文章初稿（基于本地知识库生成）。
请仅使用下方提供的真实联网文献，对文章进行外文素材补充。

【文章初稿】
{framework}

{web_text}

【允许引用的PMID白名单（只能使用以下PMID，禁止添加任何其他PMID）】
{allowed_pmids_str}

【补强要求】
1. 严禁修改、打乱、新增、删减原有文章框架与标签结构
2. 所有【#标记名#】必须保持原样，独占完整一行
3. 必须确保输出包含全部15个母稿标签：【#META#】【#ALL_INTRO#】【#SUMMARY_FAST#】【#SUMMARY_DEEP#】【#SUMMARY_ALL#】【#COMMON_BEGIN#】【#COMMON_END#】【#DEEP_PLUS_BEGIN#】【#DEEP_PLUS_END#】【#DEBATE_ZONE_BEGIN#】【#DEBATE_ZONE_END#】【#CONCLUDE_FAST#】【#CONCLUDE_DEEP#】【#CONCLUDE_ALL#】【#REF_LIST#】
4. 如果初稿中缺失某些标签（可能被截断），必须补全这些标签及其内容
5. 只能使用上方白名单中的PMID，严禁编造任何不在白名单中的PMID编号；无PMID的文献以DOI标注（引用其[序号]即可），禁止为它们编造PMID
6. 参考文献列表中只能出现上方提供的联网文献，禁止自行添加任何其他文献
7. 将联网文献的试验数据、权威声明放入综述层级和进阶拓展板块
8. 生活化实操建议保留在基础正文和速读板块，不添加外文试验到速读卡
9. 重复结论合并精简，观点冲突放入争议板块
10. 引用格式硬性要求：正文内引用统一使用[序号]上角标（如"研究显示……[1]"），严禁在正文内使用（作者, 年份, PMID:xxx）内嵌格式；文末参考文献列表必须以[序号]开头，格式：[序号] 作者. 文献名称. 期刊. 年份. PMID:编号
11. 字数弹性：各板块字数允许±50%上下浮动（最多100%），内容表达完整优先；全文控制在3000~6000字，严禁超过8000字
12. 输出完整的补强后文章（包含所有母稿标记）"""
    
    expanded = call_cloud(prompt, SYSTEM_STAGE2, tracker,
                         "Stage2外扩", temp=0.7, max_tokens=3500)
    
    if expanded:
        print(f"  ✓ 外扩完成：{len(expanded)}字")
    return expanded


# ======================== Stage 3: 格式校验 ========================
def _structure_check(article):
    """结构校验：模板标记残留 + 一级编号重复 + DEEP_PLUS 板块编号冲突
    防止出现历史问题：『通用引言/共识基础内容』残留正文、『特殊人群』用一、二、一级编号与前面板块冲突"""
    errors = []

    # 1. 模板标记残留：这些是模板内部描述文字，严禁出现在正文标题
    for label in ["通用引言", "共识基础内容"]:
        for line in article.split('\n'):
            if line.strip() == label:
                errors.append(f"正文包含模板标记残留『{label}』（该行应删除，禁止写入正文标题）")

    # 2. 提取 DEEP_PLUS 板块
    m = re.search(r"【#DEEP_PLUS_BEGIN#】(.*?)【#DEEP_PLUS_END#】", article, re.S)
    dp = m.group(1) if m else ""

    # 3. DEEP_PLUS 板块内禁止使用"一、""二、"一级编号（应使用（一）（二）二级编号或直接段落）
    if dp:
        h1_in_dp = re.findall(r"^[一二三四五六七八九十百]+、", dp, re.M)
        if h1_in_dp:
            errors.append(f"DEEP_PLUS 板块内使用了{len(h1_in_dp)}个一级编号{h1_in_dp[:4]}，应改用二级编号（一）（二），避免与前面共识板块编号冲突")

    # 4. 全篇一级编号重复检测
    all_h1 = re.findall(r"^([一二三四五六七八九十百]+)、", article, re.M)
    if len(all_h1) != len(set(all_h1)):
        errors.append(f"全篇一级编号重复: {all_h1}")

    # 5. 深度拓展板块：若存在裸标题（特殊人群/细分场景/深度拓展），应能匹配板块标题规范
    for lbl in ["深度拓展", "特殊人群", "细分场景"]:
        if dp and lbl not in dp:
            pass  # 板块内部结构灵活，不强校验标题必须存在

    return errors


def stage3_validate(article, use_ollama, ollama_model, tracker):
    """Stage 3: 格式校验"""
    print("\n--- Stage 3: 格式校验 ---")
    mode = "Ollama本地" if use_ollama else "云端降级"
    print(f"  模式：{mode}")
    
    required_tags = [
        "【#META#】", "【#ALL_INTRO#】", "【#SUMMARY_FAST#】", "【#SUMMARY_DEEP#】",
        "【#SUMMARY_ALL#】", "【#COMMON_BEGIN#】", "【#COMMON_END#】",
        "【#DEEP_PLUS_BEGIN#】", "【#DEEP_PLUS_END#】",
        "【#DEBATE_ZONE_BEGIN#】", "【#DEBATE_ZONE_END#】",
        "【#CONCLUDE_FAST#】", "【#CONCLUDE_DEEP#】", "【#CONCLUDE_ALL#】",
        "【#REF_LIST#】"
    ]
    
    # 简单检查标签完整性
    missing = [tag for tag in required_tags if tag not in article]
    order_ok = all(article.find(required_tags[i]) < article.find(required_tags[i+1])
                   for i in range(len(required_tags)-1) if required_tags[i] in article and required_tags[i+1] in article)

    # 结构校验（模板残留 / 编号冲突）
    structure_errors = _structure_check(article)
    if structure_errors:
        for e in structure_errors:
            print(f"  ⚠ {e}")

    if not missing and order_ok and not structure_errors:
        print(f"  ✓ 格式校验通过（15个标签齐全，顺序正确，结构合规）")
        return {"pass": True, "missing": [], "order_ok": True, "structure_errors": []}
    
    print(f"  ⚠ 格式问题：缺失{len(missing)}个标签，顺序{'正确' if order_ok else '错误'}"
          + (f"，结构问题{len(structure_errors)}处" if structure_errors else ""))
    if missing:
        print(f"    缺失：{missing}")
    
    return {"pass": False, "missing": missing, "order_ok": order_ok, "structure_errors": structure_errors}


# ======================== 主流程 ========================
def run_pipeline(group, persona, topic, pubmed_keywords):
    """运行完整双模型流水线"""
    print("=" * 70)
    print("v3.2 双模型流水线 — 母稿生成")
    print("=" * 70)
    print(f"人群：{group}")
    print(f"主题：{topic}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检测Ollama
    print("\n检测Ollama...")
    ollama_ok, ollama_model = check_ollama()
    use_ollama = ollama_ok
    
    # Stage 0: 知识库检索
    print("\n--- Stage 0: 知识库检索 ---")
    kb_cards_raw = retrieve_from_kb(topic, group, top_n=14)
    print(f"  检索到{len(kb_cards_raw)}张卡片")
    for i, c in enumerate(kb_cards_raw[:5]):
        print(f"    [{i+1}] {c.get('title','')[:50]} (相似度:{c.get('similarity',0):.3f})")

    # 闸门3：本地知识库预处理（批量去重 + 内容筛查 + 无关卡片剔除）
    print("\n--- 闸门3: 知识库预处理 ---")
    kb_cards, gate3_report = gate3_kb_preprocess(kb_cards_raw, group)
    print(f"  去重前{gate3_report['original']}张 → 去重后{gate3_report['after_dedup']}张 → 筛查后{gate3_report['after_screen']}张")
    if gate3_report["dropped"]:
        print(f"  剔除无关卡片{len(gate3_report['dropped'])}张：{gate3_report['dropped'][:3]}")
    
    # Stage 0.5: 联网搜索（多源回退：PubMed → Europe-PMC → Semantic Scholar → Crossref）
    print("\n--- Stage 0.5: 联网搜索（多源回退） ---")
    existing_ids = {c.get("card_id", "") for c in kb_cards}
    web_materials = []
    verified_pmids = set()  # 记录所有真实获取的PMID（白名单，用于幻觉检测）
    literature_sources = []  # 记录命中的文献来源
    for kw in pubmed_keywords:
        print(f"  [检索] {kw}")
        results, used_source = search_literature_online(kw, max_results=3, exclude_ids=existing_ids)
        if used_source and used_source not in literature_sources:
            literature_sources.append(used_source)
        for r in results:
            pmid_num = r.get("pmid", "")
            if pmid_num:
                verified_pmids.add(pmid_num)
        web_materials.extend(results)
        time.sleep(1)
    print(f"  联网新文献：{len(web_materials)}篇（来源：{literature_sources or '全部网络不可达，本次无外文素材'}）")

    # 闸门2：主题相关性强制过滤（人群+关键词+主题黑名单）
    print("\n--- 闸门2: 文献主题相关性过滤 ---")
    web_materials, gate2_report = gate2_topic_filter(web_materials, group)
    print(f"  过滤前文献{len(web_materials)+len(gate2_report)}篇 → 保留{len(web_materials)}篇，剔除{len(gate2_report)}篇")
    for d in gate2_report[:5]:
        print(f"    剔除：{d.get('title','')[:45]}（{d.get('reason','')}）")
    # 同步更新已验证PMID集合（只保留通过过滤的文献）
    verified_pmids = set()
    for r in web_materials:
        pmid_num = r.get("pmid", "")
        if pmid_num:
            verified_pmids.add(pmid_num)
    print(f"  闸门2通过后已验证PMID集合：{len(verified_pmids)}个（用于后续幻觉检测）")

    tracker = {"total": 0, "calls": 0, "local_calls": 0, "cloud_calls": 0}

    # Stage 1: 本地生成完整正文（闸门4：截断检测 + 自动重生成）
    framework, gate4_err = gate4_regenerate_framework(
        kb_cards, persona, topic, use_ollama, ollama_model, tracker, max_retries=2)
    if gate4_err:
        print(f"✗ Stage 1失败（{gate4_err}），终止")
        return None

    # Stage 2: 云端外扩（仅补外文素材）
    final_article = stage2_expand(framework, web_materials, persona, topic, tracker)
    if not final_article:
        print("✗ Stage 2失败，使用框架作为终稿")
        final_article = framework

    # Stage 2.5: PMID双重校验 + 清理（方案A：白名单 + Europe-PMC第二层）
    print("\n--- Stage 2.5: PMID双重校验 + 清理 ---")
    final_article, pmid_report = verify_pmids_in_article(final_article, verified_pmids)
    print(f"  PMID校验：共{pmid_report['total']}个，真实{pmid_report['verified']}个，剔除虚假{len(pmid_report['fake'])}个")
    if pmid_report.get("second_check", 0) > 0:
        print(f"  Europe-PMC第二层复核：{pmid_report['second_check']}个PMID经过二次排查")

    # 清理占位标记（方案C）
    final_article = clean_placeholders(final_article)

    # 参考文献标准化（方案C）
    final_article = standardize_references(final_article, web_materials)
    print(f"  参考文献标准化完成")

    # 闸门5延伸：META声明的官方权威指南补充进参考文献（若缺失），正文角标同步偏移
    final_article, added_guides = ensure_official_guides(final_article)
    if added_guides:
        print(f"  ✓ 补充{len(added_guides)}条官方权威指南（正文角标已同步偏移）")
    else:
        print(f"  - META声明权威指南已在参考文献中，无需补充")

    # Stage 3: 格式校验
    validation = stage3_validate(final_article, use_ollama, ollama_model, tracker)

    # 闸门5：终稿引用自检（正文角标↔文末参考文献一一对应 + 无关文献清理 + 排序）
    print("\n--- 闸门5: 终稿引用自检 ---")
    final_article, gate5_report = gate5_reference_audit(final_article)
    print(f"  正文引用{gate5_report['cited_in_body']}个编号 | 参考文献{gate5_report['ref_total']}条")
    if gate5_report["uncited_removed"]:
        print(f"  剔除未引用无关文献{len(gate5_report['uncited_removed'])}条：")
        for r in gate5_report["uncited_removed"][:3]:
            print(f"    {r}")
    if gate5_report["missing_citations"]:
        print(f"  ⚠ 正文引用了但参考文献缺失的编号：{gate5_report['missing_citations']}")
    print(f"  自检后参考文献{gate5_report['ref_final']}条（已按 指南>立场声明>RCT>综述 排序）")
    
    # 保存结果（文件名必须安全化：Windows 禁止 ?*:<>|" 等字符，且中文人群名可能混入非法字符）
    safe_group = re.sub(r'[\\/:*?"<>|\r\n\t]', '_', group or "default").strip()
    if not safe_group:
        safe_group = "default"
    output_file = os.path.join(OUTPUT_DIR, f"{safe_group}_v32_pipeline.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"{'='*70}\n")
        f.write(f"v3.2 双模型流水线生成（五道质量闸门）\n")
        f.write(f"人群：{group} | 主题：{topic}\n")
        f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Ollama：{'✓ '+ollama_model if use_ollama else '✗ 降级云端'}\n")
        f.write(f"知识库卡片：{gate3_report['original']}张 → 闸门3预处理后{gate3_report['after_screen']}张\n")
        f.write(f"联网文献：闸门2过滤后{len(web_materials)}篇（来源：{literature_sources or '网络不可达'}；剔除{len(gate2_report)}篇无关文献）\n")
        f.write(f"Token估算：{tracker['total']}（本地{tracker['local_calls']}次+云端{tracker['cloud_calls']}次）\n")
        f.write(f"闸门1 PMID校验：共{pmid_report['total']}个，真实{pmid_report['verified']}个，剔除虚假{len(pmid_report['fake'])}个\n")
        if pmid_report.get("second_check", 0) > 0:
            f.write(f"Europe-PMC第二层复核：{pmid_report['second_check']}个PMID二次排查\n")
        f.write(f"闸门4 Stage1完整性：{'通过' if not gate4_err else gate4_err}\n")
        f.write(f"闸门5 引用自检：正文引用{gate5_report['cited_in_body']}个编号，参考文献{gate5_report['ref_final']}条，剔除未引用{len(gate5_report['uncited_removed'])}条\n")
        f.write(f"格式校验：{'通过' if validation['pass'] else '有问题'}\n")
        f.write(f"{'='*70}\n\n")
        f.write(final_article)
        f.write(f"\n\n{'='*70}\n")
        f.write(f"Stage 1 框架（本地生成）\n")
        f.write(f"{'='*70}\n\n")
        f.write(framework)
        f.write(f"\n\n{'='*70}\n")
        f.write(f"素材详情\n")
        f.write(f"{'='*70}\n\n")
        f.write(f"【知识库卡片】（每张卡片均标注真实来源，便于溯源核查）\n")
        for i, c in enumerate(kb_cards):
            source = c.get("source_channel", "") or "未知来源"
            line = f"[{i+1}] {c.get('title','')}（{c.get('group','')}）｜ 来源：{source}"
            if c.get("sub_group"):
                line += f"｜ 细分人群：{c['sub_group']}"
            if c.get("source_url"):
                line += f"｜ 链接：{c['source_url']}"
            elif c.get("journal"):
                line += f"｜ {c['journal']}"
            if c.get("pubdate"):
                line += f"（{c['pubdate']}）"
            if c.get("orig_title") and c["orig_title"] != c.get("title", ""):
                line += f"｜ 原文：{c['orig_title'][:60]}"
            if c.get("ingest_time"):
                line += f"｜ 入库：{c['ingest_time'][:10]}"
            f.write(line + "\n")
        f.write(f"\n【联网新文献】\n")
        for i, m in enumerate(web_materials):
            if m.get("pmid"):
                display_id = f"PMID:{m['pmid']}"
            elif m.get("doi"):
                display_id = f"DOI:{m['doi']}"
            else:
                display_id = m.get("id", "")
            f.write(f"[{i+1}] {m.get('title','')}（{display_id}｜来源：{m.get('source_api','')}）\n")
    
    # 汇总
    print(f"\n{'='*70}")
    print(f"流水线完成（五道质量闸门）")
    print(f"{'='*70}")
    print(f"终稿长度：{len(final_article)}字")
    print(f"闸门3知识库预处理：{gate3_report['original']}→{gate3_report['after_screen']}张（剔除{len(gate3_report['dropped'])}张）")
    print(f"闸门2文献过滤：保留{len(web_materials)}篇，剔除{len(gate2_report)}篇")
    print(f"Token估算：{tracker['total']}（本地{tracker['local_calls']}+云端{tracker['cloud_calls']}）")
    print(f"闸门1 PMID校验：共{pmid_report['total']}个，真实{pmid_report['verified']}个，剔除虚假{len(pmid_report['fake'])}个")
    if pmid_report.get("second_check", 0) > 0:
        print(f"Europe-PMC第二层复核：{pmid_report['second_check']}个PMID二次排查")
    print(f"闸门5 引用自检：剔除未引用{len(gate5_report['uncited_removed'])}条，参考文献{gate5_report['ref_final']}条")
    print(f"格式校验：{'通过' if validation['pass'] else '有问题'}")
    print(f"结果已保存：{output_file}")
    
    return {
        "article": final_article,
        "framework": framework,
        "validation": validation,
        "tracker": tracker,
        "output_file": output_file,
        "gate2_report": gate2_report,
        "gate3_report": gate3_report,
        "gate5_report": gate5_report,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="v3.2 双模型流水线 — 母稿生成")
    parser.add_argument("--group", default="青少年", help="人群分组（普通人/健身用户/孕妇/青少年/老年人/糖尿病患者）")
    parser.add_argument("--persona", default=None, help="目标人群标签，默认与group相同")
    parser.add_argument("--topic", default="青少年补钙与身高发育的营养策略", help="文章主题")
    parser.add_argument("--keywords", nargs="+", default=None, help="PubMed搜索关键词，多个用空格分隔")
    args = parser.parse_args()

    persona = args.persona or args.group

    # 默认关键词映射（按人群）
    default_keywords = {
        "普通人": ["balanced diet general population health", "dietary guidelines chronic disease prevention"],
        "健身用户": ["protein intake resistance training muscle", "sports nutrition supplementation recovery"],
        "孕妇": ["prenatal nutrition pregnancy outcomes", "folic acid iron supplementation pregnancy"],
        "青少年": ["calcium supplementation adolescent height growth", "adolescent bone development calcium vitamin D"],
        "老年人": ["elderly protein intake sarcopenia prevention", "elderly nutrition bone health calcium vitamin D"],
        "糖尿病患者": ["diabetes diet glycemic control", "type 2 diabetes meal plan blood glucose"],
    }
    keywords = args.keywords or default_keywords.get(args.group, default_keywords["普通人"])

    print(f"参数：group={args.group} | persona={persona} | topic={args.topic}")
    print(f"搜索关键词：{keywords}")

    result = run_pipeline(
        group=args.group,
        persona=persona,
        topic=args.topic,
        pubmed_keywords=keywords
    )
