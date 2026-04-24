content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8', errors='ignore').read()
print('human_thinking in file:', 'human_thinking' in content)
print('remelight in file:', 'remelight' in content)
idx = content.find('remelight')
if idx >= 0:
    print('remelight context:', content[max(0,idx-50):idx+100])