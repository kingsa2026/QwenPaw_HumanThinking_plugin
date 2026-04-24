import re

js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'
with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print('=== File checks ===')
print('File size:', len(content))

# 检查 human_thinking 是否存在
ht_count = content.count('human_thinking')
print('human_thinking count:', ht_count)

# 检查 getAgentRunningConfig 的上下文
idx = content.find('getAgentRunningConfig')
if idx >= 0:
    print('\n=== getAgentRunningConfig context ===')
    print(repr(content[idx:idx+400]))

# 检查 X-Agent-Id 是否存在
xa_count = content.count('X-Agent-Id')
print('\nX-Agent-Id count:', xa_count)

# 检查是否有语法错误（如连续的括号）
if '})},{' in content:
    print('Warning: potential syntax issue with }},{')