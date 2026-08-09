import os, json
from datetime import datetime

crowds = ['普通人','孕妇','健身人群','老年人','青少年','糖尿病患者','通用']
now = datetime.now()
print(f'=== 检查时间: {now.strftime("%H:%M:%S")} ===')
total_done = 0
all_done = True

for c in crowds:
    ckp = None
    out = None
    for f in os.listdir('.'):
        if f.startswith('ckp_') and f.endswith('.json') and c in f:
            ckp = f
        if f.startswith('kb_out_') and f.endswith('.json') and c in f:
            out = f
    done = 0
    finished = False
    if ckp:
        try:
            with open(ckp,'r',encoding='utf-8') as fh:
                j = json.load(fh)
            done = len(j.get('completed_task_ids',[]))
        except Exception as e:
            pass
    finished = done >= 200
    if not finished:
        all_done = False
    out_ex = os.path.exists(out) if out else False
    mark = 'DONE' if finished else 'RUN'
    print(f'[{c:6s}] {done:4d}/200 {mark}  JSON:{out_ex and "Y" or "N"}')
    total_done += done

pct = round(total_done/1400*100,1)
ad = 'YES' if all_done else 'NO'
print(f'\nTotal: {total_done}/1400 ({pct}%)  AllDone:{ad}')

# ChromaDB stats
print('\n=== 向量知识库统计 ===')
try:
    import sys
    sys.path.insert(0, '.')
    from vector.retriever import ChromaRetriever
    r = ChromaRetriever()
    stats = r.stats()
    print('总数:', stats.get('total', 0))
    for k,v in stats.get('by_category', {}).items():
        print(f'  {k}: {v}')
except Exception as e:
    print('查询失败:', e)
