content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 agent-config 相关的 API 调用
idx = content.find('path:"/agent-config"')
if idx >= 0:
    # 查找这个路径后面最近的代码块
    end = min(len(content), idx + 5000)
    area = content[idx:end]
    print('=== agent-config area ===')
    print(area[:3000])

# 查找 memory_manager_backend 相关的 useEffect
idx = content.find('memory_manager_backend')
if idx >= 0:
    start = max(0, idx - 500)
    end = min(len(content), idx + 500)
    ctx = content[start:end]
    print('\n=== memory_manager_backend context ===')
    print(ctx)