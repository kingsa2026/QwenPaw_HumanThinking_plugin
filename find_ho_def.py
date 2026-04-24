content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 ho 的完整定义
import re
pattern = r'ho\s*=\s*[^;,]+'
for m in re.finditer(pattern, content):
    ctx = m.group(0)[:300]
    print(f'ho = {ctx[:200]}')
    print()