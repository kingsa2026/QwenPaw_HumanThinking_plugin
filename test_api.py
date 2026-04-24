#!/usr/bin/env python3
"""测试API返回的记忆管理器配置"""

import requests
import json

BASE_URL = "http://192.168.10.132:8088"

def test_agents_api():
    """测试获取agents列表"""
    print("=" * 60)
    print("Testing Agents API")
    print("=" * 60)

    try:
        # 先尝试获取agents列表
        resp = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        print(f"\nGET /api/agents")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"Error: {e}")

def test_agent_config_api():
    """测试获取agent配置"""
    print("\n" + "=" * 60)
    print("Testing Agent Config API")
    print("=" * 60)

    agent_ids = ["default", "QwenPaw_QA_Agent_0.2"]

    for agent_id in agent_ids:
        try:
            # 尝试不同的API路径
            endpoints = [
                f"/api/agents/{agent_id}/config",
                f"/api/agent/{agent_id}/config",
                f"/api/workspaces/{agent_id}/config",
            ]

            for endpoint in endpoints:
                resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                print(f"\nGET {endpoint}")
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    data = resp.json()
                    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:800]}")
                    break
        except Exception as e:
            print(f"Error for {agent_id}: {e}")

def test_workspace_api():
    """测试workspace API"""
    print("\n" + "=" * 60)
    print("Testing Workspace API")
    print("=" * 60)

    try:
        resp = requests.get(f"{BASE_URL}/api/workspaces", timeout=10)
        print(f"\nGET /api/workspaces")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:800]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_agents_api()
    test_agent_config_api()
    test_workspace_api()
