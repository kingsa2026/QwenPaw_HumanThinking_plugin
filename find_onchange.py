content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 onChange:_ 中的 _ 函数定义
# 在 selectAgent 附近查找 _,= 或 _= 的定义
import re
pattern = r',_\s*=\s*[^,;]+selectAgent[^,;]+'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 200)
    print('Pattern 1:')
    print(content[start:end][:300])
    print()

# 另一种方式：查找 selectAgent 附近的函数定义
idx = content.find('selectAgent')
while idx >= 0 and idx < len(content):
    start = max(0, idx - 200)
    end = min(len(content), idx + 400)
    ctx = content[start:end]
    if '_,_' in ctx or '(_,n)' in ctx or 'setSelectedAgent' in ctx:
        print('Found selectAgent with setSelectedAgent:')
        print(ctx[:400])
        break
    idx = content.find('selectAgent', idx + 1)