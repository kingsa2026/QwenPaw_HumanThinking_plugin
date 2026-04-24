content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 qwenpaw-agent-storage 相关的代码
import re

# 查找 setItem 存储
idx = content.find('qwenpaw-agent-storage')
while idx >= 0 and idx < len(content):
    start = max(0, idx - 100)
    end = min(len(content), idx + 300)
    ctx = content[start:end]

    if 'setItem' in ctx or 'persist' in ctx.lower():
        print('Storage context:')
        print(ctx[:300])
        print()
        break

    idx = content.find('qwenpaw-agent-storage', idx + 1)

# 查找 persist middleware 的 storage 配置
pattern = r'persist\s*\([^)]*storage[^)]*\)'
for m in re.finditer(pattern, content):
    ctx = content[m.start():m.end()+200]
    if 'sessionStorage' in ctx:
        print('Persist storage config:')
        print(ctx[:400])
        print()
        break

# 查找 pt store 的 state 初始化
pattern = r'pt\s*=\s*pt\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*state[^}]*\}'
for m in re.finditer(pattern, content):
    ctx = content[m.start():m.end()+300]
    if 'selectedAgent' in ctx:
        print('pt store state:')
        print(ctx[:300])
        print()
        break