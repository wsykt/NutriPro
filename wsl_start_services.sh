#!/bin/bash
# WSL 健康助手一键启动脚本（项目 4 服务 + dsh）
# 用法：bash wsl_start_services.sh
# 注意：
#   - 日志统一写到 /root/health/logs（沙箱环境 /root/logs 可能被拦截）
#   - dsh 本体装在 Windows 侧，WSL 直启会卡在 /mnt/c (9p) 访问，统一用 powershell 在 Windows 侧拉起
set -x
LOGDIR=/root/health/logs
mkdir -p "$LOGDIR"
export JAVA_HOME=/root/tools/jdk8
export MAVEN_HOME=/root/tools/maven
export PATH=/root/node-v24.19.0-linux-x64/bin:$JAVA_HOME/bin:$MAVEN_HOME/bin:$PATH

# 1. Ollama (systemd)
if systemctl is-active --quiet ollama; then
  echo "ollama: already active"
else
  systemctl start ollama && sleep 2
fi
curl -s http://localhost:11434/api/tags | head -c 300; echo
echo "OLLAMA_OK"

# 2. AI 服务 :8002
if pgrep -f "uvicorn main:app" >/dev/null; then
  echo "ai_service: already running"
else
  cd /root/health/ai_service
  source venv/bin/activate
  nohup uvicorn main:app --host 0.0.0.0 --port 8002 > "$LOGDIR/ai_service.log" 2>&1 &
  echo "ai_service pid: $!"
fi

# 3. 后端 :8082（强制 IPv4，否则 Windows localhost 转发不通）
if pgrep -f "health-backend-1.0.0.jar" >/dev/null; then
  echo "backend: already running"
else
  cd /root/health/backend-health
  nohup java -Djava.net.preferIPv4Stack=true -jar target/health-backend-1.0.0.jar > "$LOGDIR/backend.log" 2>&1 &
  echo "backend pid: $!"
fi

# 4. 前端 :5173（setsid 脱离会话，防止 wsl 命令退出时被回收；绑 0.0.0.0 供 Windows 访问）
if pgrep -f "vite.js --host" >/dev/null; then
  echo "frontend: already running"
else
  cd /root/health/frontend-health
  setsid nohup /root/node-v24.19.0-linux-x64/bin/node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 </dev/null > "$LOGDIR/frontend.log" 2>&1 &
  echo "frontend pid: $!"
fi

# 5. dsh web UI :3080（Windows 侧启动；--no-open 不自动开浏览器）
DASH_UP=$(powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 3080 -ErrorAction SilentlyContinue | Where-Object State -eq Listen | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null | tr -d '\r')
if [ "$DASH_UP" = "1" ]; then
  echo "dsh: already running (http://127.0.0.1:3080)"
else
  cd /root/health
  nohup powershell.exe -NoProfile -Command "Set-Location 'C:\Users\13425'; & 'dsh' --profile web --no-open 2>&1" > "$LOGDIR/dsh.log" 2>&1 &
  echo "dsh pid: $!"
  sleep 8
fi

sleep 8
echo "---- PORT CHECK ----"
for p in 11434 8002 8082 5173; do
  if ss -tlnp 2>/dev/null | grep -q ":$p "; then
    echo "PORT $p: LISTENING"
  else
    echo "PORT $p: NOT LISTENING"
  fi
done
DASH_UP2=$(powershell.exe -NoProfile -Command "Get-NetTCPConnection -LocalPort 3080 -ErrorAction SilentlyContinue | Where-Object State -eq Listen | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null | tr -d '\r')
echo "PORT 3080 (dsh): $([ "$DASH_UP2" = "1" ] && echo LISTENING || echo NOT LISTENING)"
echo ALL_SERVICES_STARTED
