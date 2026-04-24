content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找 agent-config 页面的 getAgentRunningConfig 相关代码
# 对比原生代码和我们注入的代码

# 1. 查找 getAgentRunningConfig 的定义
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    end = content.find('},', idx + 50)
    if end > idx and end - idx < 500:
        impl = content[idx:end+2]
        print('=== getAgentRunningConfig (patched) ===')
        print(impl[:400])
        print()

# 2. 查找 updateAgentRunningConfig 的定义
idx = content.find('updateAgentRunningConfig:')
if idx >= 0:
    end = content.find('},', idx + 50)
    if end > idx and end - idx < 600:
        impl = content[idx:end+2]
        print('=== updateAgentRunningConfig (patched) ===')
        print(impl[:400])
        print()

# 3. 检查是否有 human_thinking 相关注入
if 'human_thinking' in content.lower():
    print('=== human_thinking found in JS ===')
    count = content.lower().count('human_thinking')
    print(f'human_thinking occurrences: {count}')

# 4. 检查 memory_manager_backend 下拉菜单
idx = content.find('memory_manager_backend')
if idx >= 0:
    start = max(0, idx - 50)
    end = min(len(content), idx + 200)
    ctx = content[start:end]
    print('\n=== memory_manager_backend context ===')
    print(ctx[:300])