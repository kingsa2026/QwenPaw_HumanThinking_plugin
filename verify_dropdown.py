content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找 human_thinking 选项
if 'value:"human_thinking"' in content:
    print('✓ human_thinking option found in dropdown!')
    idx = content.find('value:"human_thinking"')
    start = max(0, idx - 50)
    end = min(len(content), idx + 200)
    ctx = content[start:end]
    print('Context:', ctx[:250])
else:
    print('✗ human_thinking option NOT FOUND!')

# 查找 memory_manager_backend 相关代码
idx = content.find('memory_manager_backend')
if idx >= 0:
    start = max(0, idx - 30)
    end = min(len(content), idx + 300)
    ctx = content[start:end]
    print('\nmemory_manager_backend context:')
    print(ctx[:350])