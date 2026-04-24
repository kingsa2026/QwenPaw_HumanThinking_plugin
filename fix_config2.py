import json
import os

# Fix default agent
with open("/root/.qwenpaw/workspaces/default/agent.json", "r") as f:
    content = f.read()
    print("Default before:")
    print(content)

with open("/root/.qwenpaw/workspaces/default/agent.json", "r+") as f:
    d = json.load(f)
    d["memory_manager_backend"] = "remelight"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()

with open("/root/.qwenpaw/workspaces/default/agent.json", "r") as f:
    print("Default after:")
    print(f.read())

# Fix QA agent
with open("/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json", "r") as f:
    content = f.read()
    print("QA before:")
    print(content)

with open("/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json", "r+") as f:
    d = json.load(f)
    d["memory_manager_backend"] = "human_thinking"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()

with open("/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json", "r") as f:
    print("QA after:")
    print(f.read())
