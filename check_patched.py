content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 updateAgentRunningConfig
idx = content.find('updateAgentRunningConfig:')
if idx >= 0:
    end = content.find('},', idx + 50)
    if end > idx and end - idx < 600:
        impl = content[idx:end+2]
        print('=== updateAgentRunningConfig ===')
        print(impl[:400])
        print()
        if 'X-Agent-Id' in impl:
            print('✓ Has X-Agent-Id header')
        else:
            print('✗ MISSING X-Agent-Id header')

# 查找 getAgentRunningConfig
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    end = content.find('},', idx + 50)
    if end > idx and end - idx < 400:
        impl = content[idx:end+2]
        print('\n=== getAgentRunningConfig ===')
        print(impl[:350])
        print()
        if 'X-Agent-Id' in impl:
            print('✓ Has X-Agent-Id header')
        else:
            print('✗ MISSING X-Agent-Id header')