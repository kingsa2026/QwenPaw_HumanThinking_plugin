#!/usr/bin/env python3
"""测试新的API路由"""

import requests
import json

BASE_URL = "http://192.168.10.132:8088"

def test_api(endpoint, method='GET', data=None):
    """测试API"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == 'GET':
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=data, timeout=10)
        print(f"{method} {endpoint}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {json.dumps(resp.json(), indent=2)[:300]}")
        else:
            print(f"  Error: {resp.text[:200]}")
        return resp.status_code == 200
    except Exception as e:
        print(f"  Exception: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("测试 HumanThinking API")
    print("=" * 60)
    
    # 测试各个API
    test_api("/api/plugin/humanthinking/stats")
    test_api("/api/plugin/humanthinking/config")
    test_api("/api/plugin/humanthinking/emotion")
    test_api("/api/plugin/humanthinking/sessions")
    test_api("/api/plugin/humanthinking/memories/recent")
    test_api("/api/plugin/humanthinking/memories/timeline")
    test_api("/api/plugin/humanthinking/search", "POST", {"query": "test", "limit": 5})
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
