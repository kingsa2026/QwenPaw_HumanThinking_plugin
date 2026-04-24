content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 subscribe 或事件发布相关代码
patterns = ['subscribe', 'emit', 'on(', 'addEventListener', 'setSelectedAgent']
for p in patterns:
    count = content.count(p)
    if count > 0:
        print(f'{p}: {count} occurrences')

# 查找 setSelectedAgent 附近的订阅代码
idx = content.find('setSelectedAgent')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 300)
    ctx = content[start:end]
    print('\nsetSelectedAgent context:')
    print(ctx[:400])