content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 workspace 组件如何获取 agent 数据
import re

# 查找 workspace 相关的 API 调用
patterns = [
    'getAgentConfig',
    'getAgentInfo',
    'getAgent',
    'fetchAgent',
    'loadAgent'
]

for p in patterns:
    count = content.count(p)
    if count > 0:
        print(f'{p}: {count} occurrences')

# 查找 workspace 页面如何响应 agent 变化
# 查找包含 pt 或 ho 的 workspace 相关代码
idx = content.find('path:"/workspace"')
if idx >= 0:
    # 查找这个组件的定义
    start = max(0, idx - 500)
    end = min(len(content), idx + 2000)
    ctx = content[start:end]
    print('\n=== Workspace route context ===')
    print(ctx[:1500])