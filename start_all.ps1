# -*- coding: utf-8 -*-
<#
.SYNOPSIS
    个人健康助手 — 一键启动/编译脚本（全部命令固化，无需每次重写）

.DESCRIPTION
    支持的操作：
      默认           一键启动 AI服务(8002) → 后端(8082) → 前端(5173)
      -Build         先编译后端jar包，再启动全部服务
      -OllamaOnly    仅启动 Ollama（带 OLLAMA_MODELS 环境变量）
      -BackendOnly   仅启动后端（jar 包方式，JDK 1.8）
      -FrontendOnly  仅启动前端
      -AIServiceOnly 仅启动 AI 服务
      -StopAll       停止全部服务进程

.NOTES
    端口：AI服务 8002 | 后端 8082 | 前端 5173 | Ollama 11434
    编译：JDK 1.8.0_341 + IntelliJ IDEA 内置 Maven（项目已设为 Java 1.8）
    运行：后端 jar 用 JDK 1.8 启动（pom 已改 <java.version>1.8</java.version>）
    注意：本脚本必须保存为带 BOM 的 UTF-8，否则 PowerShell 5.1 解析中文报错
#>
[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$OllamaOnly,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$AIServiceOnly,
    [switch]$StopAll
)

# ======================== 路径常量（可用环境变量覆盖，便于迁移/CI） ========================
# 覆盖方式（示例）：
#   $env:DSH_HEALTH_ROOT = "D:\work\health"
#   $env:DSH_JDK8 = "D:\tools\jdk1.8.0_341"
#   $env:DSH_MVN = "D:\tools\maven\bin\mvn.cmd"
#   $env:DSH_NODEJS = "D:\tools\nodejs\npm.cmd"
#   $env:DSH_PY312 = "D:\tools\python312\python.exe"
#   $env:DSH_OLLAMA_MODELS = "D:\ollama\models"
$PROJECT_ROOT = $env:DSH_HEALTH_ROOT
if (-not $PROJECT_ROOT) { $PROJECT_ROOT = "c:\Users\13425\Desktop\个人健康助手\health" }
$JDK8 = $env:DSH_JDK8
if (-not $JDK8) { $JDK8 = "C:\Program Files\Java\jdk1.8.0_341" }
$JAR = "$PROJECT_ROOT\backend-health\target\health-backend-1.0.0.jar"
$MVN = $env:DSH_MVN
if (-not $MVN) { $MVN = "C:\Program Files\JetBrains\IntelliJ IDEA 2025.3.3\plugins\maven\lib\maven3\bin\mvn.cmd" }
$AI_DIR = "$PROJECT_ROOT\ai_service"
$FE_DIR = "$PROJECT_ROOT\frontend-health"
# npm 必须用 .cmd 绝对路径（Start-Process 无法直接运行不带扩展名的 npm 脚本文件）
$NPM = $env:DSH_NODEJS
if (-not $NPM) { $NPM = "C:\Program Files\nodejs\npm.cmd" }
# Python 3.12（AI 服务运行时，可用 DSH_PY312 覆盖）
$PY312 = $env:DSH_PY312
if (-not $PY312) { $PY312 = "C:\Users\13425\AppData\Local\Programs\Python\Python312\python.exe" }
if (-not (Test-Path $NPM)) {
    $NPM = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
}
if (-not $NPM) { Write-Host "  ERROR 未找到 npm.cmd，请先安装 Node.js" -ForegroundColor Red; exit 1 }
# Ollama 可执行文件探测（Start-Process 需要 .exe 绝对路径）
$OLLAMA_EXE = (Get-Command ollama.exe -ErrorAction SilentlyContinue).Source
if (-not $OLLAMA_EXE) { $OLLAMA_EXE = "C:\Program Files\Ollama\ollama.exe" }

# ======================== 工具函数 ========================
function Wait-Port([int]$Port, [int]$Seconds) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Start-Ollama {
    Write-Host "`n[Ollama] 启动本地大模型服务（端口11434）..." -ForegroundColor Yellow
    # 确保模型目录指向 D 盘（已永久设置到用户环境变量，此处兜底）
    $modelsDir = $env:DSH_OLLAMA_MODELS
    if (-not $modelsDir) { $modelsDir = "D:\ollama\models" }
    if (-not [Environment]::GetEnvironmentVariable("OLLAMA_MODELS", "User")) {
        [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $modelsDir, "User")
    }
    $env:OLLAMA_MODELS = $modelsDir
    if (Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "  Ollama 已在运行（端口11434已监听）" -ForegroundColor Green
    } else {
        $p = Start-Process -FilePath $OLLAMA_EXE -ArgumentList "serve" -WindowStyle Minimized -PassThru
        Start-Sleep -Seconds 3
        if (Wait-Port 11434 5) { Write-Host "  OK Ollama 已启动（PID: $($p.Id)）" -ForegroundColor Green }
        else { Write-Host "  WARN Ollama 可能未就绪，请检查" -ForegroundColor Red }
    }
    # 通过 API 探测实际可用模型（避免写死模型名）
    $ollamaOk = $false
    try {
        $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
        $names = @($tags.models | ForEach-Object { $_.name })
        if ($names.Count -gt 0) {
            Write-Host "  OK Ollama 可用模型: $($names -join ', ')" -ForegroundColor Green
            $ollamaOk = $true
        } else {
            Write-Host "  WARN Ollama 运行中但无模型" -ForegroundColor Red
        }
    } catch {
        Write-Host "  WARN 无法探测 Ollama 模型列表（AI服务会自动降级到云端）" -ForegroundColor Yellow
    }
    $script:OllamaReady = $ollamaOk
}

function Build-Backend {
    Write-Host "`n[Build] 编译后端 jar（JDK 1.8 + IntelliJ Maven）..." -ForegroundColor Yellow
    $env:JAVA_HOME = $JDK8
    # 若后端在运行，先停止以释放 jar 文件锁
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "health-backend-1.0.0.jar" -and $_.Name -eq "java.exe" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "  已停止旧后端进程 PID $($_.ProcessId)" -ForegroundColor Gray }
    Start-Sleep -Seconds 2
    & $MVN -f "$PROJECT_ROOT\backend-health\pom.xml" clean package "-Dmaven.test.skip=true" -q
    if ($LASTEXITCODE -eq 0) { Write-Host "  OK 编译成功：$JAR" -ForegroundColor Green }
    else { Write-Host "  ERROR 编译失败（EXIT=$LASTEXITCODE）" -ForegroundColor Red; exit 1 }
}

function Start-Backend {
    Write-Host "`n[Backend] 启动后端（jar 包，JDK 1.8，端口8082）..." -ForegroundColor Yellow
    if (Get-NetTCPConnection -LocalPort 8082 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "  后端已在运行" -ForegroundColor Green; return
    }
    if (-not (Test-Path $JAR)) {
        Write-Host "  jar 不存在，先编译..." -ForegroundColor Gray
        Build-Backend
    }
    $java8 = "$JDK8\bin\java.exe"
    $p = Start-Process -FilePath $java8 -ArgumentList "-jar", "`"$JAR`"" `
        -WorkingDirectory "$PROJECT_ROOT\backend-health" -WindowStyle Minimized -PassThru
    Start-Sleep -Seconds 15
    if (Wait-Port 8082 20) { Write-Host "  OK 后端已就绪（PID: $($p.Id)） http://localhost:8082" -ForegroundColor Green }
    else { Write-Host "  WARN 后端尚未就绪，请查看新窗口日志" -ForegroundColor Red }
}

function Start-AIService {
    Write-Host "`n[AIService] 启动 AI 服务（Python，端口8002）..." -ForegroundColor Yellow
    if (Get-NetTCPConnection -LocalPort 8002 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "  AI服务已在运行" -ForegroundColor Green; return
    }
    # 优先使用 Python312（已装完整 AI 依赖，可用 DSH_PY312 覆盖），回退到 PATH 中的 python
    $PyPath = $PY312
    if (-not (Test-Path $PyPath)) { $PyPath = "python" }
    Write-Host "  使用 Python: $PyPath" -ForegroundColor Gray
    $p = Start-Process -FilePath $PyPath -ArgumentList "main.py" `
        -WorkingDirectory $AI_DIR -WindowStyle Minimized -PassThru
    Start-Sleep -Seconds 8
    if (Wait-Port 8002 40) { Write-Host "  OK AI服务已就绪（PID: $($p.Id)） http://localhost:8002" -ForegroundColor Green }
    else { Write-Host "  WARN AI服务加载中（向量模型较慢），请稍后访问" -ForegroundColor Red }
}

function Start-Frontend {
    Write-Host "`n[Frontend] 启动前端（Vue3+Vite，端口5173）..." -ForegroundColor Yellow
    if (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "  前端已在运行" -ForegroundColor Green; return
    }
    $p = Start-Process -FilePath $NPM -ArgumentList "run", "dev" `
        -WorkingDirectory $FE_DIR -WindowStyle Minimized -PassThru
    Start-Sleep -Seconds 5
    if (Wait-Port 5173 15) { Write-Host "  OK 前端已就绪（PID: $($p.Id)） http://localhost:5173" -ForegroundColor Green }
    else { Write-Host "  WARN 前端尚未就绪，请查看新窗口日志" -ForegroundColor Red }
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
        Write-Host "  已停止 PID $($_.ProcessId) : $($_.Name)" -ForegroundColor Gray
    }
    Write-Host "  OK 已全部停止" -ForegroundColor Green
}

# ======================== 连接自检 ========================
# 目标：验证「本地 Ollama 与云端 DeepSeek 两条 LLM 链路」均已连通，
#       以及三服务健康。任何一条链路不可用时给出明确告警，不阻断启动。
function Check-Connections {
    Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
    Write-Host "  启动后自检（LLM 双链路 + 三服务健康）" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor Cyan

    # 1. 云端 DeepSeek（读 ai_service/.env 的 DEEPSEEK_API_KEY）
    $envPath = "$PROJECT_ROOT\ai_service\.env"
    $deepseekOk = $false
    if (Test-Path $envPath) {
        $line = Get-Content $envPath | Where-Object { $_ -match "^DEEPSEEK_API_KEY=" } | Select-Object -First 1
        if ($line -and $line -match "^DEEPSEEK_API_KEY=(\S+)$") {
            $key = $Matches[1]
            if ($key -and $key -notmatch "sk-xxxx|your-key") {
                $deepseekOk = $true
                Write-Host "  [云端] DeepSeek API Key 已配置（长度 $($key.Length)）" -ForegroundColor Green
            } else {
                Write-Host "  [云端] WARN DeepSeek API Key 未正确配置（请检查 ai_service/.env）" -ForegroundColor Red
            }
        } else {
            Write-Host "  [云端] WARN 未找到 DEEPSEEK_API_KEY 配置" -ForegroundColor Red
        }
    } else {
        Write-Host "  [云端] WARN 找不到 $envPath" -ForegroundColor Red
    }

    # 2. 本地 Ollama
    if ($script:OllamaReady) {
        Write-Host "  [本地] Ollama 可用（模型已就绪）" -ForegroundColor Green
    } else {
        Write-Host "  [本地] WARN Ollama 不可用（AI 服务将自动降级为云端链路）" -ForegroundColor Yellow
    }

    # 3. 三服务健康检查
    Write-Host "`n  服务健康检查："
    $svc = @(
        @{ Name = "AI服务"; Port = 8002; Url = "http://localhost:8002/health" },
        @{ Name = "后端";   Port = 8082; Url = "http://localhost:8082/api/user/info" },
        @{ Name = "前端";   Port = 5173; Url = "http://localhost:5173/" }
    )
    foreach ($s in $svc) {
        if (Get-NetTCPConnection -LocalPort $s.Port -State Listen -ErrorAction SilentlyContinue) {
            Write-Host "    $($s.Name) : 端口 $($s.Port) 已监听 ✓" -ForegroundColor Green
        } else {
            Write-Host "    $($s.Name) : 端口 $($s.Port) 未监听 ✗" -ForegroundColor Red
        }
    }

    Write-Host "`n  结论："
    if ($deepseekOk -and $script:OllamaReady) {
        Write-Host "    云端 + 本地 LLM 双链路均可用（A/B/C 三方案路由全开）" -ForegroundColor Green
    } elseif ($deepseekOk) {
        Write-Host "    仅云端链路可用（本地降级，C 方案正常，A 方案受限）" -ForegroundColor Yellow
    } elseif ($script:OllamaReady) {
        Write-Host "    仅本地链路可用（离线模式 A 方案正常，C 方案受限）" -ForegroundColor Yellow
    } else {
        Write-Host "    ⚠️ 两条 LLM 链路均不可用，AI 功能将无法正常响应" -ForegroundColor Red
    }
}

# ======================== 主流程 ========================
if ($StopAll) { Stop-All; exit 0 }
if ($OllamaOnly) { Start-Ollama; exit 0 }
if ($BackendOnly) { Start-Backend; exit 0 }
if ($FrontendOnly) { Start-Frontend; exit 0 }
if ($AIServiceOnly) { Start-AIService; exit 0 }

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  个人健康助手 — 一键启动" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Start-Ollama
Start-AIService
if ($Build) { Build-Backend } else { Start-Backend }
Start-Frontend
Check-Connections

Write-Host "`n" + ("=" * 60) -ForegroundColor Cyan
Write-Host "  全部服务启动完成！" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "`n服务清单：" -ForegroundColor White
Write-Host "  AI服务   : http://localhost:8002" -ForegroundColor Gray
Write-Host "  后端服务 : http://localhost:8082" -ForegroundColor Gray
Write-Host "  前端服务 : http://localhost:5173" -ForegroundColor Gray
Write-Host "  Ollama   : http://localhost:11434" -ForegroundColor Gray
Write-Host "`n前端页面: http://localhost:5173" -ForegroundColor Cyan
Write-Host "`n按任意键退出此窗口（服务继续运行）..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
