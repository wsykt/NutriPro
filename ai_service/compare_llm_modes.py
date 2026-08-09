# -*- coding: utf-8 -*-
"""
云端 vs 本地大模型 对比测试脚本
================================
调用现有 API 端点（沿用项目自带的提示词和知识库），
对比 DeepSeek 云端 API 与 Ollama 本地大模型两种方案。

用法：
    python compare_llm_modes.py --mode cloud    # 测试云端模式
    python compare_llm_modes.py --mode local    # 测试本地模式
    python compare_llm_modes.py --report        # 生成对比报告（需两种模式都跑过）

测试场景（全部沿用现有 API 端点和提示词）：
    1. /api/v1/chat              健康咨询对话
    2. /api/v1/diet/plan         饮食方案生成
    3. /api/v1/exercise/advice   运动方案生成
    4. /api/v1/food/recommend    食材菜谱推荐
"""
import argparse
import json
import os
import sys
import time
import requests
from datetime import datetime

API_BASE = "http://localhost:8002"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output", "llm_compare")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# 测试用例（沿用项目现有 API 端点和输入格式）
# ============================================================
TEST_CASES = [
    {
        "name": "健康咨询对话",
        "endpoint": "/api/v1/chat",
        "payload": {
            "message": "我今年35岁，男性，最近体检发现血脂偏高，日常饮食应该注意什么？",
            "user_id": 0,
            "health_snapshot": {
                "profile": {
                    "gender": "男", "age": 35, "height_cm": 175,
                    "weight_kg": 80, "bmi": 26.1, "crowdType": "普通人"
                }
            }
        },
        "extract": lambda r: r.get("data", {}).get("response", "") if isinstance(r.get("data"), dict) else str(r.get("data", "")),
        "extra_info": lambda r: {
            "provider": r.get("data", {}).get("provider") if isinstance(r.get("data"), dict) else "",
            "retrieve_info_count": len(r.get("data", {}).get("retrieve_info") or []) if isinstance(r.get("data"), dict) else 0,
            "timing": r.get("data", {}).get("timing_breakdown") if isinstance(r.get("data"), dict) else {},
        },
    },
    {
        "name": "饮食方案生成",
        "endpoint": "/api/v1/diet/plan",
        "payload": {
            "user_profile": {
                "gender": "女", "age": 28, "height": 165, "weight": 58,
                "bmi": 21.3, "crowd_type": "孕妇", "activity_level": "轻度活动"
            },
            "goal": "孕期营养均衡"
        },
        "extract": lambda r: json.dumps(r.get("data", r), ensure_ascii=False, indent=2)[:1500],
        "extra_info": lambda r: {"is_dict": isinstance(r.get("data"), dict)},
    },
    {
        "name": "运动方案生成",
        "endpoint": "/api/v1/exercise/advice",
        "payload": {
            "user_profile": {
                "gender": "男", "age": 45, "height": 170, "weight": 78,
                "bmi": 26.9, "crowd_type": "普通人"
            },
            "goal": "减脂",
            "preferences": "喜欢跑步和游泳",
            "chronic_diseases": ["高血压"]
        },
        "extract": lambda r: json.dumps(r.get("data", r), ensure_ascii=False, indent=2)[:1500],
        "extra_info": lambda r: {"has_schedule": isinstance(r.get("data"), dict) and "weekly_schedule" in (r.get("data") or {})},
    },
    {
        "name": "食材菜谱推荐",
        "endpoint": "/api/v1/food/recommend",
        "payload": {
            "ingredients": ["鸡胸肉", "西兰花", "糙米"],
            "crowd_type": "健身",
            "goal": "高蛋白低脂"
        },
        "extract": lambda r: json.dumps(r.get("data", r), ensure_ascii=False, indent=2)[:1500],
        "extra_info": lambda r: {"is_dict": isinstance(r.get("data"), dict)},
    },
]


def call_api(endpoint: str, payload: dict, timeout: int = 120) -> dict:
    """调用 API 端点"""
    url = f"{API_BASE}{endpoint}"
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        return resp.json() if resp.status_code == 200 else {"error": f"HTTP {resp.status_code}", "body": resp.text[:300]}
    except requests.exceptions.Timeout:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


def run_tests(mode: str) -> list:
    """运行所有测试用例"""
    print(f"\n{'='*70}")
    print(f"  测试模式: {mode}（调用 {API_BASE}）")
    print(f"{'='*70}")

    results = []
    for tc in TEST_CASES:
        print(f"\n[{tc['name']}] 调用 {tc['endpoint']} ...")
        start = time.time()
        raw = call_api(tc["endpoint"], tc["payload"])
        elapsed = round(time.time() - start, 2)

        content = tc["extract"](raw)
        extra = tc["extra_info"](raw)
        is_error = isinstance(raw, dict) and raw.get("error")

        result = {
            "name": tc["name"],
            "endpoint": tc["endpoint"],
            "mode": mode,
            "elapsed_seconds": elapsed,
            "success": not is_error,
            "content": content,
            "content_length": len(content) if content else 0,
            "extra_info": extra,
            "raw_error": raw.get("error") if is_error else None,
            "timestamp": datetime.now().isoformat(),
        }
        results.append(result)

        status = "✓" if not is_error else "✗"
        print(f"  {status} 耗时 {elapsed}s | 内容长度 {result['content_length']} 字")
        if is_error:
            print(f"    错误: {raw.get('error')}")
        else:
            print(f"    预览: {content[:120]}...")

    return results


def save_results(mode: str, results: list):
    """保存单次测试结果"""
    path = os.path.join(OUTPUT_DIR, f"results_{mode}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存: {path}")


def generate_report():
    """生成对比报告"""
    cloud_path = os.path.join(OUTPUT_DIR, "results_cloud.json")
    local_path = os.path.join(OUTPUT_DIR, "results_local.json")

    if not os.path.exists(cloud_path) or not os.path.exists(local_path):
        print("需要先运行两种模式的测试：")
        print("  python compare_llm_modes.py --mode cloud")
        print("  python compare_llm_modes.py --mode local")
        return

    with open(cloud_path, "r", encoding="utf-8") as f:
        cloud = json.load(f)
    with open(local_path, "r", encoding="utf-8") as f:
        local = json.load(f)

    report_path = os.path.join(OUTPUT_DIR, "comparison_report.md")
    lines = []
    lines.append("# 云端 API vs 本地大模型 对比测试报告\n")
    lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"云端模型: DeepSeek (deepseek-chat)")
    lines.append(f"本地模型: Ollama qwen2.5-7b-local (Q4_K_M 4-bit 量化, 上下文 2048)\n")
    lines.append(f"知识库: ChromaDB {3022} 条文档（共用）\n")
    lines.append("---\n")

    # 1. 总览对比表
    lines.append("## 一、总体对比\n")
    lines.append("| 测试场景 | 云端耗时(s) | 本地耗时(s) | 云端内容长度 | 本地内容长度 | 云端成功 | 本地成功 |")
    lines.append("|----------|------------|------------|-------------|-------------|---------|---------|")
    for c, l in zip(cloud, local):
        lines.append(
            f"| {c['name']} | {c['elapsed_seconds']} | {l['elapsed_seconds']} | "
            f"{c['content_length']}字 | {l['content_length']}字 | "
            f"{'✓' if c['success'] else '✗'} | {'✓' if l['success'] else '✗'} |"
        )
    lines.append("")

    # 2. 耗时对比
    cloud_times = [r["elapsed_seconds"] for r in cloud if r["success"]]
    local_times = [r["elapsed_seconds"] for r in local if r["success"]]
    lines.append("## 二、耗时分析\n")
    if cloud_times and local_times:
        lines.append(f"- 云端平均耗时: {sum(cloud_times)/len(cloud_times):.2f}s")
        lines.append(f"- 本地平均耗时: {sum(local_times)/len(local_times):.2f}s")
        lines.append(f"- 云端总耗时: {sum(cloud_times):.2f}s")
        lines.append(f"- 本地总耗时: {sum(local_times):.2f}s")
        ratio = sum(local_times) / sum(cloud_times) if sum(cloud_times) > 0 else 0
        lines.append(f"- 本地/云端耗时比: {ratio:.1f}x\n")

    # 3. 内容质量对比
    lines.append("## 三、内容质量对比\n")
    for c, l in zip(cloud, local):
        lines.append(f"### {c['name']}\n")
        lines.append(f"**云端 (DeepSeek) — {c['elapsed_seconds']}s, {c['content_length']}字**\n")
        lines.append("```\n" + (c["content"][:800] if c["content"] else "(无内容/失败)") + "\n```\n")
        lines.append(f"**本地 (Ollama) — {l['elapsed_seconds']}s, {l['content_length']}字**\n")
        lines.append("```\n" + (l["content"][:800] if l["content"] else "(无内容/失败)") + "\n```\n")

        # 质量评估
        notes = []
        if c["success"] and l["success"]:
            if c["content_length"] > l["content_length"] * 1.5:
                notes.append("云端输出更详尽")
            elif l["content_length"] > c["content_length"] * 1.5:
                notes.append("本地输出更详尽")
            if c["elapsed_seconds"] < l["elapsed_seconds"]:
                notes.append("云端响应更快")
            else:
                notes.append("本地响应更快")
        elif c["success"] and not l["success"]:
            notes.append("本地失败，云端成功")
        elif l["success"] and not c["success"]:
            notes.append("云端失败，本地成功")
        if notes:
            lines.append(f"**评估**: {'; '.join(notes)}\n")
        lines.append("---\n")

    # 4. 结论
    lines.append("## 四、综合结论\n")
    cloud_success = sum(1 for r in cloud if r["success"])
    local_success = sum(1 for r in local if r["success"])
    lines.append(f"- 成功率: 云端 {cloud_success}/{len(cloud)}, 本地 {local_success}/{len(local)}")
    if cloud_times and local_times:
        lines.append(f"- 响应速度: 云端 {sum(cloud_times)/len(cloud_times):.1f}s avg, "
                     f"本地 {sum(local_times)/len(local_times):.1f}s avg")
    cloud_avg_len = sum(r["content_length"] for r in cloud if r["success"]) / max(cloud_success, 1)
    local_avg_len = sum(r["content_length"] for r in local if r["success"]) / max(local_success, 1)
    lines.append(f"- 输出丰富度: 云端 avg {cloud_avg_len:.0f}字, 本地 avg {local_avg_len:.0f}字")
    lines.append(f"- 成本: 云端按 Token 计费, 本地零成本（仅需电费）")
    lines.append(f"- 隐私: 云端数据需上传, 本地完全离线")
    lines.append(f"- 部署门槛: 云端仅需 API Key, 本地需 6GB+ 显存 GPU\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n对比报告已生成: {report_path}")
    print("=" * 70)
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="云端 vs 本地大模型对比测试")
    parser.add_argument("--mode", choices=["cloud", "local"], help="测试模式")
    parser.add_argument("--report", action="store_true", help="生成对比报告")
    args = parser.parse_args()

    if args.report:
        generate_report()
    elif args.mode:
        # 检查服务是否运行
        try:
            r = requests.get(f"{API_BASE}/health", timeout=5)
            if r.status_code != 200:
                print(f"服务未启动或异常（{API_BASE}/health 返回 {r.status_code}）")
                sys.exit(1)
        except Exception:
            print(f"无法连接到 {API_BASE}，请先启动 AI 服务")
            sys.exit(1)

        results = run_tests(args.mode)
        save_results(args.mode, results)
        print(f"\n{args.mode} 模式测试完成，共 {len(results)} 个场景")
