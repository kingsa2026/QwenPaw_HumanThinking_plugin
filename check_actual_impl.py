import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 getAgentRunningConfig 完整实现
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    # 找到函数结束的完整实现
    end = idx
    brace_count = 0
    started = False
    for i in range(idx, min(idx + 500, len(content))):
        if content[i] == '{':
            brace_count += 1
            started = True
        elif content[i] == '}':
            brace_count -= 1
            if started and brace_count == 0:
                end = i + 1
                break

    impl = content[idx:end]
    print('=== getAgentRunningConfig implementation ===')
    print(impl)
    print()

    # 检查是否包含 headers
    if 'headers' in impl and 'X-Agent-Id' in impl:
        print('✓ getAgentRunningConfig has X-Agent-Id headers')
    else:
        print('✗ getAgentRunningConfig MISSING X-Agent-Id headers')

# 检查 sessionStorage
if 'qwenpaw-agent-storage' in content:
    count = content.count('qwenpaw-agent-storage')
    print(f'qwenpaw-agent-storage found: {count} times')
else:
    print('✗ qwenpaw-agent-storage NOT found')