# Codebase Memory (CBM) 使用指南

> Codebase Memory MCP (DeusData/codebase-memory-mcp) —— 代码库语义记忆/图谱索引工具。
> 本文档记录本机（Windows）的实际安装、索引、自动更新与复用方法。

---

## 1. 基本情况

| 项 | 值 |
|---|---|
| 版本 | codebase-memory-mcp 0.10.8 |
| 二进制 | `C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe` |
| 数据目录 | `C:\Users\13425\.cache\codebase-memory-mcp\` |
| UI 地址 | http://127.0.0.1:9749 （图谱可视化） |
| 项目名（本项目） | `wsl-Ubuntu-22.04-root-health` |
| 项目路径 | `C:\Users\13425\Desktop\个人健康助手\health_wsl`（符号链接 → `\\wsl$\Ubuntu-22.04\root\health`） |

> 💡 **图谱统一说明（重要）**
> 代码唯一住在 WSL（`/root/health`）。Windows 侧通过符号链接 `health_wsl` 指向它，
> CBM 索引时跟随符号链接并归入项目 `wsl-Ubuntu-22.04-root-health`（root_path 为
> `//wsl$/Ubuntu-22.04/root/health`）——这就是**唯一权威图谱**。
> 旧的 Windows 副本 `health/` 不再索引（`.cbmignore` 排除），旧项目
> `C-Users-13425-Desktop-e4b8aae4babae581a5e5bab7e58aa9e6898b` 已删除，避免 MCP 自动匹配歧义。

> ⚠️ **重要坑：中文路径**
> CBM daemon 在中文路径下会拒绝 session（`daemon session context was rejected`）。
> **所有 `cli` 命令必须先 `Set-Location 'C:\Users\13425'`（ASCII 路径）再执行**。
> 项目本身是中文路径没关系，只要执行 cli 时的工作目录是 ASCII 即可。

---

## 2. 安装（首次）

```powershell
# 已通过官方安装器安装到 Program Files，一般无需重装。
# 如需重装：运行 install.ps1
& "C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\install.ps1"
```

---

## 3. 启动 / 停止 daemon

```powershell
# 启动（后台常驻，端口 9749）
& "C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe" daemon start --port=9749

# 停止
& "...\codebase-memory-mcp.exe" daemon stop

# 验证
Invoke-WebRequest -Uri http://127.0.0.1:9749/ -UseBasicParsing -TimeoutSec 3   # 期望 200
```

---

## 4. 索引项目

```powershell
Set-Location 'C:\Users\13425'   # 必须，ASCII 路径

$CBM  = 'C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe'
$Repo = 'C:\Users\13425\Desktop\个人健康助手\health_wsl'   # 符号链接 → WSL /root/health

# full 模式：全部文件 + 相似/语义边（最全，较慢）
& $CBM cli index_repository --repo-path $Repo --mode full --json

# fast 模式：过滤文件，无相似/语义边（快）
& $CBM cli index_repository --repo-path $Repo --mode fast --json
```

索引结果中 `nodes`/`edges` 即图谱规模；`not_indexed_files` 是按 gitignore/.cbmignore 设计排除项，非错误。

---

## 5. 自动更新 ✅

`update_cbm_index.ps1` 已封装索引与自动更新：

```powershell
# 手动重新索引（full）
.\update_cbm_index.ps1

# 快速索引
.\update_cbm_index.ps1 -Fast

# 检测变更（git 仓库已位于 health_wsl 根，增量检测可用）
.\update_cbm_index.ps1 -CheckOnly

# 注册每日自动更新（每天 03:00，fast 模式，后台静默执行）
.\update_cbm_index.ps1 -InstallTask

# 移除自动更新
.\update_cbm_index.ps1 -RemoveTask
```

脚本自动处理：
- 检查/拉起 daemon（未运行则启动）
- 切换到 ASCII 工作目录再调用 cli
- 注册计划任务 `CBM-HealthAutoIndex`

> 说明：git 仓库位于 `health_wsl/` 根（`.git` 已复制到 WSL），`detect_changes` 增量检测可用；
> 若检测不可用会自动回退为 fast 全量重索引。

---

## 6. 常用查询（复用）

```powershell
Set-Location 'C:\Users\13425'
$CBM = 'C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe'
$P   = 'wsl-Ubuntu-22.04-root-health'

# 项目列表
& $CBM cli list_projects --json

# 索引状态（节点/边/未索引文件）
& $CBM cli index_status --project $P --json

# 图谱搜索（语义）
& $CBM cli search_graph --project $P --query "用户认证" --json

# 代码片段
& $CBM cli get_code_snippet --project $P --path "src/..." --json

# 架构总览
& $CBM cli get_architecture --project $P --aspects "all" --json

# 调用链追踪
& $CBM cli trace_path --project $P --from "X" --to "Y" --json

# 代码检索（文本）
& $CBM cli search_code --project $P --query "high_performance" --json
```

完整工具列表（13 个）：
`index_repository` `search_graph` `query_graph` `trace_path` `get_code_snippet`
`get_graph_schema` `get_architecture` `search_code` `list_projects` `delete_project`
`index_status` `check_index_coverage` `detect_changes` `manage_adr` `ingest_traces`

---

## 7. UI 可视化

浏览器打开 http://127.0.0.1:9749 ，可查看：
- 代码图谱（节点=符号，边=调用/引用/相似）
- 按文件/目录浏览

---

## 8. 已知问题与注意事项

1. **中文路径 session 拒绝**：cli 必须从 ASCII 工作目录运行（见第 1 节）。
2. `daemon start --ui=true` 选项不支持，端口直接 `--port=9749`。
3. 部分解析（parse_partial）文件：`init-schema.sql`、`nginx.conf`、`HealthReport.vue(271行)` 有局部缺失，用 grep 兜底。
4. 设计排除项（node_modules、*.class、PDF、日志、数据库文件）不会被索引，属正常。
5. 删除项目索引：`& $CBM cli delete_project --project $P`。
