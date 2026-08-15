@echo off
title Health Frontend Vite
color 0A
cd /d "c:\Users\lenovo\Desktop\个人健康助手\health\frontend-health"
echo ========================================
echo   前端 Vite 启动中...
echo   端口: 5173
echo ========================================
call node_modules\.bin\vite.cmd --port 5173 --host
pause
