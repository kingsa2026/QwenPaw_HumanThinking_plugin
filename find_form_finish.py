content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

# 查找表单提交 onFinish 的完整处理
idx = content.find('onFinish')
count = 0
while idx >= 0 and count < 3:
    start = max(0, idx - 200)
    end = min(len(content), idx + 500)
    ctx = content[start:end]
    if 'getAgentRunningConfig' in ctx or 'updateAgentConfig' in ctx:
        print(f'Found onFinish #{count+1}:')
        print(ctx[:600])
        print()
    idx = content.find('onFinish', idx + 1)
    count += 1