#!/usr/bin/env python3
"""测试正确的API路径 - 带调试信息"""

import requests
import json

BASE_URL = "http://192.168.10.132:8088"

def test_with_auth():
    """测试需要认证的API"""
    print("=" * 60)
    print("测试Agent Running Config API (带调试)")
    print("=" * 60)
    
    # 测试default agent
    headers_default = {"X-Agent-Id": "default"}
    try:
        resp = requests.get(f"{BASE_URL}/api/agent/running-config", headers=headers_default, timeout=10)
        print(f"\nGET /api/agent/running-config (X-Agent-Id: default)")
        print(f"Status: {resp.status_code}")
        print(f"Response Headers: {dict(resp.headers)}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"memory_manager_backend: {backend}")
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # 测试QA agent
    headers_qa = {"X-Agent-Id": "QwenPaw_QA_Agent_0.2"}
    try:
        resp = requests.get(f"{BASE_URL}/api/agent/running-config", headers=headers_qa, timeout=10)
        print(f"\nGET /api/agent/running-config (X-Agent-Id: QwenPaw_QA_Agent_0.2)")
        print(f"Status: {resp.status_code}")
        print(f"Response Headers: {dict(resp.headers)}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"memory_manager_backend: {backend}")
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"Error: {resp.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_with_auth()
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
