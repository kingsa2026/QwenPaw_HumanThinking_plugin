#!/usr/bin/env python3
"""测试正确的API路径"""

import requests
import json

BASE_URL = "http://192.168.10.132:8088"

def test_with_auth():
    """测试需要认证的API"""
    print("=" * 60)
    print("测试Agent Running Config API")
    print("=" * 60)
    
    # 先获取agents列表
    try:
        resp = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        print(f"\nGET /api/agents: {resp.status_code}")
        if resp.status_code == 200:
            agents = resp.json()
            print(f"Agents: {[a['id'] for a in agents.get('agents', [])]}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试running-config (需要X-Agent-Id header)
    headers_default = {"X-Agent-Id": "default"}
    headers_qa = {"X-Agent-Id": "QwenPaw_QA_Agent_0.2"}
    
    try:
        resp = requests.get(f"{BASE_URL}/api/agent/running-config", headers=headers_default, timeout=10)
        print(f"\nGET /api/agent/running-config (default): {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"  memory_manager_backend: {backend}")
        else:
            print(f"  错误: {resp.text[:200]}")
    except Exception as e:
        print(f"  异常: {e}")
    
    try:
        resp = requests.get(f"{BASE_URL}/api/agent/running-config", headers=headers_qa, timeout=10)
        print(f"\nGET /api/agent/running-config (QA): {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"  memory_manager_backend: {backend}")
        else:
            print(f"  错误: {resp.text[:200]}")
    except Exception as e:
        print(f"  异常: {e}")

if __name__ == "__main__":
    test_with_auth()
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
