content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 QwenPaw 全局对象
import re
patterns = [
    r'QwenPaw\.register',
    r'QwenPaw\.on',
    r'window\.QwenPaw',
    r'registerRoutes',
    r'getApiToken',
    r'getApiUrl'
]
for p in patterns:
    if p in content:
        print(f'Found: {p}')
        idx = content.find(p)
        start = max(0, idx - 50)
        end = min(len(content), idx + 150)
        print(content[start:end][:200])
        print()