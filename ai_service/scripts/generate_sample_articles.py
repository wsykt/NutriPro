import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llm.base_llm import llm_client


article_topics = [
    {
        "topic": "老年人饮食营养要点",
        "category": "老年人膳食",
        "audience": "老年人",
        "system_prompt": "你是一位专业营养师，请写一篇关于老年人饮食营养的科普文章，重点讲蛋白质摄入、膳食纤维、钙吸收、水分补充等方面。"
    },
    {
        "topic": "孕妇孕期营养指南",
        "category": "孕期营养",
        "audience": "孕妇",
        "system_prompt": "你是一位专业营养师，请写一篇关于孕妇孕期营养的科普文章，包括叶酸、铁、DHA的重要性，以及孕期饮食禁忌。"
    },
    {
        "topic": "青少年健康成长饮食建议",
        "category": "儿童青少年健康",
        "audience": "青少年",
        "system_prompt": "你是一位专业营养师，请写一篇关于青少年健康成长饮食的科普文章，重点讲均衡营养、早餐重要性、避免垃圾食品等。"
    },
    {
        "topic": "糖尿病患者饮食管理",
        "category": "糖尿病饮食",
        "audience": "糖尿病",
        "system_prompt": "你是一位专业营养师，请写一篇关于糖尿病患者饮食管理的科普文章，包括控制碳水、选择低GI食物、定时定量进餐等。"
    },
    {
        "topic": "健身增肌饮食攻略",
        "category": "运动健康",
        "audience": "健身",
        "system_prompt": "你是一位专业营养师，请写一篇关于健身增肌饮食的科普文章，重点讲蛋白质摄入时机、碳水化合物选择、训练前后营养补充。"
    },
    {
        "topic": "普通人日常健康饮食原则",
        "category": "膳食指南",
        "audience": "普通人群",
        "system_prompt": "你是一位专业营养师，请写一篇关于普通人日常健康饮食原则的科普文章，包括膳食宝塔、三餐搭配、烹饪方式选择等。"
    },
    {
        "topic": "减脂期间如何科学饮食",
        "category": "运动健康",
        "audience": "健身",
        "system_prompt": "你是一位专业营养师，请写一篇关于减脂期间科学饮食的科普文章，包括热量缺口、蛋白质保存肌肉、膳食纤维增加饱腹感等。"
    },
    {
        "topic": "老年人常见营养问题及解决方案",
        "category": "老年人膳食",
        "audience": "老年人",
        "system_prompt": "你是一位专业营养师，请写一篇关于老年人常见营养问题及解决方案的科普文章，包括食欲减退、咀嚼困难、便秘等问题的应对方法。"
    }
]


def generate_article(topic, system_prompt):
    prompt = f"{system_prompt}\n\n请输出一篇完整的科普文章，格式如下：\n标题：{topic}\n\n摘要：（50-100字）\n\n正文：（800-1000字，分3-4个小标题）\n\n关键词：（3-5个）"
    
    try:
        response = llm_client.chat(
            messages=[
                {"role": "system", "content": "你是一位专业的健康科普作家，擅长用通俗易懂的语言解释复杂的营养学知识。"},
                {"role": "user", "content": prompt}
            ],
            model="deepseek-chat",
            temperature=0.7
        )
        
        content = response.get('content', '')
        return parse_article(content, topic)
    except Exception as e:
        print(f"生成文章失败: {e}")
        return None


def parse_article(content, topic):
    lines = content.strip().split('\n')
    title = topic
    summary = ""
    body = []
    tags = []
    
    in_summary = False
    in_body = False
    in_tags = False
    
    for line in lines:
        if line.startswith('标题：'):
            title = line.replace('标题：', '').strip()
        elif line.startswith('摘要：'):
            summary = line.replace('摘要：', '').strip()
            in_summary = True
        elif line.startswith('正文：'):
            in_summary = False
            in_body = True
            in_tags = False
        elif line.startswith('关键词：'):
            tags_str = line.replace('关键词：', '').strip()
            tags = [t.strip() for t in tags_str.split('、')]
            in_body = False
            in_tags = True
        elif in_summary:
            summary += line.strip() + ' '
        elif in_body:
            body.append(line)
    
    if not summary:
        summary = content[:100] + '...'
    
    if not tags:
        tags = ['健康', '营养']
    
    return {
        "title": title,
        "summary": summary.strip(),
        "content": '\n\n'.join(body),
        "tags": ','.join(tags)
    }


def main():
    print("开始生成示例科普文章...")
    
    articles_data = []
    
    for item in article_topics:
        print(f"\n生成文章: {item['topic']}")
        article = generate_article(item['topic'], item['system_prompt'])
        if article:
            articles_data.append({
                "title": article['title'],
                "topic": item['topic'],
                "category": item['category'],
                "audience": item['audience'],
                "summary": article['summary'],
                "content": article['content'],
                "tags": article['tags']
            })
            print(f"  ✓ 已生成")
    
    output_file = os.path.join(os.path.dirname(__file__), '..', 'sample_articles.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n已生成 {len(articles_data)} 篇文章，保存到 {output_file}")
    
    print("\n文章列表：")
    for i, article in enumerate(articles_data, 1):
        print(f"{i}. {article['title']} - {article['category']} - {article['audience']}")


if __name__ == "__main__":
    main()