"""
Ollama 本地大模型集成服务
============================
功能：
1. 用户对话交互系统（上下文感知）
2. 数据分析引擎（解析结构化与非结构化数据）
3. 日常需求满足模块（基于知识库的问答）
"""

import requests
import json
import time
import logging
from typing import List, Dict, Optional, Generator

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ollama 服务配置
OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-7b-local"  # 本地 GGUF 模型（4-bit 量化，6G 显存安全）

# RAG 相关配置
# 假设 retrieval_service 在 ai_service/services/ 下
import sys
import os
AI_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AI_SERVICE_DIR)

# 性能指标追踪
class PerformanceMonitor:
    """简易性能监控器"""
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0,
            'token_usage': 0
        }
    
    def record_request(self, response_time_ms, token_usage, success=True):
        self.metrics['total_requests'] += 1
        if success:
            self.metrics['successful_requests'] += 1
        else:
            self.metrics['failed_requests'] += 1
        self.metrics['total_response_time'] += response_time_ms
        self.metrics['token_usage'] += token_usage
    
    def get_report(self):
        total = self.metrics['total_requests']
        avg_time = self.metrics['total_response_time'] / total if total > 0 else 0
        return {
            '总请求数': total,
            '成功请求数': self.metrics['successful_requests'],
            '失败请求数': self.metrics['failed_requests'],
            '平均响应时间': f"{avg_time:.2f} ms",
            '总Token使用量': self.metrics['token_usage']
        }

# 全局监控器
monitor = PerformanceMonitor()

class OllamaService:
    """Ollama 本地大模型服务封装"""
    
    def __init__(self, model_name=DEFAULT_MODEL):
        self.base_url = OLLAMA_BASE_URL
        self.model_name = model_name
        self.conversation_history: List[Dict] = []
        self._check_service()
        
    def _check_service(self):
        """检查 Ollama 服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                data = response.json()
                available_models = [m['name'] for m in data.get('models', [])]
                logger.info(f"Ollama 服务运行中，可用模型: {available_models}")
                if self.model_name not in available_models:
                    logger.warning(f"模型 {self.model_name} 未找到，可用模型: {available_models}")
                    logger.info(f"请运行: ollama pull {self.model_name}")
        except requests.exceptions.ConnectionError:
            logger.error(f"无法连接到 Ollama 服务 ({self.base_url})")
            logger.error("请确保 Ollama 已启动: ollama serve")
            logger.error(f"并已拉取模型: ollama pull {self.model_name}")
    
    def chat(self, user_message: str, system_prompt: str = None, 
             use_history: bool = True, temperature: float = 0.7) -> Dict:
        """
        用户对话交互（非流式）
        """
        start_time = time.time()
        
        # 构建消息列表
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if use_history:
            messages.extend(self.conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": 2048
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('message', {}).get('content', '')
                token_usage = result.get('usage', {}).get('total_tokens', 0)
                
                # 更新对话历史
                if use_history:
                    self.conversation_history.append({"role": "user", "content": user_message})
                    self.conversation_history.append({"role": "assistant", "content": response_text})
                
                response_time_ms = (time.time() - start_time) * 1000
                monitor.record_request(response_time_ms, token_usage, True)
                
                return {
                    'success': True,
                    'response': response_text,
                    'token_usage': token_usage,
                    'response_time_ms': round(response_time_ms, 2)
                }
            else:
                logger.error(f"Ollama 响应错误: {response.status_code}")
                monitor.record_request(0, 0, False)
                return {'success': False, 'error': '模型响应错误'}
                
        except requests.exceptions.Timeout:
            logger.error("请求超时")
            monitor.record_request(30000, 0, False)
            return {'success': False, 'error': '请求超时'}
        except Exception as e:
            logger.error(f"请求异常: {e}")
            monitor.record_request(0, 0, False)
            return {'success': False, 'error': str(e)}
    
    def chat_stream(self, user_message: str, system_prompt: str = None,
                    use_history: bool = True) -> Generator:
        """
        用户对话交互（流式）
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if use_history:
            messages.extend(self.conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "stream": True,
                    "options": {"temperature": 0.7}
                },
                stream=True,
                timeout=60
            )
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if 'message' in data and 'content' in data['message']:
                        chunk = data['message']['content']
                        full_response += chunk
                        yield {'content': chunk, 'done': False}
                    if data.get('done', False):
                        if use_history:
                            self.conversation_history.append({"role": "user", "content": user_message})
                            self.conversation_history.append({"role": "assistant", "content": full_response})
                        yield {'content': '', 'done': True}
                        
        except Exception as e:
            logger.error(f"流式请求异常: {e}")
            yield {'content': f'请求失败: {str(e)}', 'done': True}
    
    def analyze_data(self, data_input: str, analysis_type: str = 'general') -> Dict:
        """
        数据分析引擎：解析结构化与非结构化数据
        """
        prompts = {
            'general': "请分析以下数据，并提供关键洞察和总结：\n\n",
            'nutrition': "请分析以下营养数据，评估营养状况并提供建议：\n\n",
            'health': "请分析以下健康数据，识别潜在风险并提供健康建议：\n\n",
            'recipe': "请分析以下食谱数据，计算营养成分并评估健康价值：\n\n"
        }
        
        system_prompt = """你是一个专业的数据分析助手，擅长从各种数据中提取关键信息，
        并以清晰、结构化的方式呈现分析结果。请用中文回答。"""
        
        full_prompt = prompts.get(analysis_type, prompts['general']) + data_input
        
        result = self.chat(full_prompt, system_prompt=system_prompt, use_history=False)
        result['analysis_type'] = analysis_type
        return result
    
    def rag_chat(self, user_question: str, top_k: int = 3) -> Dict:
        """
        基于知识库的 RAG 对话（检索增强生成）
        """
        try:
            # 尝试导入检索服务
            from services.retrieval_service import retrieval_service
            
            # 步骤1：从知识库检索相关内容
            search_results = retrieval_service.search(
                query=user_question,
                top_k=top_k
            )
            
            # 步骤2：构建包含检索结果的提示词
            context_texts = []
            for result in search_results.get('results', []):
                context_texts.append(f"[来源: {result.get('source_channel', '未知')}] {result.get('content', '')}")
            
            context = "\n\n".join(context_texts) if context_texts else "（暂无相关知识库内容）"
            
            system_prompt = f"""你是个人健康助手的AI营养师。请严格基于以下知识库资料回答用户问题。
            如果知识库中没有相关信息，请说明"根据现有知识库，暂无相关信息"。
            回答要专业、准确、易于理解。"""
            
            prompt = f"""知识库资料：
            {context}
            
            用户问题：{user_question}
            
            请基于知识库资料回答问题："""
            
            result = self.chat(prompt, system_prompt=system_prompt, use_history=True)
            result['rag_sources'] = search_results.get('results', [])
            result['context_used'] = bool(context_texts)
            return result
            
        except ImportError:
            logger.warning("检索服务不可用，回退到纯LLM对话")
            return self.chat(user_question, use_history=True)
        except Exception as e:
            logger.error(f"RAG对话异常: {e}")
            return self.chat(user_question, use_history=True)
    
    def get_health_advice(self, user_profile: Dict) -> Dict:
        """
        日常需求满足模块：根据用户档案生成个性化健康建议
        """
        profile_text = f"""用户档案：
        - 性别：{user_profile.get('gender', '未知')}
        - 年龄：{user_profile.get('age', '未知')}岁
        - 身高：{user_profile.get('height', '未知')}cm
        - 体重：{user_profile.get('weight', '未知')}kg
        - 活动水平：{user_profile.get('activity_level', '未知')}
        - 健康目标：{user_profile.get('goal', '未知')}
        - 特殊人群：{user_profile.get('crowd_type', '无')}"""
        
        system_prompt = """你是个人健康助手的AI营养师。请根据用户档案，
        提供个性化的营养和健康建议。建议包括：
        1. 每日能量需求估算
        2. 核心营养素需求量
        3. 膳食模式建议
        4. 运动指导
        5. 需要注意的风险点"""
        
        result = self.chat(profile_text, system_prompt=system_prompt, use_history=False)
        result['advice_type'] = 'personalized_health_advice'
        return result
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
        logger.info("对话历史已重置")
    
    def get_performance_report(self):
        """获取性能报告"""
        return monitor.get_report()

# ========== 测试示例 ==========
if __name__ == '__main__':
    print("=" * 60)
    print("Ollama 本地大模型服务测试")
    print("=" * 60)
    
    # 初始化服务
    ollama = OllamaService(model_name="qwen2.5-7b-local")
    
    # 测试1：基础对话
    print("\n【测试1】基础对话")
    result = ollama.chat("你好，请简单介绍一下你自己。", use_history=False)
    if result['success']:
        print(f"AI: {result['response'][:100]}...")
        print(f"耗时: {result['response_time_ms']}ms")
        print(f"Token: {result['token_usage']}")
    
    # 测试2：数据分析
    print("\n【测试2】营养数据分析")
    test_data = """
    食物：鸡胸肉（100g）
    - 能量：165 kcal
    - 蛋白质：31 g
    - 脂肪：3.6 g
    - 碳水化合物：0 g
    - 钠：64 mg
    """
    result = ollama.analyze_data(test_data, analysis_type='nutrition')
    if result['success']:
        print(f"AI分析: {result['response'][:200]}...")
    
    # 测试3：健康建议生成
    print("\n【测试3】个性化健康建议")
    user_profile = {
        'gender': '男',
        'age': 28,
        'height': 175,
        'weight': 70,
        'activity_level': '中度活动',
        'goal': '保持健康',
        'crowd_type': '普通人群'
    }
    result = ollama.get_health_advice(user_profile)
    if result['success']:
        print(f"建议生成: {len(result['response'])} 字")
        print(f"内容摘要: {result['response'][:150]}...")
    
    # 测试4：性能报告
    print("\n【性能报告】")
    report = ollama.get_performance_report()
    for key, value in report.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示：")
    print("1. 当前使用本地 GGUF 模型: qwen2.5-7b-local (基于 Qwen2.5-7B-Instruct-Q4_K_M)")
    print("2. 如果需要嵌入功能，可改用: ollama pull bge-m3")
    print("3. 更高质量模型: ollama pull qwen2.5:14b (需要更多显存)")