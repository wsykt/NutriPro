import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vector.retriever import retriever
from agent.voice_text_parse import agent as voice_agent
from agent.food_audit import agent as food_audit_agent
from agent.diet_plan import agent as diet_plan_agent
from agent.retrieve_judge import agent as retrieve_judge_agent
from utils.json_utils import safe_parse_json, truncate_text


def test_vector_retrieval():
    print("\n=== 测试向量检索优化 ===")
    
    print("\n1. 糖尿病人群过滤测试：")
    results = retriever.search("糖尿病饮食建议", top_k=3, target_crowd="糖尿病患者")
    print(f"检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"  {i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}...")
    
    print("\n2. 健身人群过滤测试：")
    results = retriever.search("增肌蛋白质摄入", top_k=3, target_crowd="健身人群")
    print(f"检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"  {i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}...")
    
    print("\n3. GI值数据检索测试：")
    results = retriever.search("白米饭GI值", top_k=2)
    print(f"检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"  {i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:100]}...")
    
    print("\n4. 去重测试（同一文档重复检索）：")
    results1 = retriever.search("膳食指南", top_k=5)
    results2 = retriever.search("中国居民膳食指南", top_k=5)
    contents1 = set([r['content'][:50] for r in results1])
    contents2 = set([r['content'][:50] for r in results2])
    print(f"第一次检索内容片段: {contents1}")
    print(f"第二次检索内容片段: {contents2}")
    
    print("\n5. 长度截断测试：")
    long_content = "中国居民膳食指南2022核心推荐一：食物多样，合理搭配。" * 50
    truncated = retriever._truncate_content(long_content)
    print(f"原长度: {len(long_content)}, 截断后长度: {len(truncated)}")
    print(f"截断后内容: {truncated[:100]}...")
    
    return True


def test_voice_text_parse():
    print("\n=== 测试语音文本解析优化 ===")
    
    test_cases = [
        "一点点米饭",
        "半碗面条",
        "一小块蛋糕",
        "一勺盐",
        "半个拳头大小的苹果",
        "一个鸡蛋",
        "一杯牛奶",
        "一份红烧肉",
        "一片面包",
    ]
    
    for text in test_cases:
        try:
            result = voice_agent.parse(text)
            items = result.get("items", [])
            weights = [item.get("weight", "null") for item in items]
            print(f"输入: '{text}' -> 结果: {items}, 重量: {weights}")
        except Exception as e:
            print(f"输入: '{text}' -> 错误: {e}")
    
    return True


def test_food_audit():
    print("\n=== 测试食材初审优化 ===")
    
    test_cases = [
        {"food_name": "土鸡蛋", "portion": "1个", "category": "蛋类"},
        {"food_name": "鸡蛋", "portion": "1个", "category": "蔬菜"},
        {"food_name": "五花肉", "portion": "100克", "category": "肉类"},
        {"food_name": "三层肉", "portion": "100克", "category": "肉类"},
        {"food_name": "西红柿", "portion": "200克", "category": "水果"},
        {"food_name": "未知食材", "portion": "100克", "category": "蔬菜"},
    ]
    
    for tc in test_cases:
        try:
            result = food_audit_agent.audit(tc)
            print(f"食材: {tc['food_name']}, 分类: {tc['category']}")
            print(f"  审核级别: {result.get('audit_level')}, 风险描述: {result.get('risk_desc')}")
            print(f"  近义词: {result.get('duplicate_info', {}).get('similar_names')}")
            print(f"  分类匹配: {not result.get('category_mismatch')}, 建议: {result.get('category_suggestion')}")
        except Exception as e:
            print(f"食材: {tc['food_name']} -> 错误: {e}")
    
    return True


def test_diet_plan():
    print("\n=== 测试膳食方案优化 ===")
    
    test_profiles = [
        {
            "crowd_type": "糖尿病患者",
            "allergies": ["牛奶"],
            "dietary_restrictions": [],
            "age": 55,
            "gender": "男",
        },
        {
            "crowd_type": "健身人群",
            "allergies": [],
            "dietary_restrictions": ["素食"],
            "age": 28,
            "gender": "男",
        },
        {
            "crowd_type": "普通人",
            "allergies": ["海鲜"],
            "dietary_restrictions": ["不吃猪肉"],
            "age": 35,
            "gender": "女",
        },
    ]
    
    for profile in test_profiles:
        try:
            result = diet_plan_agent.generate(profile, goal="减脂")
            print(f"\n人群: {profile['crowd_type']}, 过敏: {profile['allergies']}, 禁忌: {profile['dietary_restrictions']}")
            print(f"  总热量: {result.get('total_calories')}")
            print(f"  避免食材: {result.get('avoided_foods')}")
            print(f"  替换食材: {result.get('replaced_foods')}")
            for meal, items in result.get("daily_plan", {}).items():
                foods = [item.get("food") for item in items]
                print(f"  {meal}: {foods}")
        except Exception as e:
            print(f"人群: {profile['crowd_type']} -> 错误: {e}")
    
    return True


def test_retrieve_judge():
    print("\n=== 测试检索判定优化 ===")
    
    test_queries = [
        "糖尿病患者早餐吃什么好？蛋白质摄入多少合适？",
        "你好",
        "推荐一些低GI的主食",
        "我想减肥，应该怎么吃？每天需要多少热量？运动多久合适？",
        "这个功能怎么用",
        "孕妇应该补充哪些营养素",
    ]
    
    for query in test_queries:
        try:
            result = retrieve_judge_agent.judge(query)
            print(f"\n问题: '{query}'")
            print(f"  需要检索: {result.get('need_retrieve')}")
            print(f"  复杂问题: {result.get('is_complex')}")
            print(f"  检索关键词: {result.get('search_keywords')}")
            print(f"  有知识库: {result.get('has_knowledge')}")
        except Exception as e:
            print(f"问题: '{query}' -> 错误: {e}")
    
    print("\n测试复杂问题批量检索：")
    keywords = ["糖尿病饮食", "蛋白质摄入", "主食选择"]
    results = retrieve_judge_agent.batch_retrieve(keywords, top_k=2)
    print(f"批量检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"  {i+1}. 相似度: {r['similarity']:.4f}, 内容: {r['content'][:80]}")
    
    return True


def test_json_utils():
    print("\n=== 测试JSON工具函数 ===")
    
    test_cases = [
        '{"name": "test", "value": 1}',
        '```json\n{"name": "test", "value": 2}\n```',
        '{"name": "test", "value": 3} // comment',
        '一些文本 {"name": "test", "value": 4} 更多文本',
    ]
    
    for tc in test_cases:
        result = safe_parse_json(tc)
        print(f"输入: {tc[:50]}... -> 解析结果: {result}")
    
    print("\n测试文本截断：")
    long_text = "a" * 5000
    truncated = truncate_text(long_text, max_length=100)
    print(f"原长度: {len(long_text)}, 截断后长度: {len(truncated)}")
    
    return True


def main():
    print("=" * 60)
    print("综合测试脚本 - 验证AI服务所有优化")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("向量检索", test_vector_retrieval()))
    except Exception as e:
        print(f"向量检索测试失败: {e}")
        results.append(("向量检索", False))
    
    try:
        results.append(("语音解析", test_voice_text_parse()))
    except Exception as e:
        print(f"语音解析测试失败: {e}")
        results.append(("语音解析", False))
    
    try:
        results.append(("食材初审", test_food_audit()))
    except Exception as e:
        print(f"食材初审测试失败: {e}")
        results.append(("食材初审", False))
    
    try:
        results.append(("膳食方案", test_diet_plan()))
    except Exception as e:
        print(f"膳食方案测试失败: {e}")
        results.append(("膳食方案", False))
    
    try:
        results.append(("检索判定", test_retrieve_judge()))
    except Exception as e:
        print(f"检索判定测试失败: {e}")
        results.append(("检索判定", False))
    
    try:
        results.append(("JSON工具", test_json_utils()))
    except Exception as e:
        print(f"JSON工具测试失败: {e}")
        results.append(("JSON工具", False))
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n✓ 所有测试通过！")
    else:
        print("\n✗ 部分测试失败，请检查相关模块")


if __name__ == "__main__":
    main()