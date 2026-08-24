$ErrorActionPreference='Continue'
Set-Location 'C:\Users\13425\Desktop\个人健康助手\health\frontend-health'
& 'C:\Program Files\nodejs\npm.cmd' run dev 2>&1
Write-Output "FE_EXIT=$LASTEXITCODE"