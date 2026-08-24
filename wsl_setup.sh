#!/bin/bash
# WSL 环境配置脚本：Node PATH + 依赖安装
# 用法：wsl -d Ubuntu-22.04 -- bash /mnt/c/Users/13425/Desktop/个人健康助手/wsl_setup.sh <step>
set -x
export PATH=/root/node-v24.19.0-linux-x64/bin:$PATH

step=${1:-all}

node -v && npm -v || echo "NODE_CHECK_FAIL"

if [ "$step" = "all" ] || [ "$step" = "frontend" ]; then
  cd /root/health/frontend-health && npm install --no-audit --no-fund 2>&1 | tail -5 && echo FRONTEND_NPM_DONE
fi

if [ "$step" = "all" ] || [ "$step" = "dsh-run" ]; then
  cd /root/dsh-run && npm install --no-audit --no-fund 2>&1 | tail -5 && echo DSH_RUN_NPM_DONE
fi

if [ "$step" = "all" ] || [ "$step" = "ai" ]; then
  cd /root/health/ai_service
  python3 --version
  if [ ! -d venv ]; then
    python3 -m venv venv
  fi
  source venv/bin/activate
  pip install --upgrade pip -q
  pip install -r requirements.txt 2>&1 | tail -8
  echo AI_PIP_DONE
fi

echo SETUP_STEP_${step}_COMPLETE
