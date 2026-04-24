content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 getAgentRunningConfig 的调用时机
import re

# 查找包含 getAgentRunningConfig 和 onFinish 的代码
pattern = r'getAgentRunningConfig[^}]+onFinish|onFinish[^}]+getAgentRunningConfig'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 100)
    end = min(len(content), m.end() + 200)
    ctx = content[start:end]
    print('getAgentRunningConfig + onFinish:')
    print(ctx[:400])
    print()