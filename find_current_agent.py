content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 搜索"当前智能体"
if '当前智能体' in content:
    idx = content.find('当前智能体')
    start = max(0, idx - 100)
    end = min(len(content), idx + 200)
    print('Found "当前智能体":')
    print(content[start:end])
else:
    print('"当前智能体" not found')

# 也搜索英文 "currentAgent" 或类似
if 'currentAgent' in content:
    print('\nFound "currentAgent"')
if 'switchAgent' in content:
    print('\nFound "switchAgent"')
if 'agentSwitch' in content:
    print('\nFound "agentSwitch"')