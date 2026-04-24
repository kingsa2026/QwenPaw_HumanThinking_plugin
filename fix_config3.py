import json

# Fix default agent - 修改 running 对象内的 memory_manager_backend
with open("/root/.qwenpaw/workspaces/default/agent.json", "r+") as f:
    d = json.load(f)
    # 修改 running 配置
    if "running" in d:
        d["running"]["memory_manager_backend"] = "remelight"
    # 同时修改根级别
    d["memory_manager_backend"] = "remelight"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()
print("default updated")

# Fix QA agent - 修改 running 对象内的 memory_manager_backend
with open("/root/.qwenpaw/workspaces/QwenPaw_QA_Agent_0.2/agent.json", "r+") as f:
    d = json.load(f)
    # 修改 running 配置
    if "running" in d:
        d["running"]["memory_manager_backend"] = "human_thinking"
    # 同时修改根级别
    d["memory_manager_backend"] = "human_thinking"
    f.seek(0)
    json.dump(d, f, indent=2)
    f.truncate()
print("QA updated")
