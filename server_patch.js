#!/usr/bin/env python3
"""服务器端 JS 修补脚本"""
import re
import shutil
import os

js_file = '/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js'

print(f"Reading: {js_file}")

with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print(f"File size: {len(content)} chars")

# 查找选项数组 - 精确模式
patterns = [
    r'\{value\s*:\s*"remelight"\s*,\s*label\s*:\s*"ReMeLight"\s*\}',
    r"\{value\s*:\s*'remelight'\s*,\s*label\s*:\s*'ReMeLight'\s*\}",
]

for i, p in enumerate(patterns):
    matches = re.findall(p, content)
    print(f"Pattern {i+1}: {p[:60]}... -> {len(matches)} matches")

# 搜索 remelight 选项的上下文
print("\nSearching for remelight context...")
for m in re.finditer(r'.{0,80}remelight.{0,80}', content, re.IGNORECASE):
    ctx = m.group(0)
    if 'value' in ctx.lower() or 'label' in ctx.lower():
        print(f"  Context: ...{ctx}...")

# 查找 ik 数组
print("\nSearching for ik array...")
ik_match = re.search(r'ik\s*=\s*\[([^\]]+)\]', content)
if ik_match:
    print(f"  Found: ik=[{ik_match.group(1)}]")
else:
    print("  Not found")

# 替换: 在 remelight 选项后添加 human_thinking
print("\nPatching...")
old_pattern = '{value:"remelight",label:"ReMeLight"}'
new_pattern = '{value:"remelight",label:"ReMeLight"},{value:"human_thinking",label:"Human Thinking"}'

if old_pattern in content:
    print(f"  Found target pattern: {old_pattern}")

    # 备份
    backup = js_file + ".bak"
    if not os.path.exists(backup):
        shutil.copy2(js_file, backup)
        print(f"  Backup created: {backup}")

    # 替换
    new_content = content.replace(old_pattern, new_pattern)

    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  Patched successfully!")
    print(f"  New pattern: {new_pattern}")

    # 验证
    if 'human_thinking' in new_content:
        print("  ✓ Verification passed: human_thinking found in patched file")
    else:
        print("  ✗ Verification failed: human_thinking NOT found")
else:
    print(f"  Pattern not found: {old_pattern}")
    # 尝试搜索实际存在的模式
    for m in re.finditer(r'\{[^}]*remelight[^}]*\}', content, re.IGNORECASE):
        print(f"  Found similar: {m.group(0)}")