import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt() 的初始化 state - selectedAgent 附近
print('=== Looking for pt() state initialization ===')
idx = content.find('selectedAgent:"default"')
if idx >= 0:
    # 往前找 state 定义
    start = max(0, idx - 300)
    end = min(len(content), idx + 200)
    ctx = content[start:end]
    print(f'Context around selectedAgent:"default":')
    print(ctx)
    print()

# 查找 getAgentRunningConfig 中的访问路径
print('=== Looking for the actual access pattern ===')
# 我们用 parsed?.state?.selectedAgent - 检查这是否正确
pattern = r'parsed\?\.[^;]{0,50}selectedAgent'
for m in re.finditer(pattern, content):
    ctx = m.group(0)[:60]
    print(f'  {ctx}')