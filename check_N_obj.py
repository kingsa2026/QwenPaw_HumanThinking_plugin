content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()

# 查找 N_ 对象的初始化
idx = content.find('N_={')
if idx >= 0:
    end = min(len(content), idx + 300)
    ctx = content[idx:end]
    print('N_ object initialization:')
    print(ctx[:300])
    print()

# 查找 getAgentRunningConfig 附近的完整代码
idx = content.find('getAgentRunningConfig:()=>{')
if idx >= 0:
    end = min(len(content), idx + 400)
    ctx = content[idx:end]
    print('getAgentRunningConfig implementation:')
    print(ctx[:350])