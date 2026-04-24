content = open('/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js', 'r', encoding='utf-8').read()

if 'value:"human_thinking"' in content:
    print('✓ human_thinking option found!')
else:
    print('✗ human_thinking option NOT FOUND!')

if 'value:"remelight"' in content:
    print('✓ remelight option found')