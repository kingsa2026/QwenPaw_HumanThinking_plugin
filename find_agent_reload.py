content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 Agent 切换后重新加载配置的代码
import re
# 查找 onSelect 或 onChange 中包含 reload 或 fetch 或 getAgentConfig 的模式
patterns = [
    r'onChange[^}]*(fetch|reload|getConfig|loadConfig)',
    r'selectAgent[^}]*(fetch|reload|getConfig|loadConfig)',
    r'switchAgent[^}]*(fetch|reload|getConfig|loadConfig)',
    r'setSelectedAgent[^}]*(fetch|reload|getConfig|loadConfig)'
]
for p in patterns:
    for m in re.finditer(p, content):
        start = max(0, m.start() - 50)
        end = min(len(content), m.end() + 150)
        ctx = content[start:end]
        print(f'Pattern: {p[:50]}')
        print(ctx[:250])
        print()