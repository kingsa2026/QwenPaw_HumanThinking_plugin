import re

js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'
with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 检查 updateAgentRunningConfig 是否完整
idx = content.find('updateAgentRunningConfig')
if idx >= 0:
    print('=== updateAgentRunningConfig context ===')
    print(repr(content[idx:idx+500]))

# 检查是否有未闭合的括号
open_parens = content.count('(')
close_parens = content.count(')')
print(f'\nParentheses: ( = {open_parens}, ) = {close_parens}')

# 检查 getAgentRunningConfig 后面的代码是否正确终止
pattern = r'return N\("/agent/running-config",\{headers:\{"X-Agent-Id":agentId\}\}\);'
matches = re.findall(pattern, content)
print(f'\nComplete return statements: {len(matches)}')

# 检查是否有 },{ 序列后面跟着不完整代码
bad_pattern = r'\},\{[^}]*\}?\w{0,30}$'
matches = re.findall(bad_pattern, content[-5000:])
if matches:
    print('\nPotential issues near end:')
    for m in matches[:3]:
        print(f'  ...{m[:50]}...')