# ======================================================================
# Windows 启动脚本 —— 个人健康助手（Vite 前端 5173）
# 使用方式：在 PowerShell 里执行  .\health\start_windows.ps1
# 若执行策略受限，先运行一次： Set-ExecutionPolicy -Scope Process Bypass
# ======================================================================
$ErrorActionPreference = "Stop"

# ---------- 路径 ----------
$ProjectRoot = Split-Path -Parent $PSScriptRoot          # 项目根：个人健康助手
$FrontendDir = Join-Path $PSScriptRoot "frontend-health"  # health\frontend-health
$Port = 5173

function Write-Info($m)  { Write-Host "[INFO]  $m" -ForegroundColor Green }
function Write-Warn($m)  { Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function Write-Err($m)   { Write-Host "[ERROR] $m" -ForegroundColor Red }

# ---------- 检查 ----------
if (-not (Test-Path $FrontendDir)) {
    Write-Err "前端目录不存在：$FrontendDir"; exit 1
}
$PackageJson = Join-Path $FrontendDir "package.json"
if (-not (Test-Path $PackageJson)) {
    Write-Err "找不到 package.json：$PackageJson"; exit 1
}
$nodeModules = Join-Path $FrontendDir "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Warn "node_modules 不存在，先执行 npm install"
    Set-Location $FrontendDir
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Err "npm install 失败"; exit 1 }
}

# ---------- 端口占用检查 ----------
$conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    Write-Warn "端口 ${Port} 已被 PID=$($conn.OwningProcess) ($($proc.ProcessName)) 占用"
    $ans = Read-Host "是否杀掉该进程后继续？(y/N)"
    if ($ans -eq "y" -or $ans -eq "Y") {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction Stop
        Write-Info "已清理 PID=$($conn.OwningProcess)"
        Start-Sleep -Seconds 1
    } else {
        Write-Err "用户取消"; exit 1
    }
}

# ---------- 启动 Vite ----------
Set-Location $FrontendDir
Write-Info "进入目录：$FrontendDir"
Write-Info "启动 Vite dev server (端口 ${Port}) …"
Write-Info "按 Ctrl+C 可停止前端"
Write-Host ""
npm run dev -- --port $Port

if ($LASTEXITCODE -ne 0) {
    Write-Err "Vite 异常退出 (code=$LASTEXITCODE)"
    exit $LASTEXITCODE
}
