import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 persist middleware 的 storage 配置
print('=== Looking for persist storage config ===')
for m in re.finditer(r'persist\s*\([^)]*storage[^)]*getItem[^)]*\)', content):
    ctx = content[m.start():m.end()+300]
    print(ctx[:400])
    print()
    break

# 查找 sessionStorage getItem 的完整上下文
print('=== sessionStorage getItem context ===')
idx = content.find('sessionStorage.getItem("qwenpaw-agent-storage")')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 500)
    ctx = content[start:end]
    print(ctx[:600])