import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 qwenpaw-agent-storage 的使用
print('=== qwenpaw-agent-storage contexts ===')
for m in re.finditer(r'qwenpaw-agent-storage[^}]{0,150}', content):
    ctx = m.group(0)
    if 'selectedAgent' in ctx or 'parse' in ctx or 'state' in ctx:
        print(f'  ...{ctx[:120]}...')
        print()