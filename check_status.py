content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

print('=== JS File Status ===')
print(f'File size: {len(content)}')
print(f'human_thinking: {content.count("human_thinking")}')
print(f'X-Agent-Id: {content.count("X-Agent-Id")}')
print(f'Parentheses: ( = {content.count("(")}, ) = {content.count(")")}')

# 查找 getAgentRunningConfig
idx = content.find('getAgentRunningConfig')
if idx >= 0:
    print('\n=== getAgentRunningConfig ===')
    print(content[idx:idx+300])

# 查找 sessionStorage
ss_count = content.count('sessionStorage.getItem("qwenpaw-agent-storage")')
print(f'\nsessionStorage qwenpaw-agent-storage: {ss_count}')