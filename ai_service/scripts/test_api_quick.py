import requests

def test_chat():
    print("测试聊天API...")
    try:
        resp = requests.post('http://localhost:8002/api/v1/chat', json={'message': '苹果的热量是多少', 'user_id': 1})
        print(f'状态码: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'对话ID: {result.get("conversation_id")}')
            print(f'回复: {result.get("response", "")[:200]}')
        else:
            print(f'响应内容: {resp.text[:200]}')
    except Exception as e:
        print(f'测试失败: {e}')

def test_nutrition():
    print("\n测试营养分析API...")
    try:
        resp = requests.post('http://localhost:8002/api/v1/nutrition/analyze', json={
            'user_profile': {'username': '张先生', 'gender': '男', 'age': 35, 'height': 175, 'weight': 70, 'activity_level': '中等'},
            'daily_nutrition': {'calories': 2200, 'protein': 75, 'fat': 70, 'carbohydrate': 280, 'fiber': 20, 'sodium': 4500}
        })
        print(f'状态码: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'营养评分: {result.get("nutrition_score")}')
            print(f'摘要: {result.get("summary", "")[:200]}')
        else:
            print(f'响应内容: {resp.text[:200]}')
    except Exception as e:
        print(f'测试失败: {e}')

def test_retrieve():
    print("\n测试向量检索API...")
    try:
        resp = requests.post('http://localhost:8002/api/v1/retrieve', json={'query': '糖尿病饮食', 'top_k': 3})
        print(f'状态码: {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'结果数: {result.get("total")}')
            for i, item in enumerate(result.get('results', [])):
                print(f'  {i+1}. 相似度: {item.get("similarity", 0):.4f}, 内容: {item.get("content", "")[:100]}')
        else:
            print(f'响应内容: {resp.text[:200]}')
    except Exception as e:
        print(f'测试失败: {e}')

if __name__ == '__main__':
    test_chat()
    test_nutrition()
    test_retrieve()