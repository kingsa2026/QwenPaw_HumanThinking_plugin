content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt.subscribe 的用法
import re
pattern = r'pt\.subscribe'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 200)
    ctx = content[start:end]
    print('pt.subscribe context:')
    print(ctx[:300])
    print()