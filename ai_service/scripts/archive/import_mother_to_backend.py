# -*- coding: utf-8 -*-
"""
将 pipeline_v32 双模型流水线生成的母稿导入后端项目（复用后端 ArticleSplitUtil 拆分入库）。
用法：
    python import_mother_to_backend.py <pipeline输出文件> <topic> <persona>
示例：
    python import_mother_to_backend.py test_results/v32_pipeline/孕妇_v32_pipeline.txt "孕妇叶酸补充与神经管畸形预防" "孕妇"
"""
import sys
import os
import re
import json
import requests

BACKEND_URL = "http://localhost:8082"
IMPORT_API = BACKEND_URL + "/api/articles/import-mother"


def extract_mother_draft(file_path):
    """从 pipeline 输出文件中提取母稿部分。

    输出文件结构：
        ====== 头信息 ======
        母稿（【#META#】...【#REF_LIST#】）
        ====== Stage 1 框架 ======
        ====== 素材详情 ======

    只提取第一个 ====== 分隔线之后的母稿正文，避免素材详情的
    "[1] 卡片名｜ 来源：..." 列表被后端 parseRefs 误判为参考文献。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    idx = content.find("【#META#】")
    if idx == -1:
        raise ValueError(f"未找到【#META#】标记：{file_path}")
    # 截断到下一个分隔线（====）之前
    end = content.find("\n=====", idx)
    if end != -1:
        draft = content[idx:end]
    else:
        draft = content[idx:]
    # 若母稿内还残留 Stage 1 框架的第二个【#META#】，截断到它之前
    second = draft.find("【#META#】", draft.find("【#META#】") + 1)
    if second != -1:
        draft = draft[:second]
    return draft


def import_mother(mother_draft, topic, persona):
    payload = {
        "motherDraft": mother_draft,
        "topic": topic,
        "persona": persona,
    }
    resp = requests.post(IMPORT_API, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    topic = sys.argv[2]
    persona = sys.argv[3] if len(sys.argv) > 3 else "普通人群"

    draft = extract_mother_draft(file_path)
    print(f"母稿长度：{len(draft)} 字符，主题：{topic}，人群：{persona}")

    result = import_mother(draft, topic, persona)
    print(f"code={result.get('code')} message={result.get('message')}")
    print(f"qualityScore={result.get('qualityScore')} passed={result.get('passed')}")
    if result.get("errors"):
        print(f"errors={result.get('errors')}")
    print(f"topicGroupId={result.get('topicGroupId')}")
    for a in result.get("articles", []):
        print(f"  [{a.get('id')}] {a.get('title')} ({a.get('lengthType')}, {a.get('wordCount')}字)")
