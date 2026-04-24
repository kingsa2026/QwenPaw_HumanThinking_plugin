import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 qg 函数
match = re.search(r'function qg\([^)]+\)\{[^}]+\}', content)
if match:
    print('=== qg function ===')
    print(match.group(0)[:300])