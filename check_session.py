import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找所有 sessionStorage getItem 调用
items = re.findall(r'sessionStorage\.getItem\(["\']([^"\']+)["\']\)', content)
print('=== sessionStorage.getItem keys ===')
for item in set(items):
    print(f'  {item}: {items.count(item)} times')

# 查找 selectedAgent 相关内容
print('\n=== selectedAgent contexts ===')
for m in re.finditer(r'selectedAgent[^;]{0,100}', content):
    print(f'  ...{m.group(0)[:80]}...')