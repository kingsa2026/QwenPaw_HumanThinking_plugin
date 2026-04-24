content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 AgentConfig 或 agent 相关的 onChange
patterns = [
    'AgentConfig',
    'agentChange',
    'onAgentChange',
    'selectedAgentChange'
]
for p in patterns:
    count = content.count(p)
    if count > 0:
        print(f'{p}: {count} occurrences')

# 查找 Agent 切换时的处理 - 点击下拉菜单后的处理
# 查找 dropdown onChange
import re
pattern = r'onChange[^,;{]+selectedAgent'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 150)
    ctx = content[start:end]
    print(f'\nonChange selectedAgent: {ctx[:200]}')