content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 sessionStorage 相关的 storage key
import re
pattern = r'sessionStorage\.(getItem|setItem)\(["\']([^"\']+)["\']'
for m in re.finditer(pattern, content):
    key = m.group(2)
    action = m.group(1)
    print(f'sessionStorage.{action}("{key}")')
    # 打印上下文
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 100)
    ctx = content[start:end]
    print(f'  Context: {ctx[:100]}')
    print()