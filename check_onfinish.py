#!/bin/bash
# 查找表单 onFinish 的上下文
python3 << 'EOF'
content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 onFinish 附近的代码
idx = content.find('onFinish')
while idx >= 0 and idx < len(content):
    # 查找包含 updateAgentConfig 的 onFinish 上下文
    end_idx = min(len(content), idx + 500)
    ctx = content[idx:end_idx]
    if 'updateAgentConfig' in ctx or 'D.updateAgentConfig' in ctx:
        print('Found onFinish with updateAgentConfig:')
        print(ctx[:400])
        print()
        break
    idx = content.find('onFinish', idx + 1)
EOF