content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 agent-config 和 workspace 组件的定义
import re

# 查找组件定义（可能有函数名）
patterns = [
    r'function\s+\w*Workspace\w*',
    r'function\s+\w*[Aa]gent[Cc]onfig\w*',
    r'const\s+\w*[Ww]orkspace\s*=',
    r'const\s+\w*[Aa]gent[Cc]onfig\s*='
]
for p in patterns:
    for m in re.finditer(p, content):
        ctx = content[m.start():m.end()+50]
        print(f'{p}: {ctx[:60]}')

# 查找关键差异：workspace 可能使用了 pt store
# 查找 /workspace 路由对应的组件是否使用了 pt
idx = content.find('path:"/workspace"')
if idx >= 0:
    # 向前查找组件定义
    start = max(0, idx - 2000)
    component_area = content[start:idx]
    # 查找最近的组件定义
    comp_match = re.search(r'component:\w+', component_area)
    if comp_match:
        print(f'\nWorkspace component: {comp_match.group(0)}')

idx = content.find('path:"/agent-config"')
if idx >= 0:
    start = max(0, idx - 2000)
    component_area = content[start:idx]
    comp_match = re.search(r'component:\w+', component_area)
    if comp_match:
        print(f'Agent-config component: {comp_match.group(0)}')