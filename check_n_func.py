content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 N 函数的定义
import re
match = re.search(r'function N\(e,o=\{\}\)\{[^}]+\}', content)
if match:
    print('N function:')
    print(match.group(0)[:300])
else:
    print('N function not found')

# 检查 getAgentRunningConfig 的当前状态
idx = content.find('getAgentRunningConfig')
if idx >= 0:
    print('\ngetAgentRunningConfig:')
    print(content[idx:idx+250])