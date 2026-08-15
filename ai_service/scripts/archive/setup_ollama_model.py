"""
Ollama 本地模型配置与验证脚本
============================
将用户指定的 GGUF 模型注册到 Ollama，并测试基础功能。
"""

import requests
import time
import os
import subprocess

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5-7b-local"  # Ollama 中的模型名称
MODELFILE_PATH = r"C:\ai-models\qwen25-7b\Modelfile"
GGUF_PATH = r"C:\ai-models\qwen25-7b\Qwen2.5-7B-Instruct-Q4_K_M.gguf"

def check_ollama_service():
    """检查 Ollama 服务状态"""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = resp.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f"✅ Ollama 服务运行中，可用模型: {model_names}")
            return True, model_names
        return False, []
    except requests.exceptions.ConnectionError:
        print("❌ Ollama 服务未启动")
        print("   请运行: ollama serve")
        return False, []

def create_model():
    """使用 Modelfile 创建 Ollama 模型"""
    print(f"\n📦 创建模型: {MODEL_NAME}")
    print(f"   模型文件: {GGUF_PATH}")
    print(f"   配置文件: {MODELFILE_PATH}")
    
    # 检查 GGUF 文件是否存在
    if not os.path.exists(GGUF_PATH):
        print(f"❌ GGUF 文件不存在: {GGUF_PATH}")
        return False
    
    # 检查 Modelfile 是否存在
    if not os.path.exists(MODELFILE_PATH):
        print(f"❌ Modelfile 不存在: {MODELFILE_PATH}")
        return False
    
    # 使用 ollama create 创建模型
    cmd = f'ollama create {MODEL_NAME} -f "{MODELFILE_PATH}"'
    print(f"\n执行命令: {cmd}")
    print("（首次创建需要几分钟，请耐心等待）")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        if result.returncode == 0:
            print("✅ 模型创建成功！")
            return True
        else:
            print(f"❌ 模型创建失败: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ 模型创建超时，请检查 Ollama 是否正常运行")
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False

def test_model():
    """测试模型对话功能"""
    print(f"\n🧪 测试模型: {MODEL_NAME}")
    
    test_cases = [
        ("基础对话", "你好，请简单介绍一下你自己。"),
        ("营养咨询", "我是一个健身爱好者，每天需要多少蛋白质？"),
        ("数据分析", "分析以下数据：鸡胸肉100g含蛋白质31g、脂肪3.6g、能量165kcal。这是高蛋白食物吗？"),
    ]
    
    for case_name, question in test_cases:
        print(f"\n--- 测试: {case_name} ---")
        print(f"问题: {question}")
        
        try:
            start = time.time()
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_NAME,
                    "messages": [{"role": "user", "content": question}],
                    "stream": False,
                    "options": {"temperature": 0.3}
                },
                timeout=60
            )
            elapsed = time.time() - start
            
            if resp.status_code == 200:
                result = resp.json()
                answer = result.get('message', {}).get('content', '')
                tokens = result.get('usage', {}).get('total_tokens', 0)
                print(f"✅ 回答: {answer[:150]}...")
                print(f"   耗时: {elapsed:.2f}s | Token: {tokens}")
            else:
                print(f"❌ 错误: HTTP {resp.status_code}")
                print(f"   {resp.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏰ 响应超时（60秒）")
        except Exception as e:
            print(f"❌ 异常: {e}")

def test_rag_capability():
    """测试 RAG 检索能力（结合知识库）"""
    print(f"\n🔍 测试 RAG 检索能力")
    
    from services.retrieval_service import retrieval_service
    
    # 检索测试
    query = "孕妇叶酸补充建议"
    results = retrieval_service.search(query, target_crowd="孕妇", top_k=3)
    
    print(f"\n检索查询: {query}")
    print(f"找到 {len(results.get('results', []))} 条相关内容:")
    for i, r in enumerate(results.get('results', [])[:3]):
        content = r.get('content', '')[:100]
        print(f"  [{i+1}] {r.get('topic', '')}: {content}...")
    
    # RAG 问答测试
    context = "\n".join([r.get('content', '')[:200] for r in results.get('results', [])[:3]])
    prompt = f"""基于以下知识库内容回答问题：
    {context}
    
    问题：{query}"""
    
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.3, "num_ctx": 4096}
            },
            timeout=60
        )
        
        if resp.status_code == 200:
            answer = resp.json().get('message', {}).get('content', '')
            print(f"\n🤖 RAG回答: {answer[:300]}...")
            
    except Exception as e:
        print(f"❌ RAG 测试异常: {e}")

def update_config():
    """更新 ollama_service.py 配置"""
    service_path = r"c:\Users\13425\Desktop\个人健康助手\health\ai_service\ollama_service.py"
    
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新默认模型名称
    old_default = 'DEFAULT_MODEL = "qwen2.5:7b"'
    new_default = f'DEFAULT_MODEL = "{MODEL_NAME}"'
    
    if old_default in content:
        content = content.replace(old_default, new_default)
        with open(service_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ 已更新 ollama_service.py 默认模型为: {MODEL_NAME}")
    else:
        print(f"\n⚠️  未找到需要更新的配置行")

if __name__ == '__main__':
    print("=" * 60)
    print("Ollama 本地模型配置与验证")
    print("=" * 60)
    
    # Step 1: 检查 Ollama 服务
    print("\n【Step 1】检查 Ollama 服务...")
    running, existing_models = check_ollama_service()
    
    if not running:
        print("\n请先启动 Ollama 服务:")
        print("  1. 打开新的 PowerShell 窗口")
        print("  2. 运行: ollama serve")
        print("  3. 等待服务启动后，回到此处重新运行")
    else:
        # Step 2: 检查/创建模型
        if MODEL_NAME in existing_models:
            print(f"\n✅ 模型 {MODEL_NAME} 已存在")
        else:
            print(f"\n【Step 2】创建新模型...")
            if create_model():
                print("\n✅ 模型创建成功")
            else:
                print("\n❌ 模型创建失败，后续步骤跳过")
                exit(1)
        
        # Step 3: 更新配置
        print(f"\n【Step 3】更新配置文件...")
        update_config()
        
        # Step 4: 测试模型
        print(f"\n【Step 4】测试模型对话...")
        test_model()
        
        # Step 5: 测试 RAG
        print(f"\n【Step 5】测试 RAG 检索...")
        test_rag_capability()
    
    print("\n" + "=" * 60)
    print("配置完成！")
    print("=" * 60)
