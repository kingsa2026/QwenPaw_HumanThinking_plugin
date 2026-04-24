content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 workspace 和 agent-config 的组件定义
import re

# 查找包含路径定义和组件的代码块
patterns = [
    (r'path["\']:/agent-config["\'][^}]+component[^,}]+', 'agent-config'),
    (r'path["\']:/workspace["\'][^}]+component[^,}]+', 'workspace'),
    (r'path:"/agent-config"[^}]+}', 'agent-config'),
    (r'path:"/workspace"[^}]+}', 'workspace'),
]

for pattern, name in patterns:
    for m in re.finditer(pattern, content):
        ctx = content[m.start():m.end()+100]
        print(f'\n=== {name} ===')
        print(ctx[:250])
        break

# 查找页面重新渲染的 key
print('\n\n=== 查找 key 或 re-render 机制 ===')
# 查找页面路由切换时是否会改变 key
key_patterns = ['key:', 're-render', 'forceUpdate']
for p in key_patterns:
    count = content.count(p)
    print(f'{p}: {count} occurrences')