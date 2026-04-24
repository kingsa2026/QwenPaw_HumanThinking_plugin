import re
js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'
content = open(js_file, 'r', encoding='utf-8', errors='ignore').read()

# 查找 getAgentRunningConfig 的上下文
idx = content.find('getAgentRunningConfig')
if idx >= 0:
    print('=== getAgentRunningConfig context ===')
    print(repr(content[idx:idx+350]))
    print()

# 检查是否有 N(" 后面直接跟 URL 的情况
patterns = [
    'N("/agent/running-config",{headers:{"X-Agent-Id":agentId}})',
    'N("/agent/running-config",{method:"PUT"',
]
for p in patterns:
    if p in content:
        print(f"Found pattern: {p[:50]}...")
    else:
        print(f"NOT found: {p[:50]}...")