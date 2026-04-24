import re

# 实际的 JS 代码
js_code = 'getAgentRunningConfig:()=>N("/agent/running-config"),updateAgentRunningConfig:e=>N("/agent/running-config",{method:"PUT",body:JSON.stringify(e)})'

# Step 6 中的正则
get_pattern = r'getAgentRunningConfig\s*:\s*\(\s*\)\s*=>\s*N\s*\(\s*["\']\/agent\/running-config["\']\s*\)'
put_pattern = r'updateAgentRunningConfig\s*:\s*\w+\s*=>\s*N\s*\(\s*["\']\/agent\/running-config["\']\s*,\s*\{[^}]*method\s*:\s*["\']PUT["\'][^}]*\}'

print('Testing get_pattern:', get_pattern)
get_match = re.search(get_pattern, js_code)
print('get_match:', get_match.group(0) if get_match else 'NO MATCH')

print('\nTesting put_pattern:', put_pattern[:60], '...')
put_match = re.search(put_pattern, js_code)
print('put_match:', put_match.group(0)[:80] if put_match else 'NO MATCH')

# 测试替换代码
new_code = 'getAgentRunningConfig:()=>{const stored=sessionStorage.getItem("qwenpaw-agent-storage");const parsed=stored?JSON.parse(stored):{};const agentId=parsed?.state?.selectedAgent||"default";return N("/agent/running-config",{headers:{"X-Agent-Id":agentId}});}'

if get_match:
    result = js_code[:get_match.start()] + new_code + js_code[get_match.end():]
    print('\nReplaced getAgentRunningConfig:')
    print(result[:200], '...')