with open("/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/index-gW3b32wu.js", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

print("File size:", len(content))
idx = content.find("HumanThinking: Agent")
print("Agent refresh code found:", idx >= 0)
idx2 = content.find("human_thinking")
print("human_thinking found:", idx2 >= 0)
