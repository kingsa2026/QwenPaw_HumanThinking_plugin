import re

# 原始 JS 代码片段
original = 'getAgentRunningConfig:()=>N("/agent/running-config"),updateAgentRunningConfig:e=>N("/agent/running-config",{method:"PUT",body:JSON.stringify(e)})'

# Step 6 的正则
get_pattern = r'getAgentRunningConfig\s*:\s*\(\s*\)\s*=>\s*N\s*\(\s*["\']\/agent\/running-config["\']\s*\)'

# 查找匹配
get_match = re.search(get_pattern, original)
print('Original:', original[:80], '...')
print()
print('Pattern:', get_pattern)
print()
print('Match:', get_match.group(0) if get_match else 'NO MATCH')
print('Match start:', get_match.start() if get_match else None)
print('Match end:', get_match.end() if get_match else None)

if get_match:
    print()
    print('Before match:', original[:get_match.start()])
    print('Match:', get_match.group(0))
    print('After match:', original[get_match.end():])

    # 替换代码
    new_code = 'getAgentRunningConfig:()=>{const stored=sessionStorage.getItem("qwenpaw-agent-storage");const parsed=stored?JSON.parse(stored):{};const agentId=parsed?.state?.selectedAgent||"default";return N("/agent/running-config",{headers:{"X-Agent-Id":agentId}});}'

    result = original[:get_match.start()] + new_code + original[get_match.end():]
    print()
    print('Result:', result[:150], '...')

    # 检查括号平衡
    print()
    print('Original parens:', original.count('('), original.count(')'))
    print('New code parens:', new_code.count('('), new_code.count(')'))
    print('Result parens:', result.count('('), result.count(')'))