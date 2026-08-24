#!/bin/bash
# Ollama 服务改为 root 运行（模型在 /root/.ollama/models）+ JAVA_HOME 配置
set -x
printf '[Service]\nUser=root\nEnvironment=OLLAMA_MODELS=/root/.ollama/models\n' > /etc/systemd/system/ollama.service.d/override.conf
systemctl daemon-reload
systemctl restart ollama
sleep 5
echo "=== OLLAMA LIST ==="
ollama list

# 配置 .bashrc：JAVA_HOME + MAVEN_HOME + Node
grep -v -E 'JAVA_HOME|MAVEN_HOME|node-v24' /root/.bashrc > /tmp/bashrc.clean2
printf 'export JAVA_HOME=/root/tools/jdk8\nexport MAVEN_HOME=/root/tools/maven\nexport PATH=$JAVA_HOME/bin:$MAVEN_HOME/bin:/root/node-v24.19.0-linux-x64/bin:$PATH\n' >> /tmp/bashrc.clean2
mv /tmp/bashrc.clean2 /root/.bashrc

export JAVA_HOME=/root/tools/jdk8
export MAVEN_HOME=/root/tools/maven
export PATH=$JAVA_HOME/bin:$MAVEN_HOME/bin:/root/node-v24.19.0-linux-x64/bin:$PATH
/root/tools/maven/bin/mvn -version 2>&1 | head -2
echo OLLAMA_FIX_DONE
