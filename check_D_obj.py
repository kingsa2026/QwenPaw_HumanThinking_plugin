content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 D 对象的初始化
idx = content.find('D={')
if idx >= 0:
    end = min(len(content), idx + 500)
    ctx = content[idx:end]
    print('D object initialization:')
    print(ctx[:400])
    print()

# 检查 pt() 和 D 的关系
idx = content.find('D=D||{')
if idx >= 0:
    end = min(len(content), idx + 200)
    ctx = content[idx:end]
    print('D = D || {...} context:')
    print(ctx[:200])