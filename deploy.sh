#!/bin/bash
# HumanThinking Plugin - 服务器端更新（仅需 git pull，代码自动同步由插件完成）
# 用法: bash deploy.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "=== HumanThinking Deploy ==="

if [ -d "$SCRIPT_DIR/.git" ]; then
    cd "$SCRIPT_DIR"
    git pull && echo "git pull done"
else
    echo "not a git repo, skipping pull"
fi

echo "Restarting QwenPaw..."
/root/.qwenpaw/bin/qwenpaw shutdown 2>/dev/null || true
sleep 3

cd /root/.qwenpaw
nohup ./venv/bin/qwenpaw app --host 0.0.0.0 --port 8088 > /tmp/qw_deploy.log 2>&1 &
echo "PID=$!"
echo "Waiting 40s for double restart..."
sleep 40

echo ""
echo "=== Done ==="
echo "Server: http://192.168.10.132:8088"
grep -i 'auto-sync\|started successfully' /root/.qwenpaw/qwenpaw.log | tail -5