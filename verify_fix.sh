#!/bin/bash
# 测试 API 是否正确返回各 agent 的 memory_manager_backend
echo "=== Testing API with X-Agent-Id ==="
echo "default agent:"
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: default" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo "QA agent:"
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: QwenPaw_QA_Agent_0.2" | python3 -c "import sys,json; d=json.load(sys.stdin); print('  memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo ""
echo "=== Checking agent.json files ==="
echo "default:"
grep memory_manager_backend /root/.qwenpaw/workspaces/default/agent.json
echo "QA:"
grep memory_manager_backend /root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json