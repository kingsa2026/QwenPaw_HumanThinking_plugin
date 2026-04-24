import subprocess
import os

# 备份目录
backup_dir = '/root/.qwenpaw/backup'

# 查找备份的 JS 文件
js_files = []
for root, dirs, files in os.walk(backup_dir):
    for f in files:
        if f.endswith('.js') and 'index' in f:
            js_files.append(os.path.join(root, f))

print('Found backup JS files:')
for f in js_files[:5]:
    print(f)

# 读取最新的备份
if js_files:
    latest = max(js_files, key=os.path.getmtime)
    print(f'\nReading: {latest}')

    with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 查找原始的 getAgentRunningConfig
    idx = content.find('getAgentRunningConfig:')
    if idx >= 0:
        end = content.find('},', idx + 50)
        if end > idx and end - idx < 500:
            impl = content[idx:end+2]
            print('\n=== Original getAgentRunningConfig ===')
            print(impl[:400])
    else:
        print('Original getAgentRunningConfig not found')
else:
    print('No backup JS files found')