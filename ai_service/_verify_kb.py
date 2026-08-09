import sys, os
sys.path.insert(0, '.')
from collections import Counter, defaultdict
from vector.retriever import ChromaRetriever

r = ChromaRetriever()
total = r.count()
print(f'ChromaDB 总记录数: {total}')

# 加载全部数据分组
data = r.collection.get(include=['documents','metadatas'])
metas = data.get('metadatas',[]) or []
docs = data.get('documents',[]) or []

ai_tpls = [(d,m) for d,m in zip(docs,metas) if m and m.get('template_type')=='ai_template']
print(f'ai_template 数: {len(ai_tpls)}')

func_cnt = Counter(m.get('func_type') for _,m in ai_tpls)
crowd_cnt = Counter(m.get('target_crowd') for _,m in ai_tpls)
bmi_cnt = Counter(m.get('bmi_cn') for _,m in ai_tpls)
print('\n按功能分布:')
for k,v in func_cnt.most_common(): print(f'  {k}: {v}')
print('\n按人群分布:')
for k,v in crowd_cnt.most_common(): print(f'  {k}: {v}')
print('\n按BMI分布:')
for k,v in bmi_cnt.most_common(): print(f'  {k}: {v}')

# 交叉: 人群×功能 每格=10条×BMI5=50，每格应该50
cross = defaultdict(int)
for _,m in ai_tpls:
    cross[f"{m.get('target_crowd')}x{m.get('func_type')}"] += 1
print('\n[人群×功能] 每格应为50:')
abnormal = [(k,v) for k,v in cross.items() if v != 50]
if abnormal:
    print('异常格:', abnormal[:10])
else:
    print(f'  {len(cross)} 格均=50，OK')

# 抽样展示
print('\n[抽样3条]')
for i,(d,m) in enumerate(ai_tpls[:3]):
    print(f'  #{i}: {m.get("card_id")} | {m.get("target_crowd")}-{m.get("bmi_cn")}-{m.get("direction")} | {m.get("func_cn")}')
    print(f'    标题: {d.split(chr(10))[0][:80]}')
