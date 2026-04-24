import json

# Fix default agent
with open("/root/.qwenpaw/workspaces/default/agent.json", "r+") as f:
    d = json.load(f)
    d["memory_manager_backend"] = "remelight"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()
print("default updated to remelight")

# Fix QA agent
with open("/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json", "r+") as f:
    d = json.load(f)
    d["memory_manager_backend"] = "human_thinking"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()
print("QA updated to human_thinking")
