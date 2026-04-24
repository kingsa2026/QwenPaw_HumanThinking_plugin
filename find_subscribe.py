content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找所有 subscribe 调用
import re
pattern = r'\.subscribe\s*\([^)]+\)'
matches = list(re.finditer(pattern, content))
print(f'Found {len(matches)} subscribe calls')
for m in matches[:5]:
    ctx_start = max(0, m.start() - 30)
    ctx_end = min(len(content), m.end() + 80)
    ctx = content[ctx_start:ctx_end]
    print(f'  ...{ctx[:150]}...')
    print()