with open("/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets/ui-vendor-2TC525Ld.js", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()
idx = content.find("HumanThinking: Agent")
print("Agent refresh found:", idx >= 0)
idx2 = content.find("human_thinking")
print("human_thinking found:", idx2 >= 0)
