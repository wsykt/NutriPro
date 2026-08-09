# -*- coding: utf-8 -*-
"""汇总脚本测试 + 真实环境测试两份 JSON，输出统计摘要"""
import json, os, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "single_user_test")

def summarize(name, path):
    data = json.load(open(path, encoding="utf-8"))
    print(f"==== {name} ({len(data)} cases) ====")
    for r in data:
        issues = r.get("valid_issues") or []
        print(f"  {r['case_id']:38s} route={str(r['route']):18s} valid={r['valid_passed']} "
              f"{r['elapsed_sec']:6.1f}s issues={issues}")
    print()
    return data

def main():
    script = None
    real = None
    for root, _, files in os.walk(BASE):
        for f in files:
            if f.startswith("run_") and f.endswith(".json"):
                p = os.path.join(root, f)
                if "script_test" in p:
                    script = summarize("SCRIPT_TEST", p)
                elif "real_env_test" in p:
                    real = summarize("REAL_ENV_TEST", p)
    if script:
        _stats("脚本测试", script)
    if real:
        _stats("真实环境测试", real)

def _stats(name, rows):
    total = len(rows)
    ok = sum(1 for r in rows if r["valid_passed"])
    err = sum(1 for r in rows if r["route"] == "ERROR")
    hp = [r for r in rows if r["mode"] == "high_performance"]
    nm = [r for r in rows if r["mode"] == "normal"]
    routes = {}
    for r in rows:
        routes[r["route"]] = routes.get(r["route"], 0) + 1
    avg_all = sum(r["elapsed_sec"] for r in rows) / total
    avg_hp = sum(r["elapsed_sec"] for r in hp) / len(hp) if hp else 0
    avg_nm = sum(r["elapsed_sec"] for r in nm) / len(nm) if nm else 0
    print(f"---- {name} 汇总 ----")
    print(f"  用例 {total} | 通过 {ok} | 失败 {err} | 路由分布 {routes}")
    print(f"  平均耗时 {avg_all:.1f}s | 高性能 {avg_hp:.1f}s | 正常模式 {avg_nm:.1f}s")
    print()

if __name__ == "__main__":
    main()
