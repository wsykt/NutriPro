# dsh (DeepSeek Harness) web UI launcher
# 注意：从 ASCII 路径启动，否则 CBM MCP (codebase-memory-mcp) 会拒绝 daemon session
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\13425'
& 'dsh' --profile web 2>&1
Write-Output "DSH_EXIT=$LASTEXITCODE"
