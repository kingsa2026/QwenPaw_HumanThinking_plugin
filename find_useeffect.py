content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找这个 useCallback 和 useEffect 的关系
idx = content.find('getAgentRunningConfig()')
if idx >= 0:
    start = max(0, idx - 500)
    end = min(len(content), idx + 800)
    ctx = content[start:end]
    print('getAgentRunningConfig context:')
    print(ctx)