#!/bin/bash
# 查找 pt() store 的定义
python3 << 'EOF'
content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt = 初始化
idx = content.find('pt=pt(')
if idx >= 0:
    end = min(len(content), idx + 300)
    print('pt initialization:')
    print(content[idx:end][:250])
    print()

# 查找 sessionStorage 相关的 persist 配置
import re
pattern = r'sessionStorage[^;]{0,100}'
for m in re.finditer(pattern, content):
    ctx = m.group(0)[:100]
    if 'qwenpaw' in ctx.lower():
        print(f'sessionStorage context: {ctx}')
EOF