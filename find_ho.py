content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 ho 对象（可能是路由或状态管理器）
import re
pattern = r'ho\s*=\s*[^{]+'
for m in re.finditer(pattern, content):
    ctx = m.group(0)[:150]
    if 'subscribe' in ctx or 'listen' in ctx or 'on(' in ctx:
        print(f'ho definition: {ctx}')

# 查找 ho 的方法
pattern = r'ho\.(subscribe|listen|on|emit|addRoutes)'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 100)
    ctx = content[start:end]
    print(f'\nho method: {ctx[:150]}')