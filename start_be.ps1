$ErrorActionPreference='Continue'
Set-Location 'C:\Users\13425\Desktop\个人健康助手\health\backend-health'
& 'C:\Program Files\Java\jdk1.8.0_341\bin\java.exe' -jar 'target\health-backend-1.0.0.jar' 2>&1
Write-Output "BE_EXIT=$LASTEXITCODE"