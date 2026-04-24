import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 zustand createStore 或类似模式
print('=== Looking for zustand store creation ===')
for m in re.finditer(r'zustand[^;]{0,200}', content):
    ctx = m.group(0)[:150]
    if 'create' in ctx.lower() and ('storage' in ctx.lower() or 'agent' in ctx.lower()):
        print(f'  ...{ctx}...')
        print()

# 查找 sessionStorage 相关但不是 getItem 的模式
print('\n=== sessionStorage raw usage ===')
for m in re.finditer(r'sessionStorage[^;]{0,100}', content):
    ctx = m.group(0)[:100]
    if 'qwenpaw' in ctx.lower():
        print(f'  ...{ctx}...')