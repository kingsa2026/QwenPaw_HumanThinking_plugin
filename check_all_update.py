content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

import re

# 查找所有 updateAgentRunningConfig
matches = list(re.finditer(r'updateAgentRunningConfig', content))
print(f'Found {len(matches)} occurrences of updateAgentRunningConfig')

for i, m in enumerate(matches):
    start = m.start()
    end = content.find('},', start + 50)
    if end > start and end - start < 700:
        impl = content[start:end+2]
        print(f'\n=== Occurrence {i+1} ===')
        print(impl[:350])
        if 'headers' in impl:
            print('✓ Has headers')
        else:
            print('✗ NO headers')