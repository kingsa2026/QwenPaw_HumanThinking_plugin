content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 switchAgent 或 handleSwitch
patterns = ['switchAgent', 'handleSwitch', 'changeAgent', 'onSelectAgent', 'switchTo']
for p in patterns:
    count = content.count(p)
    if count > 0:
        print(f'{p}: {count} occurrences')

# 查找 selectAgent 的处理
idx = content.find('selectAgent')
if idx >= 0:
    start = max(0, idx - 100)
    end = min(len(content), idx + 300)
    print(f'\nselectAgent context: {content[start:end][:350]}')