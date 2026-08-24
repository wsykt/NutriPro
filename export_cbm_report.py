#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CBM 知识图谱导出脚本
从 CBM 的 SQLite 图谱数据库导出：
  1. cbm-graph.json       —— 图谱全量数据（节点 + 边）
  2. cbm-architecture.md  —— 架构报告（Markdown，人/AI 可读）
输出到项目根目录，并可复制到 Windows 桌面。
用法：
  python3 export_cbm_report.py [--desktop]
  --desktop  额外复制一份到 Windows 桌面（/mnt/c/Users/13425/Desktop）
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = '/mnt/c/Users/13425/.cache/codebase-memory-mcp/wsl-Ubuntu-22.04-root-health.db'
PROJECT_NAME = 'wsl-Ubuntu-22.04-root-health'
PROJECT_ROOT = '/root/health'
DESKTOP = '/mnt/c/Users/13425/Desktop'

# 节点类型的中文说明
LABEL_CN = {
    'Project': '项目', 'Package': '包', 'Folder': '目录', 'File': '文件',
    'Module': '模块', 'Class': '类', 'Interface': '接口', 'Enum': '枚举',
    'Type': '类型', 'Function': '函数', 'Method': '方法', 'Field': '字段',
    'Variable': '变量', 'Route': '路由', 'Section': '区块', 'Decorator': '装饰器',
    'EnvVar': '环境变量', 'Branch': '分支',
}

# 边类型的中文说明
EDGE_CN = {
    'CONTAINS_PACKAGE': '包含包', 'CONTAINS_FOLDER': '包含目录', 'CONTAINS_FILE': '包含文件',
    'DEFINES': '定义', 'DEFINES_METHOD': '定义方法', 'IMPORTS': '导入', 'CALLS': '调用',
    'HTTP_CALLS': 'HTTP调用', 'ASYNC_CALLS': '异步调用', 'IMPLEMENTS': '实现',
    'HANDLES': '处理路由', 'USAGE': '使用', 'CONFIGURES': '配置', 'WRITES': '写入',
    'MEMBER_OF': '成员属于', 'TESTS': '测试', 'USES_TYPE': '使用类型',
    'FILE_CHANGES_WITH': '随文件变更', 'INHERITS': '继承', 'OVERRIDE': '覆写',
    'RAISES': '抛出', 'SEMANTICALLY_RELATED': '语义相关', 'SIMILAR_TO': '相似',
    'CALL_REFERENCE': '调用引用', 'DEPENDS_ON': '依赖', 'DECORATES': '装饰',
    'HAS_BRANCH': '分支',
}


def connect():
    return sqlite3.connect(f'file:{DB_PATH}?mode=ro', uri=True)


def load_nodes(cur):
    cur.execute(
        'SELECT id, label, name, qualified_name, file_path, start_line, end_line '
        'FROM nodes WHERE project = ?', (PROJECT_NAME,)
    )
    nodes = []
    for row in cur.fetchall():
        nodes.append({
            'id': row[0], 'label': row[1], 'name': row[2],
            'qualified_name': row[3], 'file': row[4],
            'start_line': row[5], 'end_line': row[6],
        })
    return nodes


def load_edges(cur):
    cur.execute(
        'SELECT id, source_id, target_id, type FROM edges WHERE project = ?',
        (PROJECT_NAME,)
    )
    edges = []
    for row in cur.fetchall():
        edges.append({'id': row[0], 'from': row[1], 'to': row[2], 'type': row[3]})
    return edges


def write_graph_json(nodes, edges, path):
    graph = {
        'meta': {
            'project': PROJECT_NAME,
            'root_path': '//wsl$/Ubuntu-22.04/root/health',
            'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'node_count': len(nodes),
            'edge_count': len(edges),
            'description': 'Codebase Memory (CBM) 知识图谱全量数据导出：nodes=代码符号/文件，'
                           'edges=调用/引用/包含等关系。',
        },
        'node_labels': LABEL_CN,
        'edge_types': EDGE_CN,
        'nodes': nodes,
        'edges': edges,
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, separators=(',', ':'))
    return os.path.getsize(path)


def build_markdown(nodes, edges):
    L = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 按标签统计
    label_cnt = {}
    label_files = {}
    for n in nodes:
        label_cnt[n['label']] = label_cnt.get(n['label'], 0) + 1
        if n['file']:
            label_files.setdefault(n['label'], set()).add(n['file'])

    # 按边类型统计
    edge_cnt = {}
    for e in edges:
        edge_cnt[e['type']] = edge_cnt.get(e['type'], 0) + 1

    # 文件列表（File 节点按路径排序）
    files = sorted({n['file'] for n in nodes if n['label'] == 'File' and n['file']})

    # 按目录聚合统计各模块文件数
    module_files = {}
    for f in files:
        parts = f.split('/')
        top = '/'.join(parts[:2]) if len(parts) > 1 else parts[0]
        module_files[top] = module_files.get(top, 0) + 1

    # 热点文件（被引用最多的文件）
    file_refs = {}
    id2file = {n['id']: n['file'] for n in nodes if n['file']}
    for e in edges:
        f = id2file.get(e['to'])
        if f:
            file_refs[f] = file_refs.get(f, 0) + 1
    hot = sorted(file_refs.items(), key=lambda x: -x[1])[:15]

    # 关键调用链（Controller → Service）
    calls = []
    for e in edges:
        if e['type'] in ('CALLS', 'HTTP_CALLS'):
            calls.append(e)

    L.append(f'# 个人健康助手 知识图谱架构报告\n')
    L.append(f'> 由 CBM (Codebase Memory) 知识图谱自动导出 · 生成时间：{now}\n')
    L.append(f'> 数据源：CBM 图谱数据库 · 项目：`{PROJECT_NAME}`\n')
    L.append('')
    L.append('## 1. 总体概览\n')
    L.append(f'| 指标 | 数值 |')
    L.append(f'|---|---|')
    L.append(f'| 节点总数 | **{len(nodes)}** |')
    L.append(f'| 边（关系）总数 | **{len(edges)}** |')
    L.append(f'| 文件数 | **{len(files)}** |')
    L.append(f'| 模块目录数 | **{len(module_files)}** |')
    L.append('')

    L.append('## 2. 节点类型分布\n')
    L.append('| 类型 | 数量 | 涉及文件数 |')
    L.append('|---|---|---|')
    for label, cnt in sorted(label_cnt.items(), key=lambda x: -x[1]):
        cn = LABEL_CN.get(label, label)
        L.append(f'| {label}（{cn}） | {cnt} | {len(label_files.get(label, set()))} |')
    L.append('')

    L.append('## 3. 关系（边）类型分布\n')
    L.append('| 关系类型 | 数量 |')
    L.append('|---|---|')
    for typ, cnt in sorted(edge_cnt.items(), key=lambda x: -x[1]):
        cn = EDGE_CN.get(typ, typ)
        L.append(f'| {typ}（{cn}） | {cnt} |')
    L.append('')

    L.append('## 4. 模块结构\n')
    L.append('| 模块目录 | 文件数 |')
    L.append('|---|---|')
    for mod, cnt in sorted(module_files.items(), key=lambda x: -x[1]):
        L.append(f'| `{mod}` | {cnt} |')
    L.append('')

    L.append('## 5. 热点文件（被引用最多，核心模块）\n')
    L.append('| 文件 | 被引用次数 |')
    L.append('|---|---|')
    for f, cnt in hot:
        L.append(f'| `{f}` | {cnt} |')
    L.append('')

    L.append('## 6. 关键调用关系示例\n')
    L.append('以下为部分核心调用链（Controller/Service 层）：\n')
    L.append('```')
    # 找 Controller 调用 Service 的链
    node_by_id = {n['id']: n for n in nodes}
    shown = 0
    for e in calls:
        src = node_by_id.get(e['from'])
        dst = node_by_id.get(e['to'])
        if not src or not dst:
            continue
        if src['label'] in ('Method', 'Function') and dst['label'] in ('Method', 'Function'):
            sn = src['name']
            dn = dst['name']
            if sn == dn:
                continue
            L.append(f'{sn}  -->  {dn}   [{e["type"]}]')
            shown += 1
            if shown >= 30:
                break
    L.append('```\n')
    L.append('> 完整图谱数据见 `cbm-graph.json`（节点 + 全部边）。\n')
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--desktop', action='store_true', help='同时复制到 Windows 桌面')
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        print(f'ERROR: 找不到图谱数据库: {DB_PATH}', file=sys.stderr)
        sys.exit(1)

    conn = connect()
    cur = conn.cursor()
    nodes = load_nodes(cur)
    edges = load_edges(cur)
    conn.close()
    print(f'读取图谱: {len(nodes)} 节点, {len(edges)} 边')

    graph_path = os.path.join(PROJECT_ROOT, 'cbm-graph.json')
    size = write_graph_json(nodes, edges, graph_path)
    print(f'JSON 图谱: {graph_path} ({size/1024:.0f} KB)')

    md = build_markdown(nodes, edges)
    md_path = os.path.join(PROJECT_ROOT, 'cbm-architecture.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'架构报告: {md_path}')

    if args.desktop:
        if os.path.isdir(DESKTOP):
            for name in ('cbm-graph.json', 'cbm-architecture.md'):
                src = os.path.join(PROJECT_ROOT, name)
                dst = os.path.join(DESKTOP, name)
                shutil.copy2(src, dst)
                print(f'复制到桌面: {dst}')
        else:
            print(f'WARN: 桌面目录不存在，跳过: {DESKTOP}', file=sys.stderr)


if __name__ == '__main__':
    main()
