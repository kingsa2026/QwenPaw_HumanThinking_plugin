#!/usr/bin/env python3
"""全面测试API"""

import requests
import json
import sys

BASE_URL = "http://192.168.10.132:8088"

def test_health():
    """测试服务是否健康"""
    try:
        resp = requests.get(f"{BASE_URL}/api/agents", timeout=10)
        print(f"✓ API服务正常 (状态码: {resp.status_code})")
        return True
    except Exception as e:
        print(f"✗ API服务异常: {e}")
        return False

def test_agent_config():
    """测试获取agent配置"""
    print("\n测试Agent配置API:")
    
    # 测试default agent
    try:
        resp = requests.get(f"{BASE_URL}/api/agents/default/running-config", timeout=10)
        print(f"  default agent: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"    memory_manager_backend: {backend}")
        else:
            print(f"    错误: {resp.text[:200]}")
    except Exception as e:
        print(f"    异常: {e}")
    
    # 测试QA agent
    try:
        resp = requests.get(f"{BASE_URL}/api/agents/QwenPaw_QA_Agent_0.2/running-config", timeout=10)
        print(f"  QA agent: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            backend = data.get("memory_manager_backend", "NOT FOUND")
            print(f"    memory_manager_backend: {backend}")
        else:
            print(f"    错误: {resp.text[:200]}")
    except Exception as e:
        print(f"    异常: {e}")

def test_plugin_apis():
    """测试插件API"""
    print("\n测试插件API:")
    
    endpoints = [
        "/api/plugin/humanthinking/stats",
        "/api/plugin/humanthinking/agents",
    ]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"  {endpoint}: {resp.status_code}")
        except Exception as e:
            print(f"  {endpoint}: 异常 - {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("QwenPaw API 测试")
    print("=" * 60)
    
    if test_health():
        test_agent_config()
        test_plugin_apis()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
