import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 getAgentRunningConfig 完整调用链
idx = content.find('getAgentRunningConfig')
if idx >= 0:
    # 查找调用 getAgentRunningConfig 的地方
    call_pattern = r'D\.getAgentRunningConfig\(\)'
    for m in re.finditer(call_pattern, content):
        start = max(0, m.start() - 100)
        end = min(len(content), m.end() + 300)
        ctx = content[start:end]
        print('=== getAgentRunningConfig() call context ===')
        print(ctx)
        print()

# 检查是否有缓存机制
cache_patterns = ['cache', 'cached', 'Cache']
for p in cache_patterns:
    count = content.lower().count(p.lower())
    if count > 0:
        print(f'{p}: {count} occurrences')