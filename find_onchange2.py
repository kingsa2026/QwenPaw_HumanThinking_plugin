content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 onChange 回调中的 setSelectedAgent
import re
pattern = r'onChange[^}]+setSelectedAgent'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 100)
    print('onChange with setSelectedAgent:')
    print(content[start:end][:200])
    print()