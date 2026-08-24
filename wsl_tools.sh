#!/bin/bash
# WSL 环境修复：Ollama models 路径 + JDK8 + Maven
set -x

# 1. Ollama: 让 systemd 服务使用 /root/.ollama/models
mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment=OLLAMA_MODELS=/root/.ollama/models\n' > /etc/systemd/system/ollama.service.d/override.conf
systemctl daemon-reload
systemctl restart ollama
sleep 4
echo "=== OLLAMA LIST ==="
ollama list

# 2. 清理 .bashrc 中之前写坏的 PATH 行，重新写入 Node + 工具路径
grep -v -E 'node-v24|JAVA_HOME|exportn' /root/.bashrc > /tmp/bashrc.clean
printf 'export PATH=/root/node-v24.19.0-linux-x64/bin:$PATH\n' >> /tmp/bashrc.clean
mv /tmp/bashrc.clean /root/.bashrc

# 3. 下载 JDK8 (Temurin) + Maven 3.9.6
mkdir -p /root/tools
cd /root/tools
if [ ! -d jdk8 ]; then
  echo "Downloading Temurin JDK8..."
  curl -fsSL -o jdk8.tar.gz "https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jdk/hotspot/normal/eclipse"
  mkdir -p jdk8 && tar xzf jdk8.tar.gz -C jdk8 --strip-components=1
  rm -f jdk8.tar.gz
fi
if [ ! -d maven ]; then
  echo "Downloading Maven 3.9.6..."
  curl -fsSL -o maven.tar.gz "https://archive.apache.org/dist/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.tar.gz"
  mkdir -p maven && tar xzf maven.tar.gz -C maven --strip-components=1
  rm -f maven.tar.gz
fi
echo "=== JDK ==="
/root/tools/jdk8/bin/java -version 2>&1
echo "=== MAVEN ==="
/root/tools/maven/bin/mvn -version 2>&1 | head -2
echo WSL_TOOLS_DONE
