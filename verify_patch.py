#!/usr/bin/env python3
js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'
content = open(js_file, 'r', encoding='utf-8', errors='ignore').read()
idx = content.find('human_thinking')
print(f'Position: {idx}')
print(f'Context: ...{content[max(0,idx-100):idx+150]}...')