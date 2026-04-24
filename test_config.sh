#!/bin/bash
# 测试 QwenPaw running-config API

echo "=== 1. 获取 default agent 的 running-config (带 X-Agent-Id) ==="
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: default" | python3 -c "import sys,json; d=json.load(sys.stdin); print('memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo ""
echo "=== 2. 获取 QA agent 的 running-config (带 X-Agent-Id) ==="
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: QwenPaw_QA_Agent_0.2" | python3 -c "import sys,json; d=json.load(sys.stdin); print('memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo ""
echo "=== 3. 列出所有 agent 的配置文件 ==="
ls -la /root/.qwenpaw/workspaces/*/agent.json 2>/dev/null

echo ""
echo "=== 4. 检查 default agent.json 中的 memory_manager_backend ==="
grep memory_manager_backend /root/.qwenpaw/workspaces/default/agent.json 2>/dev/null

echo ""
echo "=== 5. 检查 QA agent.json 中的 memory_manager_backend ==="
grep memory_manager_backend /root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json 2>/dev/null