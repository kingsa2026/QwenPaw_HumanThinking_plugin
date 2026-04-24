content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()
idx = content.find('memory_manager_backend"')
if idx >= 0:
    start = max(0, idx - 200)
    end = min(len(content), idx + 300)
    print('Context around memory_manager_backend:')
    print(content[start:end])