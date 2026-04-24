#!/bin/bash
# 搜索 JS 中 memory_manager_backend 相关的 API 调用
grep -o 'memory_manager_backend[^,;)]*' /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js | sort | uniq -c | sort -rn | head -20