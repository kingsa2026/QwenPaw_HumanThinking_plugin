import os

js_path = "/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js"

with open(js_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Check human_thinking
idx = content.find("human_thinking")
print("=" * 60)
print("JS File Check")
print("=" * 60)
print(f"File: {js_path}")
print(f"File size: {len(content)} chars")
print(f"human_thinking found at: {idx}")

if idx >= 0:
    print(f"Context (100 before, 200 after):")
    print(content[idx-100:idx+200])
else:
    print("ERROR: human_thinking NOT FOUND!")

# Check for syntax errors - count brackets near injection
print("\n" + "=" * 60)
print("Syntax Check")
print("=" * 60)

# Find the array context
array_start = content.rfind("[", 0, idx)
array_end = content.find("]", idx)
if array_start >= 0 and array_end >= 0:
    array_content = content[array_start:array_end+1]
    print(f"Array content: {array_content}")
    
    # Count braces and brackets
    open_braces = array_content.count("{")
    close_braces = array_content.count("}")
    open_brackets = array_content.count("[")
    close_brackets = array_content.count("]")
    
    print(f"Open braces: {open_braces}, Close braces: {close_braces}")
    print(f"Open brackets: {open_brackets}, Close brackets: {close_brackets}")
    
    if open_braces == close_braces and open_brackets == close_brackets:
        print("Syntax: OK")
    else:
        print("Syntax: ERROR - Mismatched brackets!")
else:
    print("Could not find array context")

# Check remelight still exists
idx2 = content.find("remelight")
print(f"\nremelight found at: {idx2}")
if idx2 < 0:
    print("ERROR: remelight NOT FOUND!")
