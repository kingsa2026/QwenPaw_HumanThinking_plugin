content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 setSelectedAgent 被调用时的处理
idx = content.find('setSelectedAgent')
count = 0
while idx >= 0 and count < 10:
    start = max(0, idx - 100)
    end = min(len(content), idx + 200)
    ctx = content[start:end]
    if '=>' in ctx[:150]:  # 箭头函数
        print(f'Context {count+1}:')
        print(ctx[:300])
        print()
    idx = content.find('setSelectedAgent', idx + 1)
    count += 1