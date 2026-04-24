import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 persist 或 zustand persist 模式
print('=== Looking for persist middleware ===')
patterns = [
    r'persist\s*\(',
    r'\.persist\s*\(',
    r'storage:\s*sessionStorage',
    r'sessionStorage.*storage',
]

for p in patterns:
    matches = list(re.finditer(p, content))
    if matches:
        print(f'Pattern "{p}": {len(matches)} matches')
        for m in matches[:2]:
            ctx = content[max(0, m.start()-50):m.end()+100]
            print(f'  Context: ...{ctx[:150]}...')
            print()

# 查找 pt() 函数或 store 定义
print('=== Looking for pt() or agent store ===')
for m in re.finditer(r'pt\s*=\s*\([^)]+\)\s*=>', content):
    ctx = content[m.start():m.end()+200]
    print(f'  ...{ctx[:200]}...')
    print()