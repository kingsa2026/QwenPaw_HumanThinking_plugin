content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 useEffect 和 getAgentRunningConfig 的关系
idx = content.find('getAgentRunningConfig')
while idx >= 0 and idx < len(content):
    end_idx = min(len(content), idx + 300)
    ctx = content[idx:end_idx]
    if 'useEffect' in ctx or 'y()' in ctx or 'D.getAgentRunningConfig' in ctx:
        print('Context around getAgentRunningConfig:')
        print(ctx[:250])
        print()
        break
    idx = content.find('getAgentRunningConfig', idx + 1)

# 查找 Agent 切换时的处理
idx = content.find('setSelectedAgent')
while idx >= 0 and idx < len(content):
    end_idx = min(len(content), idx + 200)
    ctx = content[idx:end_idx]
    if 'getAgentRunningConfig' in ctx or 'fetch' in ctx.lower():
        print('Agent switch handling:')
        print(ctx[:200])
        print()
        break
    idx = content.find('setSelectedAgent', idx + 1)