content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()
idx = content.find('getAgentRunningConfig:')
if idx >= 0:
    end = content.find(',', idx + 50)
    impl = content[idx:end]
    print('=== getAgentRunningConfig ===')
    print(impl[:350])