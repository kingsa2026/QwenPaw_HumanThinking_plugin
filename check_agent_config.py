#!/usr/bin/env python3
"""诊断脚本：检查agent-config页面切换agent时的行为"""

import json
import os
import glob

QWENPAW_ROOT = "/root/.qwenpaw"

def check_agent_configs():
    """检查所有agent的配置文件"""
    workspaces_dir = os.path.join(QWENPAW_ROOT, "workspaces")
    if not os.path.isdir(workspaces_dir):
        print(f"Workspaces directory not found: {workspaces_dir}")
        return

    print("=" * 60)
    print("Agent Configuration Files")
    print("=" * 60)

    for agent_dir in sorted(glob.glob(os.path.join(workspaces_dir, "*"))):
        if not os.path.isdir(agent_dir):
            continue

        agent_id = os.path.basename(agent_dir)
        agent_json = os.path.join(agent_dir, "agent.json")

        if not os.path.isfile(agent_json):
            print(f"\nAgent: {agent_id}")
            print(f"  agent.json: NOT FOUND")
            continue

        try:
            with open(agent_json, "r", encoding="utf-8") as f:
                config = json.load(f)

            memory_backend = config.get("memory_manager_backend", "NOT SET")
            agent_name = config.get("name", "Unknown")

            print(f"\nAgent: {agent_id}")
            print(f"  Name: {agent_name}")
            print(f"  Memory Backend: {memory_backend}")

        except Exception as e:
            print(f"\nAgent: {agent_id}")
            print(f"  Error reading config: {e}")

def check_patched_js():
    """检查前端JS文件是否包含human_thinking"""
    console_dir = os.path.join(QWENPAW_ROOT, "venv", "lib", "python3.12", "site-packages", "qwenpaw", "console")

    print("\n" + "=" * 60)
    print("Patched JS Files")
    print("=" * 60)

    found = False
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".bak"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as ff:
                        content = ff.read()
                    if "human_thinking" in content:
                        print(f"\n✓ {f}")
                        # 找到human_thinking的位置并显示上下文
                        idx = content.find("human_thinking")
                        start = max(0, idx - 100)
                        end = min(len(content), idx + 200)
                        print(f"  Context: ...{content[start:end]}...")
                        found = True
                except:
                    pass

    if not found:
        print("\n✗ No patched JS files found!")

def check_backend_config():
    """检查后端配置是否包含human_thinking"""
    config_file = os.path.join(QWENPAW_ROOT, "venv", "lib", "python3.12", "site-packages", "qwenpaw", "config", "config.py")

    print("\n" + "=" * 60)
    print("Backend Config")
    print("=" * 60)

    if not os.path.isfile(config_file):
        print(f"\n✗ Config file not found: {config_file}")
        return

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "human_thinking" in content:
            print("\n✓ Backend config contains human_thinking")
            # 找到memory_manager_backend的位置
            idx = content.find("memory_manager_backend")
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(content), idx + 300)
                print(f"  Context: {content[start:end]}")
        else:
            print("\n✗ Backend config does NOT contain human_thinking")
    except Exception as e:
        print(f"\n✗ Error reading config: {e}")

def check_workspace():
    """检查workspace.py是否支持human_thinking"""
    workspace_file = os.path.join(QWENPAW_ROOT, "venv", "lib", "python3.12", "site-packages", "qwenpaw", "app", "workspace", "workspace.py")

    print("\n" + "=" * 60)
    print("Workspace.py")
    print("=" * 60)

    if not os.path.isfile(workspace_file):
        print(f"\n✗ Workspace file not found: {workspace_file}")
        return

    try:
        with open(workspace_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "human_thinking" in content and "HumanThinkingMemoryManager" in content:
            print("\n✓ workspace.py supports human_thinking")
        else:
            print("\n✗ workspace.py does NOT support human_thinking")
    except Exception as e:
        print(f"\n✗ Error reading workspace: {e}")

if __name__ == "__main__":
    check_agent_configs()
    check_patched_js()
    check_backend_config()
    check_workspace()
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)
