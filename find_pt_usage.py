content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 pt 在组件中的使用方式
import re
# 查找 pt((state) => ...) 或类似订阅模式
pattern = r'pt\s*\(\s*\([^)]*\)\s*=>\s*[^,;]+selectedAgent'
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 100)
    print('pt() subscription:')
    print(content[start:end][:200])
    print()

# 查找 ho.subscribe 的所有用法
pattern = r'ho\.subscribe\s*\([^)]+\)'
count = 0
for m in re.finditer(pattern, content):
    start = max(0, m.start() - 50)
    end = min(len(content), m.end() + 100)
    ctx = content[start:end]
    print(f'ho.subscribe #{count+1}:')
    print(ctx[:150])
    print()
    count += 1
    if count >= 3:
        break