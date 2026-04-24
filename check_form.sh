#!/bin/bash
# 查找表单提交相关的 API 调用
grep -o 'onFinish\|onSubmit\|updateAgentConfig\|putAgentConfig[^,;)]*' /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js | sort | uniq | head -10