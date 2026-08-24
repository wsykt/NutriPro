# ============================================================
#  健康助手 · 一键启动脚本（WSL 服务 + dsh web UI）
#
#  用法（在项目根目录 PowerShell 中执行）：
#    .\start_all.ps1              启动全部（WSL 服务 + dsh）
#    .\start_all.ps1 -NoDsh       只启动 WSL 服务，跳过 dsh
#    .\start_all.ps1 -Open        启动后自动打开浏览器前端
#    .\start_all.ps1 -Status      只查看各服务运行状态
#    .\start_all.ps1 -StopAll     停止全部服务（WSL 内 + dsh）
# ============================================================
param(
    [switch]$NoDsh,
    [switch]$Open,
    [switch]$Status,
    [switch]$StopAll
)
$ErrorActionPreference = 'Continue'
$WSL_DISTRO = 'Ubuntu-22.04'
$SCRIPT_DIR = $PSScriptRoot
$LOG_DIR    = Join-Path $SCRIPT_DIR 'logs'

# ---------- 工具函数 ----------
function WslPath([string]$winPath) {
    # C:\xxx -> /mnt/c/xxx
    return '/mnt/c/' + $winPath.Substring(3).Replace('\', '/')
}

function Test-Port([int]$port) {
    try {
        # 强制 IPv4（127.0.0.1）：WSL 的 localhost 转发绑定在 IPv4，用 'localhost' 可能先解析 IPv6 导致误报
        $c = New-Object System.Net.Sockets.TcpClient
        $iar = $c.BeginConnect('127.0.0.1', $port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne(500)
        if ($ok) { $c.EndConnect($iar) }
        $c.Close()
        return $ok
    } catch { return $false }
}

# ---------- 服务清单 ----------
$services = @(
    @{ Name = 'Ollama';  Port = 11434; Desc = '本地大模型(qwen2.5-7b)' },
    @{ Name = 'AI 服务'; Port = 8002;  Desc = 'AI 推理 uvicorn' },
    @{ Name = '后端';    Port = 8082;  Desc = 'Spring Boot API' },
    @{ Name = '前端';    Port = 5173;  Desc = 'Vue3 前端' },
    @{ Name = 'dsh';     Port = 3080;  Desc = 'DeepSeek Harness web UI' }
)

function Show-Status {
    Write-Host "`n================ 服务状态 ================" -ForegroundColor Cyan
    foreach ($s in $services) {
        $on   = Test-Port $s.Port
        $mark = if ($on) { '运行中' } else { '未启动' }
        $color = if ($on) { 'Green' } else { 'Red' }
        Write-Host ("  {0,-6} [ {1} ]  {2,-5}  {3}" -f $s.Name, $mark, "port=$($s.Port)", $s.Desc) -ForegroundColor $color
    }
    Write-Host "============================================" -ForegroundColor Cyan
}

# ---------- WSL 服务 ----------
function Start-WslServices {
    $script = Join-Path $SCRIPT_DIR 'wsl_start_services.sh'
    if (-not (Test-Path $script)) {
        Write-Host "[错误] 找不到 $script" -ForegroundColor Red
        return
    }
    Write-Host "`n[1/2] 启动 WSL 内服务（Ollama / AI / 后端 / 前端）..." -ForegroundColor Yellow
    & wsl -d $WSL_DISTRO -- bash (WslPath $script)
}

function Stop-WslServices {
    Write-Host "停止 WSL 内服务..." -ForegroundColor Yellow
    wsl -d $WSL_DISTRO -- bash -c "pkill -f 'uvicorn main:app'; pkill -f 'health-backend-1.0.0.jar'; pkill -f vite; sleep 1; echo WSL_STOPPED"
}

# ---------- dsh ----------
function Start-Dsh {
    if (Test-Port 3080) {
        Write-Host "[dsh] 已在运行（port 3080），跳过" -ForegroundColor Green
        return
    }
    if (-not (Get-Command dsh -ErrorAction SilentlyContinue)) {
        Write-Host "[错误] 找不到 dsh 命令，请先 npm install -g" -ForegroundColor Red
        return
    }
    New-Item -ItemType Directory -Force -Path $LOG_DIR | Out-Null
    # dsh 在 npm 全局目录，可执行文件是 dsh.cmd（不带扩展名的 dsh 是 node 脚本，Start-Process 无法直接运行）
    $dshCmd = (Get-Command dsh.cmd -ErrorAction SilentlyContinue).Source
    if (-not $dshCmd) { $dshCmd = 'dsh' }
    Write-Host "[dsh] 启动中（工作目录 C:\Users\13425，可执行文件 $dshCmd）..." -ForegroundColor Yellow
    $p = Start-Process -FilePath $dshCmd -ArgumentList '--profile', 'web' `
        -WorkingDirectory 'C:\Users\13425' -PassThru
    $p.Id | Out-File (Join-Path $LOG_DIR 'dsh.pid') -Encoding ascii
    # dsh 冷启动需要 10-20 秒，轮询等待最多 40 秒
    $deadline = (Get-Date).AddSeconds(40)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if (Test-Port 3080) { $ready = $true; break }
    }
    if ($ready) {
        Write-Host "[dsh] 启动成功 -> http://localhost:3080" -ForegroundColor Green
    } else {
        Write-Host "[dsh] 启动失败，请查看 logs\dsh.pid 对应进程或重试" -ForegroundColor Red
    }
}

function Stop-Dsh {
    $conn = Get-NetTCPConnection -LocalPort 3080 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "[dsh] 已停止" -ForegroundColor Green
    } else {
        Write-Host "[dsh] 未在运行" -ForegroundColor DarkGray
    }
}

# ---------- 主流程 ----------
if ($Status) {
    Show-Status
    exit
}

if ($StopAll) {
    Stop-WslServices
    Stop-Dsh
    Write-Host "全部服务已停止。" -ForegroundColor Cyan
    exit
}

# 检查 WSL 发行版是否可用（直接调用验证，绕开 wsl 输出编码问题）
wsl -d $WSL_DISTRO -- echo WSL_OK 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] 未找到 WSL 发行版 $WSL_DISTRO，请先导入" -ForegroundColor Red
    exit 1
}
Write-Host "[WSL] $WSL_DISTRO 正常" -ForegroundColor Green

# 确保 WSL 在运行
wsl -d $WSL_DISTRO -- echo "WSL_ALIVE" | Out-Null

Start-WslServices

if (-not $NoDsh) { Start-Dsh }

Write-Host "`n================ 最终状态 ================" -ForegroundColor Cyan
# AI 服务(torch) 与后端(Spring Boot) 启动较慢，多等一会儿再检测
Start-Sleep -Seconds 15
Show-Status

Write-Host "`n访问地址："
Write-Host "  前端页面  http://localhost:5173"
Write-Host "  后端 API  http://localhost:8082"
Write-Host "  dsh web   http://localhost:3080"
Write-Host "  WSL 终端  wsl -d $WSL_DISTRO"
if ($Open) { Start-Process 'http://localhost:5173' }
Write-Host ""
