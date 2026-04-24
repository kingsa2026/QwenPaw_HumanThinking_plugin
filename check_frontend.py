import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 memory_manager_backend 的使用
print('=== memory_manager_backend contexts ===')
for m in re.finditer(r'memory_manager_backend[^}]{0,200}', content):
    ctx = m.group(0)[:150]
    if 'value' in ctx or 'default' in ctx or 'option' in ctx.lower():
        print(f'  ...{ctx}...')
        print()