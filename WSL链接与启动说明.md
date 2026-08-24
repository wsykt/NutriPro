# 健康助手 · Trae 与 WSL 链接及启动说明

> 适用于迁移到 WSL（Ubuntu-22.04）后的日常使用。项目源码在 Windows 侧编辑（git 管理），实际运行环境在 WSL 内。

---

## 一、整体架构

```
┌─────────────── Windows 侧 ───────────────┐
│  Trae（编辑源码，git 管理）                │
│  start_all.ps1（一键启动脚本）            │
│  dsh web UI  → http://localhost:3080      │
└──────────────┬────────────────────────────┘
               │ localhost 自动转发（IPv4）
┌──────────────▼──────── WSL (Ubuntu-22.04) ─┐
│  Ollama      :11434   本地大模型 qwen2.5-7b │
│  AI 服务     :8002    uvicorn (FastAPI)     │
│  后端        :8082    Spring Boot           │
│  前端        :5173    Vite (Vue3)           │
└─────────────────────────────────────────────┘
```

浏览器直接访问 `http://localhost:5173` 即可使用整个应用。

---

## 二、Trae 与 WSL 的链接方式

### 方式 0：Windows 符号链接 health_wsl（推荐，代码唯一住在 WSL）

代码**唯一住在 WSL**（`/root/health`）。项目根目录下已建符号链接：

```
health_wsl  →  \\wsl$\Ubuntu-22.04\root\health
```

Trae 直接打开 `C:\Users\13425\Desktop\个人健康助手\health_wsl` 即可：
- 看到、编辑的就是 WSL 里的同一份代码（**无需再同步**）；
- 代码性能在 WSL 侧（原生 Linux 文件系统）；
- CBM 知识图谱也跟随该链接归入唯一项目 `wsl-Ubuntu-22.04-root-health`，Windows/WSL 图谱统一。

> 注意：`health_wsl` 是指向 UNC 的**符号链接**（junction 不支持 UNC），需要管理员权限创建；
> 若误删，用管理员 PowerShell 重建：
> `New-Item -ItemType SymbolicLink -Path "C:\Users\13425\Desktop\个人健康助手\health_wsl" -Target "\\wsl$\Ubuntu-22.04\root\health"`

### 方式 1：Trae 打开 WSL 内文件（已实测可用）

Trae 可直接打开 WSL 文件系统的网络路径，两种写法等价：

```
\\wsl$\Ubuntu-22.04\root\health
\\wsl.localhost\Ubuntu-22.04\root\health
```

操作：Trae 菜单 **文件 → 打开文件夹**，粘贴上面的路径。
WSL 内的实际代码在 `/root/health`（Windows 资源管理器里就是上面的路径）。

### 方式 2：Trae 内置终端进入 WSL

Trae 的终端里直接输入：

```powershell
wsl -d Ubuntu-22.04
```

即进入 WSL 的 bash shell，可执行 Linux 命令（`cd /root/health`、`tail -f /root/logs/backend.log` 等）。

### 方式 3：Trae 远程窗口连接 WSL（Trae 已内置支持）

Trae 已自动在 WSL 内部署了远程服务端（`/root/.trae-cn-server`，监听 34289 端口），说明 Trae 原生支持 WSL 远程环境。在 Trae 的连接/远程入口中选择 WSL（Ubuntu-22.04）即可像编辑本机一样编辑 `/root/health`，且终端、运行都直接发生在 WSL 里。

### 反向互通：WSL 里也能看到 Windows 目录

WSL 侧已有软链 `/root/hj-project → /mnt/c/Users/13425/Desktop/个人健康助手`，
WSL 内可访问 Windows 侧的脚本与文档：

```bash
ls /root/hj-project   # 即 Windows 项目根目录
```

### 日常推荐工作流

| 场景 | 做法 |
|------|------|
| 改代码 | 打开 `health_wsl`（方式 0）或 WSL 路径（方式 1/3），直接编辑 WSL 内代码，**无需同步** |
| 编辑 Windows 侧脚本/文档 | 直接编辑项目根目录，WSL 通过 `/root/hj-project` 可见 |
| 跑服务 | 一键脚本 `start_all.ps1` |
| 看日志 | `wsl -d Ubuntu-22.04` 后 `tail -f /root/logs/*.log` |

---

## 三、一键启动脚本 start_all.ps1

在项目根目录 `c:\Users\13425\Desktop\个人健康助手` 打开 PowerShell：

```powershell
.\start_all.ps1               # 启动全部：WSL 服务 + dsh
.\start_all.ps1 -NoDsh        # 只启动 WSL 服务，不启动 dsh
.\start_all.ps1 -Open         # 启动后自动打开浏览器前端
.\start_all.ps1 -Status       # 只查看各服务状态（不启动）
.\start_all.ps1 -StopAll      # 停止全部服务
```

脚本特点：
- 已运行的服务自动跳过（幂等，可反复执行）
- 内置端口健康检查，最终打印 5 个服务的运行状态
- dsh 冷启动轮询等待最长 40 秒

---

## 四、dsh 的启动与使用

### 方式 A：脚本一键启动（推荐）

```powershell
.\start_all.ps1          # 或 .\start_all.ps1 -NoDsh 跳过
```

脚本会自动：
1. 检测 3080 端口，已运行则跳过
2. 用 `dsh.cmd --profile web` 在 `C:\Users\13425` 目录启动（CBM MCP 要求 ASCII 工作目录）
3. 轮询等待就绪后提示访问地址

### 方式 B：手动启动

```powershell
Set-Location C:\Users\13425
dsh --profile web
```

### 方式 C：旧脚本

项目根目录已有 `start_dsh.ps1`（等价于手动方式）。

启动后访问：**http://localhost:3080**

停止 dsh：

```powershell
.\start_all.ps1 -StopAll
```

---

## 五、服务地址清单

| 服务 | 端口 | 地址 | 说明 |
|------|------|------|------|
| 前端页面 | 5173 | http://localhost:5173 | 日常使用入口 |
| 后端 API | 8082 | http://localhost:8082 | Spring Boot |
| AI 服务 | 8002 | http://localhost:8002/docs | Swagger 文档 |
| dsh | 3080 | http://localhost:3080 | DeepSeek Harness |
| Ollama | 11434 | http://localhost:11434 | 本地大模型 API |

---

## 六、WSL 内常用命令（终端输入 `wsl -d Ubuntu-22.04` 进入）

```bash
# 服务进程
ps aux | grep -E 'uvicorn|health-backend|vite'

# 日志（实时）
tail -f /root/logs/ai_service.log      # AI 服务
tail -f /root/logs/backend.log         # 后端
tail -f /root/logs/frontend.log        # 前端

# Ollama
ollama list                             # 查看模型
systemctl status ollama                 # 服务状态

# 手动重启单个服务（一般用 start_all.ps1 即可）
bash /mnt/c/Users/13425/Desktop/个人健康助手/wsl_restart_backend.sh   # 重启后端
```

---

## 七、常见问题排查

| 现象 | 原因与解决 |
|------|-----------|
| Windows 访问 localhost:8082 不通 | 后端必须用 `-Djava.net.preferIPv4Stack=true` 启动（已写入脚本），否则绑定 IPv6 无法转发 |
| 前端 5173 起了一会儿就没了 | vite 必须用 `setsid` 启动脱离会话（已写入脚本），否则随 wsl 命令退出被回收 |
| WSL 空闲后服务全部消失 | 已配置 `C:\Users\13425\.wslconfig` 的 `vmIdleTimeout=-1`（永不因空闲关闭）。重新执行 `start_all.ps1` 即可全部拉起 |
| 修改了 Windows 侧源码不生效 | 源码唯一住在 WSL，请直接编辑 `health_wsl`（符号链接）下的代码；旧 Windows 副本 `health/` 已废弃不再同步 |
| 修改了后端代码 | 通过 `health_wsl` 编辑 → `wsl_build_backend.sh` 构建 → `wsl_restart_backend.sh` 重启 |
| dsh 启动失败 | 确认工作目录为 `C:\Users\13425`（ASCII 路径），查看 `logs\dsh.pid` 或手动执行 `dsh --profile web` 看报错 |

---

## 八、相关脚本清单（均在项目根目录）

| 脚本 | 用途 |
|------|------|
| `health_wsl/`（符号链接） | → `\\wsl$\Ubuntu-22.04\root\health`，代码唯一住处，Trae 直接打开它 |
| `start_all.ps1` | 一键启动/停止/查看全部服务 |
| `wsl_start_services.sh` | WSL 内启动 4 个服务（Ollama/AI/后端/前端） |
| `wsl_build_backend.sh` | 后端 Maven clean package 构建 |
| `wsl_sync_src.sh` | 旧版同步脚本（源码已统一到 WSL，一般不再需要） |
| `wsl_restart_backend.sh` | 单独重启后端 |
| `start_dsh.ps1` | 旧版 dsh 启动脚本 |
| `update_cbm_index.ps1` | CBM 知识图谱索引/每日自动更新（指向 `health_wsl`，项目 `wsl-Ubuntu-22.04-root-health`） |
| `CBM使用指南.md` | CBM 索引与查询完整文档 |
