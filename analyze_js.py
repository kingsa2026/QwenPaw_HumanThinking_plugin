import re

# 读取本地 JS 文件（如果有的话）
js_path = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'
try:
    with open(js_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
except:
    print("Cannot read remote JS file locally")
    exit(1)

# 查找 updateAgentConfig 的定义和调用
print("=== Looking for updateAgentConfig ===")
idx = content.find('updateAgentConfig:')
if idx >= 0:
    end = content.find(',', idx + 50)
    if end > idx and end - idx < 500:
        print("updateAgentConfig definition:")
        print(content[idx:end][:300])
        print()

# 查找 getAgentRunningConfig
print("=== Looking for getAgentRunningConfig ===")
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    end = content.find(',', idx + 50)
    if end > idx and end - idx < 500:
        print("getAgentRunningConfig definition:")
        print(content[idx:end][:300])