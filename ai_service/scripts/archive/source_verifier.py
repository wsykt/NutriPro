# -*- coding: utf-8 -*-
"""
来源真实性验证模块
====================
1. PubMed / Europe-PMC 链接有效性验证 —— 确保知识库卡片的链接指向有效资源，用户可直接点开核对
2. 内容一致性校验 —— 通过哈希值比对防止信息被篡改或编造
3. 批量链接健康检查 —— 定期检查并更新链接状态
4. LLM双引擎真实性检测 —— 本地Ollama(qwen2.5-7b) 与 云端DeepSeek 对比测试

用法：
    python source_verifier.py --verify-links           # 批量验证知识库卡片链接
    python source_verifier.py --verify-pmid 39947162   # 验证单个PMID
    python source_verifier.py --llm-compare <article.txt>  # 本地/云端双引擎对比检测
"""
import hashlib
import json
import os
import re
import sys
import time
import requests
from datetime import datetime

AI_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_SERVICE_DIR)

from config.settings import settings

DEEPSEEK_API_KEY = settings.DEEPSEEK_API_KEY
DEEPSEEK_API_BASE = settings.DEEPSEEK_API_BASE or "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = settings.DEEPSEEK_MODEL or "deepseek-chat"
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-7b-q4km")
# 本地模型上下文自适应（与pipeline_v32.py一致）：优先8192，资源不足自动降级
NUM_CTX_TIERS = [8192, 6144, 4096, 2048]
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
# 资源不足类错误（显存/OOM等）→ 降级到更小上下文可缓解
_RESOURCE_ERR_MSG = ("memory", "oom", "vram", "allocation", "no space", "capacity", "resource")
# 提示词超长类错误（prompt超过上下文长度）→ 降级只会更糟，直接失败
_PROMPT_TOO_LONG_MSG = ("exceeds maximum context", "context length", "prompt token count",
                        "too long", "sequence too long", "window too small")

CHECK_LOG = os.path.join(AI_SERVICE_DIR, "test_results", "link_check_report.json")


# ======================== 1. PMID链接有效性验证 ========================
def extract_pmid(text):
    """从链接或文本中提取PMID编号"""
    m = re.search(r"(\d{6,9})", str(text))
    return m.group(1) if m else None


def verify_pubmed_link(pmid):
    """
    通过Europe-PMC API验证PMID链接有效性（返回真实元数据）。
    valid=True  链接指向有效文献，返回真实标题/期刊/年份供人工核对
    valid=False 链接无效（编号不存在）
    valid=None  网络异常（不阻断，标记待重试）
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        resp = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": f"EXT_ID:{pmid} AND SRC:MED", "format": "json", "pageSize": 1},
            timeout=10,
        )
        data = resp.json()
        if data.get("hitCount", 0) > 0:
            r = data["resultList"]["result"][0]
            journal = ""
            jinfo = r.get("journalInfo", {}) or {}
            j = jinfo.get("journal", {}) or {}
            journal = j.get("title", "")
            return {
                "valid": True,
                "pmid": pmid,
                "title": r.get("title", ""),
                "journal": journal,
                "pubdate": r.get("pubYear", ""),
                "authors": r.get("authorString", "")[:120],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "checked_at": now,
            }
        return {"valid": False, "pmid": pmid, "reason": "Europe-PMC无匹配记录(SRC:MED)", "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "checked_at": now}
    except Exception as e:
        return {"valid": None, "pmid": pmid, "reason": f"网络异常: {e}", "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "checked_at": now}


# ======================== 2. 内容一致性哈希校验 ========================
def content_hash(content, algorithm="sha256"):
    """计算内容哈希值（用于防止篡改/编造比对）"""
    return hashlib.new(algorithm, (content or "").encode("utf-8")).hexdigest()


def verify_content_integrity(content, stored_hash, algorithm="sha256"):
    """
    内容一致性校验：比对当前内容哈希与存储哈希。
    返回 match=True 表示内容未被篡改；False 表示内容已被修改（需人工核查）
    """
    current = content_hash(content, algorithm)
    return {
        "match": current == stored_hash,
        "algorithm": algorithm,
        "current_hash": current,
        "stored_hash": stored_hash,
        "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ======================== 3. 批量链接健康检查 ========================
def load_kb_cards_for_check(top_n=None):
    """从ChromaDB加载知识库卡片（带source_url的），供链接验证"""
    try:
        from vector.retriever import retriever
        total = retriever.count()
        all_data = retriever.collection.get(include=["documents", "metadatas"])
        docs = all_data.get("documents", []) or []
        metas = all_data.get("metadatas", []) or []
        cards = []
        for i, meta in enumerate(metas or []):
            if not meta.get("source_url"):
                continue
            cards.append({
                "card_id": meta.get("card_id", ""),
                "title": meta.get("topic", "") or docs[i][:50],
                "source_url": meta.get("source_url", ""),
                "content": docs[i],
            })
        return cards[:top_n] if top_n else cards
    except Exception as e:
        print(f"  ✗ 加载知识库卡片失败：{e}")
        return []


def check_links_batch(cards, limit=None, interval=0.3):
    """
    批量验证链接，带请求间隔限速。返回检查报告并落盘。
    limit: 限制检查数量（默认全部）
    """
    cards = cards[:limit] if limit else cards
    print(f"开始批量链接验证：共{len(cards)}条卡片")
    report = {"checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "total": len(cards), "valid": 0, "invalid": [], "network_error": 0, "items": []}
    for i, card in enumerate(cards):
        pmid = extract_pmid(card.get("source_url", ""))
        if not pmid:
            report["items"].append({**card, "verify": {"valid": None, "reason": "无PMID编号", "url": card.get("source_url", "")}})
            continue
        verify = verify_pubmed_link(pmid)
        item = {**card, "pmid": pmid, "verify": verify}
        report["items"].append(item)
        if verify["valid"] is True:
            report["valid"] += 1
            print(f"  [{i+1}/{len(cards)}] ✓ PMID:{pmid} 有效 -> {verify['title'][:50]}")
        elif verify["valid"] is False:
            report["invalid"].append({"card_id": card["card_id"], "title": card["title"], "pmid": pmid, "url": card.get("source_url", "")})
            print(f"  [{i+1}/{len(cards)}] ✗ PMID:{pmid} 无效（{verify.get('reason','')}）: {card['title'][:40]}")
        else:
            report["network_error"] += 1
            print(f"  [{i+1}/{len(cards)}] ⚠ PMID:{pmid} 网络异常: {card['title'][:40]}")
        time.sleep(interval)

    os.makedirs(os.path.dirname(CHECK_LOG), exist_ok=True)
    with open(CHECK_LOG, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n链接检查完成：有效{report['valid']} / 无效{len(report['invalid'])} / 网络异常{report['network_error']} / 无PMID{len(cards)-report['valid']-len(report['invalid'])-report['network_error']}")
    print(f"报告已保存：{CHECK_LOG}")
    return report


# ======================== 4. LLM双引擎真实性检测 ========================
DETECT_PROMPT = """你是医学文献真实性审核员。请审核下面科普文章中的【参考文献列表】与正文引用。
任务：
1. 逐条检查每条参考文献的 PMID 编号是否存在、标题是否像真实文献（警惕编造/幻觉）
2. 检查正文引用角标[编号]是否与文末参考文献一一对应（有无引用空编号、多出的文献）
3. 检查正文中的数据/结论是否有明显编造痕迹（如引用不存在的机构报告）
输出格式（严格按JSON）：
{"pmid_issues": ["PMID:xxx 疑似不真实，原因..."], "citation_mismatch": [...], "fabrication_suspicion": [...], "conclusion": "PASS / REVIEW / FAIL", "summary": "一句话总结"}
只输出JSON，不要输出其他内容。

文章内容：
{article}"""


def detect_with_local_model(article, max_tokens=800):
    """
    本地Ollama qwen2.5-7b 真实性检测。
    num_ctx 自适应：优先4096，资源不足自动降级到3072→2048。
    prompt 优先取 REF_LIST 关键片段（检测的核心是参考文献与引用对应关系）。
    """
    # 只提取对检测最有价值的片段：REF_LIST 参考文献列表（+ META权威来源声明）
    ref_start = article.find("【#REF_LIST#】")
    if ref_start != -1:
        key_part = article[ref_start:ref_start + 1600]
    else:
        key_part = article[:1000]
    prompt = DETECT_PROMPT.replace("{article}", key_part)
    if len(prompt) > 6500:
        prompt = prompt[:6500]  # 兜底截断，适配 4096 上下文

    headers = {"Content-Type": "application/json"}
    tiers = [c for c in NUM_CTX_TIERS if c <= OLLAMA_NUM_CTX] or [NUM_CTX_TIERS[-1]]
    last_err = None
    for num_ctx in tiers:
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": max_tokens, "num_ctx": num_ctx},
        }
        try:
            resp = requests.post(f"{OLLAMA_API_BASE}/api/chat", headers=headers, json=payload, timeout=300)
            data = resp.json()
            if resp.status_code != 200:
                raise RuntimeError(data.get("error", f"HTTP {resp.status_code}"))
            content = data.get("message", {}).get("content", "")
            if not content:
                return '{"error": "本地模型返回空内容（疑似截断）"}'
            return content
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            # 提示词超长：降级只会更糟（更小上下文更放不下），直接失败
            if any(k in msg for k in _PROMPT_TOO_LONG_MSG):
                return f'{{"error": "提示词超过num_ctx={num_ctx}长度: {e}"}}'
            # 资源不足类错误（显存/OOM/上下文容量）→ 自动降级到更小的上下文
            if any(k in msg for k in _RESOURCE_ERR_MSG):
                print(f"  ⚠ num_ctx={num_ctx} 资源不足（{e}），自动降级上下文...")
                continue
            return f'{{"error": "本地模型调用失败: {e}"}}'
    return f'{{"error": "本地模型全部档位失败: {last_err}"}}'


def detect_with_cloud_model(article, max_tokens=1000):
    """云端DeepSeek 真实性检测"""
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": DETECT_PROMPT.replace("{article}", article[:6000])}],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    try:
        resp = requests.post(f"{DEEPSEEK_API_BASE}/chat/completions", headers=headers, json=payload, timeout=180)
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f'{{"error": "云端模型调用失败: {e}"}}'


def parse_json_response(text):
    """从LLM输出中提取JSON"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?|\n?```$", "", text).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {"raw": text[:500], "conclusion": "PARSE_ERROR", "summary": "无法解析模型输出"}


def llm_compare(article, use_local=True, use_cloud=True):
    """
    本地/云端双引擎对比检测。
    返回一致性报告：两引擎结论是否一致、各自的发现问题。
    """
    print("=" * 60)
    print("LLM双引擎真实性检测（本地Ollama vs 云端DeepSeek）")
    print("=" * 60)
    report = {"checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if use_local:
        print("\n[引擎1] 本地 Ollama qwen2.5-7b 检测中...")
        t0 = time.time()
        local_raw = detect_with_local_model(article)
        report["local"] = {"elapsed_s": round(time.time() - t0, 1), "raw": local_raw,
                           "parsed": parse_json_response(local_raw)}
        print(f"  完成（{report['local']['elapsed_s']}s），结论：{report['local']['parsed'].get('conclusion','?')}")

    if use_cloud:
        print("\n[引擎2] 云端 DeepSeek 检测中...")
        t0 = time.time()
        cloud_raw = detect_with_cloud_model(article)
        report["cloud"] = {"elapsed_s": round(time.time() - t0, 1), "raw": cloud_raw,
                           "parsed": parse_json_response(cloud_raw)}
        print(f"  完成（{report['cloud']['elapsed_s']}s），结论：{report['cloud']['parsed'].get('conclusion','?')}")

    # 结论一致性比对
    if use_local and use_cloud:
        lc = report["local"]["parsed"].get("conclusion")
        cc = report["cloud"]["parsed"].get("conclusion")
        report["agreement"] = (lc == cc)
        print(f"\n双引擎结论一致性：{'一致' if lc == cc else '不一致'}（本地={lc}，云端={cc}）")

    out = os.path.join(AI_SERVICE_DIR, "test_results", "llm_compare_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    print(f"对比报告已保存：{out}")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="来源真实性验证模块")
    parser.add_argument("--verify-links", action="store_true", help="批量验证知识库卡片链接")
    parser.add_argument("--limit", type=int, default=None, help="限制验证数量")
    parser.add_argument("--verify-pmid", type=str, default=None, help="验证单个PMID")
    parser.add_argument("--llm-compare", type=str, default=None, help="对文章文件执行本地/云端双引擎检测")
    parser.add_argument("--local-only", action="store_true", help="仅本地模型检测")
    parser.add_argument("--cloud-only", action="store_true", help="仅云端模型检测")
    args = parser.parse_args()

    if args.verify_pmid:
        print(json.dumps(verify_pubmed_link(args.verify_pmid), ensure_ascii=False, indent=2))
    elif args.llm_compare:
        with open(args.llm_compare, "r", encoding="utf-8") as f:
            article_text = f.read()
        llm_compare(article_text, use_local=not args.cloud_only, use_cloud=not args.local_only)
    elif args.verify_links:
        cards = load_kb_cards_for_check(args.limit)
        check_links_batch(cards, limit=args.limit)
    else:
        parser.print_help()
