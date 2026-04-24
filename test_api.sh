#!/bin/bash
echo "=== default agent ==="
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: default" | python3 -c "import sys,json; d=json.load(sys.stdin); print('memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo "=== QA agent ==="
curl -s "http://localhost:8088/api/agent/running-config" -H "X-Agent-Id: QwenPaw_QA_Agent_0.2" | python3 -c "import sys,json; d=json.load(sys.stdin); print('memory_manager_backend:', d.get('memory_manager_backend', 'NOT FOUND'))"

echo "=== agent.json files ==="
grep memory_manager_backend /root/.qwenpaw/workspaces/*/agent.json