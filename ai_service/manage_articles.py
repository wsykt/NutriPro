# -*- coding: utf-8 -*-
"""
文章管理脚本：列出 / 删除 / 导入母稿（对接后端API）
用法：
    python manage_articles.py list                     # 列出所有文章
    python manage_articles.py delete <id> [id...]      # 删除指定id的文章
    python manage_articles.py delete-topic <topic>     # 按主题删除文章
    python manage_articles.py clear-all                # 清空全部文章（二次确认）
    python manage_articles.py import <pipeline文件> <topic> <persona>   # 导入母稿
"""
import sys
import requests

BACKEND = "http://localhost:8082"
ARTICLES_API = BACKEND + "/api/articles"
IMPORT_API = BACKEND + "/api/articles/import-mother"


def list_articles():
    r = requests.get(ARTICLES_API, timeout=10)
    arts = r.json()
    print("文章总数:", len(arts))
    for a in arts:
        print("  [%s] %s | lenType=%s | topicGroup=%s | status=%s | cat=%s" % (
            a.get("id"), (a.get("title") or "")[:45], a.get("lengthType"),
            a.get("topicGroupId"), a.get("status"), a.get("category")))
    return arts


def delete_article(aid):
    r = requests.delete("%s/%s" % (ARTICLES_API, aid), timeout=10)
    return r.status_code


def import_mother(file_path, topic, persona):
    from import_mother_to_backend import extract_mother_draft
    draft = extract_mother_draft(file_path)
    print("母稿长度: %d 字符" % len(draft))
    payload = {"motherDraft": draft, "topic": topic, "persona": persona}
    r = requests.post(IMPORT_API, json=payload, timeout=30)
    result = r.json()
    print("code=%s message=%s" % (result.get("code"), result.get("message")))
    print("qualityScore=%s passed=%s" % (result.get("qualityScore"), result.get("passed")))
    if result.get("errors"):
        print("errors:", result.get("errors"))
    print("topicGroupId=%s" % result.get("topicGroupId"))
    for a in result.get("articles", []):
        print("  [%s] %s (%s, %s字)" % (a.get("id"), a.get("title"), a.get("lengthType"), a.get("wordCount")))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "list":
        list_articles()
    elif args[0] == "delete":
        ids = [int(x) for x in args[1:]]
        for i in ids:
            code = delete_article(i)
            print("删除 [%s]: HTTP %s" % (i, code))
    elif args[0] == "delete-topic" and len(args) >= 2:
        topic = args[1]
        arts = list_articles()
        hits = [a for a in arts if topic in (a.get("topic") or "") or topic in (a.get("title") or "")]
        print("\n匹配 %s 篇文章，执行删除..." % len(hits))
        for a in hits:
            code = delete_article(a["id"])
            print("  删除 [%s] %s: HTTP %s" % (a["id"], (a.get("title") or "")[:40], code))
    elif args[0] == "clear-all":
        arts = list_articles()
        print("\n将删除全部 %d 篇文章！" % len(arts))
        for a in arts:
            code = delete_article(a["id"])
            print("  删除 [%s]: HTTP %s" % (a["id"], code))
    elif args[0] == "import" and len(args) >= 4:
        import_mother(args[1], args[2], args[3])
    else:
        print(__doc__)
