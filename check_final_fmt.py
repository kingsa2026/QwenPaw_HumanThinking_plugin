content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 qwenpaw-agent-storage 附近的 persist 配置
idx = content.find('qwenpaw-agent-storage"')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 400)
    ctx = content[start:end]
    print('Context around qwenpaw-agent-storage:')
    print(ctx)
    print()

# 查找 state 的结构
idx = content.find('selectedAgent:"default"')
if idx >= 0:
    start = max(0, idx - 300)
    end = min(len(content), idx + 100)
    ctx = content[start:end]
    print('State structure around selectedAgent:')
    print(ctx)