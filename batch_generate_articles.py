# -*- coding: utf-8 -*-
"""
批量生成科普文章：6 个人群 × 4 主题 = 24 篇，串行调用后端同步接口
    POST http://localhost:8082/api/articles/generate   body={"topic","persona"}

设计：
- 串行生成（一次一篇），避免并发打爆 6GB 显存的 Ollama
- 断点续跑：成功记录写入 article_generation_progress.json，重跑自动跳过已完成
- 失败重试 1 次；仍失败则记录失败原因并继续下一篇
用法：python batch_generate_articles.py
"""
import datetime
import json
import os
import sys
import time

import requests

BACKEND = "http://localhost:8082/api/articles/generate"
AUTH_BASE = "http://localhost:8082/api/auth"
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "article_generation_progress.json")
HTTP_TIMEOUT = 390  # 单篇 B方案 约5分钟，含后端/AI 通信余量

# 批量生成专用账号（自动注册），用于通过 /api/articles/generate 的认证校验
AUTH_USER = "batchgen"
AUTH_PASS = "Batch123!"


def ensure_token():
    """登录拿 JWT；账号不存在则先注册再登录。返回 token 字符串。"""
    def _try_login():
        r = requests.post(f"{AUTH_BASE}/login",
                          json={"username": AUTH_USER, "password": AUTH_PASS}, timeout=15)
        if r.status_code == 200:
            body = r.json()
            data = body.get("data") or {}
            tok = (data.get("token") or data.get("access_token")
                   or data.get("accessToken") or "")
            if tok:
                return tok
        return ""

    tok = _try_login()
    if tok:
        return tok
    # 账号不存在或密码不匹配：注册后重登
    try:
        rr = requests.post(f"{AUTH_BASE}/register", json={
            "username": AUTH_USER, "password": AUTH_PASS,
            "gender": "男", "height": 170, "weight": 65, "age": 30,
            "crowdType": "普通人"}, timeout=15)
        print(f"注册响应：HTTP {rr.status_code} {str(rr.json())[:120]}", flush=True)
    except Exception as e:
        print(f"注册异常：{type(e).__name__}: {e}", flush=True)
    return _try_login()

# 人群限定：健身 / 普通 / 青少年 / 老年 / 孕妇 / 糖尿病（已按要求删除高血压等）
TOPICS = [
    ("健身", "健身人群", [
        "健身增肌期的蛋白质摄入指南",
        "运动前中后的营养补充策略",
        "减脂期的饮食控制与安排",
        "健身人群的微量营养素补充",
    ]),
    ("普通人", "普通人群", [
        "中国居民膳食指南与均衡膳食实践",
        "一日三餐的科学搭配方法",
        "膳食纤维与肠道健康",
        "健康减重的饮食策略",
    ]),
    ("青少年", "青少年", [
        "青春期生长发育的营养需求",
        "学生早餐与学习效率",
        "青少年骨骼健康与钙的补充",
        "青少年近视防控的营养策略",
    ]),
    ("老年", "老年人", [
        "老年人肌少症与优质蛋白质摄入",
        "骨质疏松的营养防治策略",
        "老年人咀嚼吞咽困难的营养调整",
        "老年人认知健康与营养干预",
    ]),
    ("孕妇", "孕妇", [
        "孕期补钙与胎儿骨骼发育",
        "孕期叶酸补充与神经管缺陷预防",
        "孕期贫血的补铁策略",
        "孕期体重管理与妊娠期糖尿病预防",
    ]),
    ("糖尿病", "糖尿病患者", [
        "糖尿病患者的日常饮食管理",
        "糖尿病主食选择与血糖生成指数",
        "糖尿病并发症的营养预防",
        "糖尿病外出就餐与零食选择",
    ]),
]


def load_done():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_done(done):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(done, f, ensure_ascii=False, indent=2)


def generate_one(topic, persona, token):
    resp = requests.post(BACKEND, json={"topic": topic, "persona": persona},
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=HTTP_TIMEOUT)
    return resp


def main():
    done = load_done()
    plan = [(crowd, persona, t) for crowd, persona, topics in TOPICS for t in topics]
    total = len(plan)
    ok_cnt = sum(1 for k, v in done.items() if v.get("status") == "success")
    print(f"计划 {total} 篇，已完成 {ok_cnt} 篇，开始时间 {datetime.datetime.now():%H:%M:%S}",
          flush=True)

    token = ensure_token()
    if not token:
        print("无法获取认证 token，退出", flush=True)
        return 1
    print(f"认证成功（{AUTH_USER}），开始生成", flush=True)

    for idx, (crowd, persona, topic) in enumerate(plan, 1):
        key = f"{crowd}|{topic}"
        if key in done and done[key].get("status") == "success":
            print(f"[{idx}/{total}] 跳过已完成：{crowd} / {topic}", flush=True)
            continue

        print(f"[{idx}/{total}] 开始：{crowd} / {topic}（{persona}） "
              f"{datetime.datetime.now():%H:%M:%S}", flush=True)
        t0 = time.time()
        ok, msg = False, ""
        for attempt in range(2):  # 失败重试 1 次
            try:
                r = generate_one(topic, persona, token)
                if r.status_code == 200:
                    ok, msg = True, "HTTP 200"
                    break
                if r.status_code in (401, 403):  # token 失效，刷新后再试
                    token = ensure_token()
                msg = f"HTTP {r.status_code}"
                try:
                    msg += " " + str(r.json())[:200]
                except Exception:
                    msg += " " + (r.text or "")[:120]
                time.sleep(8)
            except Exception as e:
                msg = f"EXC {type(e).__name__}: {e}"
                time.sleep(8)

        cost = time.time() - t0
        done[key] = {
            "status": "success" if ok else "failed",
            "msg": msg,
            "cost_s": round(cost, 1),
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        save_done(done)
        print(f"      {'成功' if ok else '失败'}：{msg}，耗时 "
              f"{int(cost // 60)}分{cost % 60:.0f}秒", flush=True)

    ok_cnt = sum(1 for v in done.values() if v.get("status") == "success")
    print(f"全部执行完毕：成功 {ok_cnt}/{total}，进度文件 {PROGRESS_FILE}", flush=True)


if __name__ == "__main__":
    main()
