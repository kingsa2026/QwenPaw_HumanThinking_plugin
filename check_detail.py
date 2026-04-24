with open("/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()
idx = content.find("human_thinking")
print("File size:", len(content))
print("Position:", idx)
print("Context:", content[idx-100:idx+200])

# Check if the array is properly formed
start = content.rfind("[", idx-200, idx)
end = content.find("]", idx)
print("Array:", content[start:end+1])
