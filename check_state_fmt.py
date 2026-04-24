content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 persist 配置的完整 state
idx = content.find('qwenpaw-agent-storage"')
if idx >= 0:
    start = max(0, idx - 50)
    end = min(len(content), idx + 500)
    ctx = content[start:end]
    print('Persist config around qwenpaw-agent-storage:')
    print(ctx[:450])
    print()

# 查找 selectedAgent:"default" 来确认 state 结构
idx = content.find('selectedAgent:"default"')
if idx >= 0:
    start = max(0, idx - 100)
    end = min(len(content), idx + 100)
    ctx = content[start:end]
    print('selectedAgent initialization:')
    print(ctx)