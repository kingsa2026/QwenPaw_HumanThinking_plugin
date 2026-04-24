content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 getAgentRunningConfig 完整实现
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    # 找到下一个逗号为止
    end = content.find(',', idx + 50)
    if end > idx and end - idx < 500:
        impl = content[idx:end+1]
        print('=== getAgentRunningConfig implementation ===')
        print(impl)
        print()

# 检查是否有 headers 传递
if 'headers:{"X-Agent-Id"' in content:
    print('✓ X-Agent-Id headers found in file')
else:
    print('✗ X-Agent-Id headers NOT properly structured')

# 查找实际的 API 调用
import re
matches = re.findall(r'return N\([^)]+\)', content)
print(f'\nFound {len(matches)} return N() calls')
for m in matches[:3]:
    print(f'  {m}')