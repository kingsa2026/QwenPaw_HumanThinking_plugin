content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 updateAgentRunningConfig
idx = content.find('updateAgentRunningConfig:')
if idx >= 0:
    end = content.find(',', idx + 50)
    if end > idx and end - idx < 600:
        impl = content[idx:end+1]
        print('=== updateAgentRunningConfig ===')
        print(impl[:400])
        print()

# 查找所有包含 /agent/running-config 的 N() 调用
import re
pattern = r'N\(["\']\/agent\/running-config["\'][^)]*\)'
matches = re.findall(pattern, content)
print(f'Found {len(matches)} /agent/running-config calls:')
for m in matches:
    print(f'  {m}')