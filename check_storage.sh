#!/bin/bash
# 检查 JS 文件中 sessionStorage 的实际使用方式
grep -A5 'qwenpaw-agent-storage' /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js | head -30