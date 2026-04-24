import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt = create((state, actions) => 或类似的 zustand store 定义
print('=== Looking for pt() or agent store definition ===')
for m in re.finditer(r'pt\s*=\s*create\s*\(\s*\([^)]*state[^)]*\)\s*=>', content):
    ctx = content[m.start():m.end()+500]
    print(f'  ...{ctx[:400]}...')
    print()

# 查找 selectedAgent 在 state 中的定义
print('\n=== Looking for selectedAgent in state ===')
for m in re.finditer(r'selectedAgent[^,}]+[,}]', content):
    ctx = m.group(0)[:100]
    if 'state' in ctx or 'setSelectedAgent' in ctx:
        print(f'  ...{ctx}...')