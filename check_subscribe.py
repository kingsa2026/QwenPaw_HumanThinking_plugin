content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 subscribe 的用法
import re
pattern = r'\.subscribe\s*\([^)]+\)'
for m in re.finditer(pattern, content):
    ctx_start = max(0, m.start() - 50)
    ctx_end = min(len(content), m.end() + 100)
    ctx = content[ctx_start:ctx_end]
    if 'selectedAgent' in ctx or 'agent' in ctx.lower():
        print('subscribe context with agent:')
        print(ctx[:200])
        print()