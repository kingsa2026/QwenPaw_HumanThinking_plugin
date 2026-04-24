content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 检查原始模式是否存在
old_get = 'getAgentRunningConfig:()=>N("/agent/running-config")'
old_put = 'updateAgentRunningConfig:e=>N("/agent/running-config",{method:"PUT",body:JSON.stringify(e)})'

print('=== Pattern check ===')
print(f'old_get exists: {old_get in content}')
print(f'old_put exists: {old_put in content}')

# 如果不存在，检查实际内容
if old_get not in content:
    idx = content.find('getAgentRunningConfig:')
    if idx >= 0:
        end = content.find(',', idx + 50)
        print(f'\nActual getAgentRunningConfig: {content[idx:end][:250]}')