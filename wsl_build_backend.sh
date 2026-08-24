#!/bin/bash
# WSL 后端 Maven 构建脚本
set -x
export JAVA_HOME=/root/tools/jdk8
export MAVEN_HOME=/root/tools/maven
export PATH=$JAVA_HOME/bin:$MAVEN_HOME/bin:$PATH
cd /root/health/backend-health
mvn -q clean package -DskipTests -Dmaven.test.skip=true 2>&1 | tail -30
echo "BUILD_EXIT=${PIPESTATUS[0]}"
ls -la target/*.jar 2>/dev/null
echo BACKEND_BUILD_DONE
