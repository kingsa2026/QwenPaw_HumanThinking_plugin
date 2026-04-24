#!/bin/bash
# 搜索 QwenPaw 如何获取当前选中的 agent
grep -o 'selectedAgent[^,;)]*' /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js | sort | uniq -c | sort -rn | head -10