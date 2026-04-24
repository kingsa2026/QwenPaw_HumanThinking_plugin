content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找原生代码中 getAgentRunningConfig 被调用的完整上下文
idx = content.find('getAgentRunningConfig()')
if idx >= 0:
    start = max(0, idx - 300)
    end = min(len(content), idx + 500)
    ctx = content[start:end]
    print('=== Native call context ===')
    print(ctx)
    print()

# 查找原生代码中 getAgentRunningConfig 的 useEffect 依赖
# 查找 y=r.useCallback(async()=>{...D.getAgentRunningConfig()...
pattern = r'y=r\.useCallback\(async\(\)=>\{[^}]*getAgentRunningConfig[^}]*\},[^)]+\)'
import re
for m in re.finditer(pattern, content):
    ctx = content[m.start():m.end()+200]
    print('=== Native useCallback ===')
    print(ctx[:500])