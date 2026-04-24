content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt store 的订阅
import re

# 查找 pt((state) => ...) 模式
pattern = r'pt\s*\(\s*\([^)]*\)\s*=>\s*\{[^}]*\}'
matches = list(re.finditer(pattern, content))
print(f'Found {len(matches)} pt() subscriptions')
for m in matches[:5]:
    ctx = content[m.start():m.end()+200]
    if 'selectedAgent' in ctx or 'agent' in ctx.lower():
        print(f'\npt() with agent:')
        print(ctx[:300])