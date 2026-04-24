content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 persist 的完整配置来理解存储格式
import re

# 查找 persist 函数调用
pattern = r'persist\s*\(\s*[^,]+,\s*\{[^}]*name[^}]*\}'
for m in re.finditer(pattern, content):
    ctx = content[m.start():m.end()+500]
    if 'qwenpaw-agent-storage' in ctx:
        print('Persist config:')
        print(ctx[:600])
        print()
        break

# 查找 pt store 的完整定义
pattern = r'pt=gg\(\)\([^)]+\)\([^)]+\)\s*=>\s*\{[^}]*selectedAgent[^}]*\}'
for m in re.finditer(pattern, content):
    ctx = content[m.start():m.end()+300]
    if 'selectedAgent' in ctx:
        print('pt store:')
        print(ctx[:400])
        print()
        break