import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 selectedAgent 的所有上下文
print('=== All selectedAgent contexts ===')
for m in re.finditer(r'selectedAgent[^,;){]{0,80}', content):
    ctx = m.group(0)[:80]
    print(f'  {ctx}')