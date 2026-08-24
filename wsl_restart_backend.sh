#!/bin/bash
# 重启后端：验证 jar 干净 + 启动 :8082
set -x
export JAVA_HOME=/root/tools/jdk8
export PATH=$JAVA_HOME/bin:$PATH
cd /root/health/backend-health

# 验证 jar 内无 AiChatController
unzip -l target/health-backend-1.0.0.jar 2>/dev/null | grep -i aichat && echo "WARN: AICHAT STILL IN JAR" || echo "JAR_CLEAN_OK"

# 停旧进程
pkill -f health-backend-1.0.0.jar 2>/dev/null
sleep 2

# 启动
nohup java -Djava.net.preferIPv4Stack=true -jar target/health-backend-1.0.0.jar > /root/logs/backend.log 2>&1 &
echo "backend pid: $!"
sleep 25
if ss -tln | grep -q ':8082 '; then
  echo "PORT 8082: LISTENING"
else
  echo "PORT 8082: NOT LISTENING"
  tail -20 /root/logs/backend.log
fi
echo BACKEND_RESTART_DONE
