#!/bin/bash
# 同步 Windows 修改到 WSL /root/health
set -x
SRC=/mnt/c/Users/13425/Desktop/个人健康助手/health/backend-health/src
DST=/root/health/backend-health/src
# 1. User.java 增加 avatar 字段
cp "$SRC/main/java/com/health/entity/User.java" "$DST/main/java/com/health/entity/User.java"
# 2. 删除死代码 AiChatController.java
rm -f "$DST/main/java/com/health/controller/AiChatController.java"
# 3. application.yml 补充 upload 配置
cp "$SRC/main/resources/application.yml" "$DST/main/resources/application.yml"
grep -l avatar "$DST/main/java/com/health/entity/User.java"
ls "$DST/main/java/com/health/controller/" | grep -i chat
echo SYNC_DONE
