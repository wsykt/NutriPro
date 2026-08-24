$ErrorActionPreference='Continue'
Set-Location 'C:\Users\13425\Desktop\个人健康助手\health\ai_service'
$env:TRANSFORMERS_OFFLINE='1'
& 'C:\Users\13425\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\vm\tools\python\python.exe' main.py 2>&1
Write-Output "AI_EXIT=$LASTEXITCODE"