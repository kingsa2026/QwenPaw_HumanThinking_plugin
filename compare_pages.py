content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 workspace 页面和 agent-config 页面的实现
# workspace 路径
workspace_paths = ['/workspace', '/agent/workspace', 'workspacePath']
agent_config_paths = ['/agent-config', '/agent/config', 'agentConfig']

# 查找组件
for p in workspace_paths:
    if p in content:
        print(f'Found workspace path: {p}')

for p in agent_config_paths:
    if p in content:
        print(f'Found agent-config path: {p}')

# 查找两个页面的 useEffect 或重新加载逻辑
import re
# 查找包含 agent 或 selectedAgent 的 useEffect
pattern = r'useEffect[^}]*selectedAgent[^}]*\}'
matches = list(re.finditer(pattern, content))
print(f'\nFound {len(matches)} useEffect with selectedAgent')
for m in matches[:3]:
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 200)
    ctx = content[start:end]
    print(f'\nContext: {ctx[:300]}')