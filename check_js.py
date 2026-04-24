with open("/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

idx = content.find("human_thinking")
print("Found at", idx)
if idx >= 0:
    print(content[idx-50:idx+100])
else:
    print("NOT FOUND")

idx2 = content.find("remelight")
print("\nremelight Found at", idx2)
if idx2 >= 0:
    print(content[idx2-50:idx2+100])
