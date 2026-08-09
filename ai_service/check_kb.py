import json

data = json.load(open(r'c:\Users\13425\Desktop\个人健康助手\health\ai_service\knowledge_base\full_knowledge_base.json', 'r', encoding='utf-8'))
print(f'总文档数: {len(data)}')

topics = {}
groups = {}
channels = {}
for d in data:
    t = d.get('topic', '未知')
    g = d.get('group', '未知')
    c = d.get('source_channel', '未知')
    topics[t] = topics.get(t, 0) + 1
    groups[g] = groups.get(g, 0) + 1
    channels[c] = channels.get(c, 0) + 1

print('\n=== 按主题分布 ===')
for t, c in sorted(topics.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}篇')

print('\n=== 按人群分布 ===')
for g, c in sorted(groups.items(), key=lambda x: -x[1]):
    print(f'  {g}: {c}篇')

print('\n=== 按来源分布 ===')
for ch, c in sorted(channels.items(), key=lambda x: -x[1]):
    print(f'  {ch}: {c}篇')
