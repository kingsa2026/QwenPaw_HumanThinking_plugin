import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 sessionStorage getItem
idx = content.find('sessionStorage.getItem("qwenpaw-agent-storage")')
if idx >= 0:
    start = max(0, idx - 300)
    end = min(len(content), idx + 500)
    print('Context around qwenpaw-agent-storage:')
    print(content[start:end])