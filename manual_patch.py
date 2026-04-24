import re
import shutil

js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'

print(f'Reading: {js_file}')
with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print(f'File size: {len(content)} chars')

# 备份
backup = js_file + '.bak2'
shutil.copy2(js_file, backup)
print(f'Backup created: {backup}')

# Step 1: 添加 human_thinking 选项
old_opt = '{value:"remelight",label:"ReMeLight"}'
new_opt = '{value:"remelight",label:"ReMeLight"},{value:"human_thinking",label:"Human Thinking"}'
if old_opt in content:
    content = content.replace(old_opt, new_opt)
    print('Step 1: Added human_thinking option')
else:
    print('Step 1: Option pattern not found')

# Step 2: 修补 getAgentRunningConfig
old_get = 'getAgentRunningConfig:()=>N("/agent/running-config")'
new_get = 'getAgentRunningConfig:()=>{const stored=sessionStorage.getItem("qwenpaw-agent-storage");const parsed=stored?JSON.parse(stored):{};const agentId=parsed?.state?.selectedAgent||"default";return N("/agent/running-config",{headers:{"X-Agent-Id":agentId}});}'
if old_get in content:
    content = content.replace(old_get, new_get)
    print('Step 2: Patched getAgentRunningConfig')
else:
    print('Step 2: getAgentRunningConfig pattern not found')

# Step 3: 修补 updateAgentRunningConfig
old_put = 'updateAgentRunningConfig:e=>N("/agent/running-config",{method:"PUT",body:JSON.stringify(e)})'
new_put = 'updateAgentRunningConfig:e=>{const stored=sessionStorage.getItem("qwenpaw-agent-storage");const parsed=stored?JSON.parse(stored):{};const agentId=parsed?.state?.selectedAgent||"default";return N("/agent/running-config",{method:"PUT",body:JSON.stringify(e),headers:{"X-Agent-Id":agentId}});}'
if old_put in content:
    content = content.replace(old_put, new_put)
    print('Step 3: Patched updateAgentRunningConfig')
else:
    print('Step 3: updateAgentRunningConfig pattern not found')

# 验证
print(f'\nVerification:')
print(f'human_thinking: {content.count("human_thinking")}')
print(f'X-Agent-Id: {content.count("X-Agent-Id")}')
print(f'Parentheses balanced: {content.count("(") == content.count(")")}')

# 写入
with open(js_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'\nWritten to: {js_file}')