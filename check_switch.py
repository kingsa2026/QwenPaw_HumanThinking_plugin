import re

content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 selectedAgent 变化时的处理
print('=== selectedAgent change handling ===')
for m in re.finditer(r'selectedAgent[^;]{0,300}', content):
    ctx = m.group(0)[:250]
    if 'setFieldsValue' in ctx or 'useEffect' in ctx or 'y()' in ctx:
        print(f'  ...{ctx}...')
        print()

# 查找 Agent 切换时的 effect
print('\n=== Agent switch effects ===')
effect_pattern = r'useEffect\([^)]*\(\)=>[^}]*selectedAgent[^}]*\}'
for m in re.finditer(effect_pattern, content):
    print(f'  ...{m.group(0)[:200]}...')
    print()