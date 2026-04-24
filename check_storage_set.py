import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 sessionStorage.setItem("qwenpaw-agent-storage"
print('=== qwenpaw-agent-storage setItem contexts ===')
for m in re.finditer(r'sessionStorage\.setItem\(["\']qwenpaw-agent-storage["\'][^;]+;', content):
    ctx = m.group(0)[:200]
    print(f'  ...{ctx}...')
    print()

# 查找 create(qwenpaw-agent-storage 模式
print('=== create(qwenpaw-agent-storage contexts ===')
for m in re.finditer(r'create\(["\']qwenpaw-agent-storage["\'][^}]+}', content):
    ctx = m.group(0)[:300]
    print(f'  ...{ctx}...')
    print()