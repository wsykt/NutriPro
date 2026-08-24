# ============================================================
#  Codebase Memory (CBM) 索引更新脚本
#  使用方式：
#    .\update_cbm_index.ps1          # 重新索引（full 模式）
#    .\update_cbm_index.ps1 -Fast    # 快速索引（跳过语义相似边）
#    .\update_cbm_index.ps1 -CheckOnly  # 仅检测变更（需项目根是 git 仓库）
#    .\update_cbm_index.ps1 -InstallTask   # 注册每日自动更新计划任务
#    .\update_cbm_index.ps1 -RemoveTask    # 移除自动更新计划任务
#  说明：
#    - 代码唯一住在 WSL（/root/health），Windows 通过符号链接 health_wsl 访问同一份代码。
#      索引路径必须用 health_wsl（符号链接），CBM 会跟随它并归入项目
#      wsl-Ubuntu-22.04-root-health（即 WSL /root/health 的图谱，唯一权威图谱）。
#    - git 仓库位于 health_wsl 根（.git 已复制到 WSL），detect_changes 增量检测可用。
# ============================================================
param(
    [switch]$CheckOnly,
    [switch]$Fast,
    [switch]$InstallTask,
    [switch]$RemoveTask
)

$ErrorActionPreference = 'Continue'

$CBM  = 'C:\Users\13425\AppData\Local\Programs\codebase-memory-mcp\codebase-memory-mcp.exe'
$Repo = 'C:\Users\13425\Desktop\个人健康助手\health_wsl'
$Proj = 'wsl-Ubuntu-22.04-root-health'
$TaskName = 'CBM-HealthAutoIndex'

# 注册每日自动更新计划任务（每天 03:00 执行，静默模式）
if ($InstallTask) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
        -Argument "-ExecutionPolicy Bypass -File `"$PSScriptRoot\update_cbm_index.ps1`" -Fast"
    $trigger = New-ScheduledTaskTrigger -Daily -At 03:00
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "Scheduled task '$TaskName' installed (daily 03:00)." -ForegroundColor Green
    exit 0
}

# 移除计划任务
if ($RemoveTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Scheduled task '$TaskName' removed." -ForegroundColor Green
    exit 0
}

# CBM daemon 在中文路径下会拒绝 session，必须从 ASCII 目录执行
Set-Location 'C:\Users\13425'

Write-Host '== Check daemon (127.0.0.1:9749) ==' -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:9749/' -UseBasicParsing -TimeoutSec 3
    Write-Host "daemon OK (HTTP $($r.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host 'daemon not running, starting...' -ForegroundColor Yellow
    Start-Process -FilePath $CBM -ArgumentList 'daemon','start','--port=9749' -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

if ($CheckOnly) {
    if (Test-Path (Join-Path $Repo '.git')) {
        Write-Host '== Detect changes ==' -ForegroundColor Cyan
        & $CBM cli detect_changes --project $Proj --scope files --format json 2>&1 | Select-String -NotMatch 'level=(warn|info)'
    } else {
        Write-Host 'No git repo at project root, detect_changes unavailable.' -ForegroundColor Yellow
        Write-Host 'Falling back to full re-index.' -ForegroundColor Yellow
        & $CBM cli index_repository --repo-path $Repo --mode 'fast' --json 2>&1 | Select-String -NotMatch 'level=(warn|info)'
    }
    exit $LASTEXITCODE
}

$mode = if ($Fast) { 'fast' } else { 'full' }
Write-Host "== Re-index ($mode mode) ==" -ForegroundColor Cyan
& $CBM cli index_repository --repo-path $Repo --mode $mode --json 2>&1 | Select-String -NotMatch 'level=(warn|info)'
Write-Host "Index done (exit=$LASTEXITCODE)" -ForegroundColor Green

Write-Host ''
Write-Host 'UI: http://127.0.0.1:9749' -ForegroundColor Cyan
