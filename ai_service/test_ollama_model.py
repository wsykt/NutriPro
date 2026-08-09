"""Ollama 本地模型快速测试脚本"""
import requests, time, json

BASE_URL = "http://localhost:11434"
MODEL = "qwen2.5-7b-local"

def test_basic_chat():
    print("=== 测试1: 基础对话 ===")
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/chat", json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "你好，请用中文介绍一下你自己，控制在50字以内。"}],
        "stream": False,
        "options": {"temperature": 0.3}
    }, timeout=120)
    elapsed = time.time() - t0
    if r.status_code == 200:
        data = r.json()
        print(f"回答: {data['message']['content']}")
        usage = data.get("usage", {})
        print(f"耗时: {elapsed:.2f}s | Token: {usage.get('total_tokens', 'N/A')}")
        print(f"prompt_eval: {usage.get('prompt_eval_count', 'N/A')} | eval_count: {usage.get('eval_count', 'N/A')}")
        print(f"速度: {usage.get('eval_duration', 0) / 1e9:.2f}s 推理时间")
        return True
    else:
        print(f"错误: HTTP {r.status_code} {r.text[:200]}")
        return False

def test_nutrition_chat():
    print("\n=== 测试2: 营养咨询 ===")
    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/chat", json={
        "model": MODEL,
        "messages": [{"role": "user", "content": "健身爱好者每天需要多少蛋白质？请给出具体数值范围。"}],
        "stream": False,
        "options": {"temperature": 0.3}
    }, timeout=120)
    elapsed = time.time() - t0
    if r.status_code == 200:
        data = r.json()
        content = data["message"]["content"]
        print(f"回答: {content[:300]}")
        if len(content) > 300:
            print(f"  ... (共 {len(content)} 字)")
        usage = data.get("usage", {})
        print(f"耗时: {elapsed:.2f}s | Token: {usage.get('total_tokens', 'N/A')}")
        return True
    else:
        print(f"错误: HTTP {r.status_code} {r.text[:200]}")
        return False

def test_framework_generation():
    print("\n=== 测试3: 文章框架生成（核心功能） ===")
    prompt = """基于以下知识库素材，搭建一篇关于"青少年补钙"的科普文章框架。

知识库素材:
1. 钙是青少年骨骼发育的必需矿物质，推荐摄入量为 1000mg/天
2. 乳制品是最佳钙来源，每 100ml 牛奶约含 100mg 钙
3. 维生素 D 促进钙吸收，可通过日晒或补充剂获取
4. 青少年应避免过量摄入咖啡因和碳酸饮料，以免影响钙吸收
5. 运动（尤其是负重运动）有助于骨骼健康

请使用以下标签格式搭建框架，标签顺序不可调换：
【#标题#】
【#核心观点#】
【#科学依据#】
【#膳食建议#】
【#风险提示#】
【#总结#】"""

    t0 = time.time()
    r = requests.post(f"{BASE_URL}/api/chat", json={
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一位严谨的营养学科普编辑，负责搭建文章框架。严格固定文章板块标签，板块顺序不可调换、标签字符不允许修改。【#标记名#】必须独占完整一行，必须使用【】符号包裹。仅基于提供的本地知识库素材搭建框架，不引入外部文献。"},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {"temperature": 0.3, "num_ctx": 2048}
    }, timeout=120)
    elapsed = time.time() - t0
    if r.status_code == 200:
        data = r.json()
        content = data["message"]["content"]
        print(f"回答:\n{content}")
        usage = data.get("usage", {})
        print(f"\n耗时: {elapsed:.2f}s | Token: {usage.get('total_tokens', 'N/A')}")
        return True
    else:
        print(f"错误: HTTP {r.status_code} {r.text[:200]}")
        return False

def test_rag():
    print("\n=== 测试4: RAG 检索增强生成 ===")
    try:
        import sys, os
        ai_service_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(ai_service_dir)
        sys.path.insert(0, ai_service_dir)
        from services.retrieval_service import retrieve_knowledge
        
        query = "孕妇叶酸补充建议"
        results = retrieve_knowledge(query, persona="孕妇", top_k=3)
        print(f"检索查询: {query}")
        print(f"找到 {len(results)} 条相关内容")
        
        context_parts = []
        for i, r_item in enumerate(results[:3]):
            content = r_item.get("content", "")[:150]
            metadata = r_item.get("metadata", {})
            source = metadata.get("source", "未知")
            topic = metadata.get("category", "")
            print(f"  [{i+1}] {topic}: {content}...")
            context_parts.append(f"[{source}] {r_item.get('content', '')[:200]}")
        
        if context_parts:
            context = "\n".join(context_parts)
            rag_prompt = f"""基于以下知识库内容回答问题：
{context}

问题：{query}

请基于知识库资料回答，如果知识库没有相关信息请说明。"""
            
            t0 = time.time()
            r = requests.post(f"{BASE_URL}/api/chat", json={
                "model": MODEL,
                "messages": [{"role": "user", "content": rag_prompt}],
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 4096}
            }, timeout=120)
            elapsed = time.time() - t0
            
            if r.status_code == 200:
                answer = r.json()["message"]["content"]
                print(f"\nRAG 回答: {answer[:300]}")
                print(f"耗时: {elapsed:.2f}s")
                return True
            else:
                print(f"LLM 错误: HTTP {r.status_code}")
                return False
        else:
            print("知识库无相关内容，跳过 RAG 测试")
            return None
    except ImportError as e:
        print(f"检索服务不可用: {e}")
        return None
    except Exception as e:
        print(f"RAG 测试异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Ollama 本地模型测试")
    print(f"模型: {MODEL}")
    print("=" * 60)
    
    results = {}
    results["基础对话"] = test_basic_chat()
    results["营养咨询"] = test_nutrition_chat()
    results["框架生成"] = test_framework_generation()
    results["RAG检索"] = test_rag()
    
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)
    for name, ok in results.items():
        status = "✅ 通过" if ok else ("⚠️  跳过" if ok is None else "❌ 失败")
        print(f"  {name}: {status}")
