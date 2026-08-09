# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    个人健康助手 — 离线一键演示启动脚本

.DESCRIPTION
    专为比赛/演示场景设计：全程不依赖云端（DeepSeek），强制 LLM_MODE=local
    走本地 Ollama（qwen2.5-7b 4-bit 量化）。一键拉起：
      Ollama(11434) → AI服务(8002) → 后端(8082) → 前端(5173)

    与 start_all.ps1 的区别：start_all 默认 cloud（云端+本地双链路），
    本脚本固定 local（纯离线演示，断网可用）。

    若 Ollama 模型未就绪，自动提示拉取命令并降级提示（不阻断启动，
    演示仍可查看知识库检索等非 LLM 功能；LLM 功能由本地兜底引擎响应）。

.USAGE
    powershell -ExecutionPolicy Bypass -File .\start_demo_offline.ps1
    powershell -ExecutionPolicy Bypass -File .\start_demo_offline.ps1 -SkipOllama   # 跳过 Ollama 启动（已手动运行）
    powershell -ExecutionPolicy Bypass -File .\start_demo_offline.ps1 -StopAll     # 停止全部服务

.NOTES
    端口：Ollama 11434 | AI服务 8002 | 后端 8082 | 前端 5173
    本脚本必须保存为带 BOM 的 UTF-8，否则 PowerShell 5.1 解析中文报错
#>
[CmdletBinding()]
param(
    [switch]$SkipOllama,
    [switch]$StopAll
)

# ======================== 路径常量 ========================
$PROJECT_ROOT = "c:\Users\13425\Desktop\个人健康助手\health"
$JDK8 = "C:\Program Files\Java\jdk1.8.0_341"
$JAR = "$PROJECT_ROOT\backend-health\target\health-backend-1.0.0.jar"
$MVN = "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3\bin\mvn.cmd"
$AI_DIR = "$PROJECT_ROOT\ai_service"
$FE_DIR = "$PROJECT_ROOT\frontend-health"
$OLLAMA_MODEL_NAME = "qwen2.5:7b-instruct-q4_K_M"

# ======================== 工具函数 ========================
function Wait-Port([int]$Port, [int]$Seconds) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Test-PortListen([int]$Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Start-Ollama {
    Write-Host "`n[Ollama] 启动本地大模型服务（离线模式必需）..." -ForegroundColor Yellow
    if ($env:OLLAMA_MODELS -eq "") { $env:OLLAMA_MODELS = "D:\ollama\models" }
    if (Test-PortListen 11434) {
        Write-Host "  Ollama 已在运行（端口11434已监听）" -ForegroundColor Green
    } else {
        $p = Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle NewWindow -PassThru
        Start-Sleep -Seconds 3
        if (Wait-Port 11434 10) { Write-Host "  OK Ollama 已启动" -ForegroundColor Green }
        else { Write-Host "  WARN Ollama 启动失败，请手动执行: ollama serve" -ForegroundColor Red }
    }
    # 校验目标模型是否已拉取
    $modelOk = $false
    try {
        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
        if ($names -contains $OLLAMA_MODEL_NAME -or $names -contains "qwen2.5-7b-local" -or $names -contains "qwen2.5:7b") {
            Write-Host "  OK 本地模型已就绪: $($names -join ', ')" -ForegroundColor Green
            $modelOk = $true
        } elseif ($names.Count -gt 0) {
            Write-Host "  可用模型: $($names -join ', ')" -ForegroundColor Gray
            Write-Host "  WARN 未找到 $OLLAMA_MODEL_NAME，LLM 功能将走本地兜底规则" -ForegroundColor Yellow
            Write-Host "        拉取命令: ollama pull $OLLAMA_MODEL_NAME" -ForegroundColor Gray
        } else {
            Write-Host "  WARN Ollama 无模型，请先执行: ollama pull $OLLAMA_MODEL_NAME" -ForegroundColor Red
        }
    } catch {
        Write-Host "  WARN 无法连接 Ollama（演示 LLM 功能将受限，知识库检索仍可用）" -ForegroundColor Yellow
    }
    $script:OllamaReady = $modelOk
}

function Start-AIService {
    Write-Host "`n[AIService] 启动 AI 服务（LLM_MODE=local 强制离线，端口8002）..." -ForegroundColor Yellow
    if (Test-PortListen 8002) {
        Write-Host "  AI服务已在运行" -ForegroundColor Green; return
    }
    $PyPath = "C:\Users\13425\AppData\Local\Programs\Python\Python312\python.exe"
    if (-not (Test-Path $PyPath)) { $PyPath = "python" }
    Write-Host "  使用 Python: $PyPath" -ForegroundColor Gray
    $p = Start-Process -FilePath $PyPath -ArgumentList "main.py" `
        -WorkingDirectory $AI_DIR -WindowStyle NewWindow -PassThru
    Start-Sleep -Seconds 8
    if (Wait-Port 8002 45) { Write-Host "  OK AI服务已就绪（PID: $($p.Id)） http://localhost:8002" -ForegroundColor Green }
    else { Write-Host "  WARN AI服务加载中（向量模型较慢），请稍后访问" -ForegroundColor Red }
}

function Start-Backend {
    Write-Host "`n[Backend] 启动后端（JDK 1.8，端口8082）..." -ForegroundColor Yellow
    if (Test-PortListen 8082) { Write-Host "  后端已在运行" -ForegroundColor Green; return }
    if (-not (Test-Path $JAR)) {
        Write-Host "  jar 不存在，先编译..." -ForegroundColor Gray
        $env:JAVA_HOME = $JDK8
        & $MVN -f "$PROJECT_ROOT\backend-health\pom.xml" clean package "-Dmaven.test.skip=true" -q
        if ($LASTEXITCODE -ne 0) { Write-Host "  ERROR 编译失败" -ForegroundColor Red; exit 1 }
    }
    $p = Start-Process -FilePath "$JDK8\bin\java.exe" -ArgumentList "-jar", "`"$JAR`"" `
        -WorkingDirectory "$PROJECT_ROOT\backend-health" -WindowStyle NewWindow -PassThru
    Start-Sleep -Seconds 15
    if (Wait-Port 8082 20) { Write-Host "  OK 后端已就绪 http://localhost:8082" -ForegroundColor Green }
    else { Write-Host "  WARN 后端尚未就绪" -ForegroundColor Red }
}

function Start-Frontend {
    Write-Host "`n[Frontend] 启动前端（Vue3+Vite，端口5173）..." -ForegroundColor Yellow
    if (Test-PortListen 5173) { Write-Host "  前端已在运行" -ForegroundColor Green; return }
    $p = Start-Process -FilePath "npm" -ArgumentList "run", "dev" `
        -WorkingDirectory $FE_DIR -WindowStyle NewWindow -PassThru
    Start-Sleep -Seconds 5
    if (Wait-Port 5173 20) { Write-Host "  OK 前端已就绪 http://localhost:5173" -ForegroundColor Green }
    else { Write-Host "  WARN 前端尚未就绪" -ForegroundColor Red }
}

function Stop-All {
    Write-Host "停止全部服务进程..." -ForegroundColor Yellow
    Get-CimInstance Win32_Process | Where-Object {
        ($_.CommandLine -match "health-backend-1.0.0.jar") -or
        ($_.CommandLine -match "vite") -or
        ($_.CommandLine -match "python.*main\.py") -or
        ($_.CommandLine -match "ollama serve")
    } | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "  已停止 PID $($_.ProcessId)" -ForegroundColor Gray
    }
    Write-Host "  OK 已全部停止" -ForegroundColor Green
}

# ======================== 离线自检 ========================
function Check-Offline {
    Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
    Write-Host "  离线演示自检" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan

    # 1. 网络隔离确认：LLM 链路只走本地
    Write-Host "  [LLM链路] LLM_MODE=local（强制本地 Ollama，不依赖云端）" -ForegroundColor Green
    if ($script:OllamaReady) {
        Write-Host "  [Ollama ] 本地模型已就绪 → LLM 功能可用" -ForegroundColor Green
    } else {
        Write-Host "  [Ollama ] 模型未就绪 → LLM 功能走本地兜底规则，知识库检索不受影响" -ForegroundColor Yellow
    }

    # 2. 五库知识库自检
    try {
        $stats = Invoke-RestMethod -Uri "http://localhost:8002/api/v1/knowledge/stats" -TimeoutSec 10
        $total = $stats.total_docs
        $cols = $stats.collections
        Write-Host "  [知识库 ] 共 $total 条（五库隔离）" -ForegroundColor Green
        if ($cols) { Write-Host "            分布: $($cols | ConvertTo-Json -Compress)" -ForegroundColor Gray }
    } catch {
        Write-Host "  [知识库 ] WARN 无法获取统计（AI服务可能仍加载中）" -ForegroundColor Yellow
    }

    # 3. 三服务健康
    $svc = @(
        @{ Name = "AI服务"; Port = 8002; Url = "http://localhost:8002/health" },
        @{ Name = "后端";   Port = 8082; Url = "http://localhost:8082/api/user/info" },
        @{ Name = "前端";   Port = 5173; Url = "http://localhost:5173/" }
    )
    foreach ($s in $svc) {
        if (Test-PortListen $s.Port) { Write-Host "    $($s.Name) : 端口 $($s.Port) 已监听 OK" -ForegroundColor Green }
        else { Write-Host "    $($s.Name) : 端口 $($s.Port) 未监听" -ForegroundColor Red }
    }
    Write-Host "`n  结论："
    if ($script:OllamaReady) { Write-Host "    离线演示环境就绪，可断网完整演示 AI 功能" -ForegroundColor Green }
    else { Write-Host "    知识库检索可用；如需 LLM 功能请先: ollama pull $OLLAMA_MODEL_NAME" -ForegroundColor Yellow }
}

# ======================== 主流程 ========================
if ($StopAll) { Stop-All; exit 0 }

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  个人健康助手 — 离线一键演示" -ForegroundColor Cyan
Write-Host "  模式：LLM_MODE=local（纯本地，断网可用）" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# 关键：强制本地模式，AI 服务进程继承此环境变量
$env:LLM_MODE = "local"
Write-Host "  已设置 LLM_MODE=local（AI 服务将不调用云端）" -ForegroundColor Gray

if (-not $SkipOllama) { Start-Ollama }
Start-AIService
Start-Backend
Start-Frontend
Check-Offline

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "  离线演示环境启动完成！" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "`n演示入口: http://localhost:5173" -ForegroundColor Cyan
Write-Host "`n按任意键退出此窗口（服务继续运行）..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
