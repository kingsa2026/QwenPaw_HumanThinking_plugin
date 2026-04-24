import re
import shutil

js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'

print(f'Reading: {js_file}')
with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 备份
backup = js_file + '.bak3'
shutil.copy2(js_file, backup)
print(f'Backup: {backup}')

# 修复 getAgentRunningConfig - 把 parsed?.state?.selectedAgent 改成 parsed.selectedAgent
old = 'parsed?.state?.selectedAgent'
new = 'parsed.selectedAgent'
if old in content:
    count = content.count(old)
    content = content.replace(old, new)
    print(f'Fixed {count} occurrences of "{old}" -> "{new}"')
else:
    print(f'Pattern "{old}" not found')

# 验证
if 'parsed.selectedAgent' in content:
    print('✓ Fix verified: parsed.selectedAgent found')
else:
    print('✗ Fix not applied')

# 写入
with open(js_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Written: {js_file}')