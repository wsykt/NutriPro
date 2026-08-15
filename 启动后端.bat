@echo off
title Health Backend Spring Boot
color 0B
cd /d "c:\Users\lenovo\Desktop\个人健康助手\health\backend-health"
echo ========================================
echo   后端 Spring Boot 启动中...
echo   端口: 8082
echo ========================================
java -jar target\health-backend-1.0.0.jar
pause
