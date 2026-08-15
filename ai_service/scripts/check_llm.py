#!/usr/bin/env python3
"""检查 LLM 是否正常工作"""
import urllib.request, json, time

BASE = "http://localhost:8002"

# 简单问题
payload = {
    "message": "你好，请问鸡胸肉每100g多少卡路里？",
    "user_id": 1,
    "conversation_id": f"check_llm_{int(time.time())}",
}

req = urllib.request.Request(
    f"{BASE}/api/v1/chat",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    start = time.time()
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8")
        elapsed = round((time.time() - start) * 1000)
        d = json.loads(body)
        print(f"状态码: {resp.status}")
        print(f"耗时: {elapsed}ms")
        print(f"提供者: {d.get('provider', 'N/A')}")
        print(f"回答: {d.get('response', '')[:200]}")
except urllib.error.HTTPError as e:
    print(f"HTTP错误: {e.code}")
    print(e.read().decode()[:300])
except Exception as e:
    print(f"错误: {e}")
