#!/bin/bash
# 检查 getAgentRunningConfig 的实际实现
grep -o 'getAgentRunningConfig[^}]*}' /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js | head -1 | cut -c1-300