content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找 getAgentRunningConfig() 被调用的位置
import re
pattern = r'getAgentRunningConfig\s*\(\s*\)'
count = 0
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 150)
    end = min(len(content), m.end() + 100)
    ctx = content[start:end]
    print(f'getAgentRunningConfig() call #{count+1}:')
    print(ctx[:250])
    print()
    count += 1
    if count >= 5:
        break