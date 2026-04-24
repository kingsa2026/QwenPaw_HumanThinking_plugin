# -*- coding: utf-8 -*-
"""服务器完整测试脚本

测试内容：
1. API端点测试 (10个接口)
2. 前端JS注入验证
3. 插件加载和日志检查
"""

import requests
import sys
import os
import json
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class ServerTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "api_tests": {},
            "js_injection": {},
            "plugin_load": {},
            "errors": []
        }
        
    def log(self, message, level="INFO"):
        """打印日志"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_endpoints(self):
        """测试所有API端点"""
        self.log("=" * 60)
        self.log("开始API端点测试")
        self.log("=" * 60)
        
        endpoints = [
            ("GET", "/plugin/humanthinking/stats", "获取统计信息"),
            ("GET", "/plugin/humanthinking/config", "获取配置"),
            ("POST", "/plugin/humanthinking/config", "更新配置"),
            ("POST", "/plugin/humanthinking/search", "搜索记忆"),
            ("GET", "/plugin/humanthinking/emotion", "获取情感状态"),
            ("GET", "/plugin/humanthinking/sessions", "获取会话列表"),
            ("GET", "/plugin/humanthinking/memories/recent", "获取最近记忆"),
            ("GET", "/plugin/humanthinking/memories/timeline", "获取时间线"),
            ("POST", "/plugin/humanthinking/sessions/bridge", "桥接会话"),
            ("GET", "/plugin/humanthinking/dreams", "获取梦境记录"),
        ]
        
        all_passed = True
        for method, endpoint, description in endpoints:
            url = f"{self.base_url}{endpoint}"
            try:
                self.log(f"测试 {description}...", "TEST")
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json={}, timeout=10)
                
                if response.status_code == 200:
                    self.log(f"  ✓ {endpoint} - 200 OK", "PASS")
                    self.results["api_tests"][endpoint] = {
                        "status": "pass",
                        "code": 200,
                        "response": response.json() if response.text else {}
                    }
                else:
                    self.log(f"  ✗ {endpoint} - {response.status_code}", "FAIL")
                    self.results["api_tests"][endpoint] = {
                        "status": "fail",
                        "code": response.status_code,
                        "response": response.text[:200]
                    }
                    all_passed = False
                    
            except Exception as e:
                self.log(f"  ✗ {endpoint} - Error: {e}", "FAIL")
                self.results["api_tests"][endpoint] = {
                    "status": "error",
                    "error": str(e)
                }
                all_passed = False
                
        return all_passed
        
    def test_js_injection(self):
        """测试前端JS注入"""
        self.log("=" * 60)
        self.log("开始前端JS注入验证")
        self.log("=" * 60)
        
        try:
            # 获取console页面
            response = requests.get(f"{self.base_url}/console/", timeout=10)
            if response.status_code != 200:
                self.log(f"  ✗ 无法获取console页面: {response.status_code}", "FAIL")
                return False
                
            html = response.text
            
            # 查找JS文件引用
            import re
            js_files = re.findall(r'src="([^"]*\.js)"', html)
            self.log(f"  找到 {len(js_files)} 个JS文件")
            
            # 检查每个JS文件
            human_thinking_found = False
            agent_refresh_found = False
            
            for js_file in js_files[:5]:  # 检查前5个
                if js_file.startswith("http"):
                    js_url = js_file
                else:
                    js_url = f"{self.base_url}{js_file}"
                    
                try:
                    js_response = requests.get(js_url, timeout=10)
                    if js_response.status_code == 200:
                        js_content = js_response.text
                        
                        if "human_thinking" in js_content:
                            self.log(f"  ✓ 找到 human_thinking 注入: {js_file}", "PASS")
                            human_thinking_found = True
                            
                        if "HumanThinking: Agent切换自动刷新配置" in js_content:
                            self.log(f"  ✓ 找到 Agent切换自动刷新配置 注入: {js_file}", "PASS")
                            agent_refresh_found = True
                            
                except Exception as e:
                    self.log(f"  警告: 无法获取 {js_file}: {e}", "WARN")
                    
            self.results["js_injection"] = {
                "human_thinking": human_thinking_found,
                "agent_refresh": agent_refresh_found
            }
            
            if human_thinking_found and agent_refresh_found:
                self.log("  ✓ 所有JS注入验证通过", "PASS")
                return True
            else:
                if not human_thinking_found:
                    self.log("  ✗ human_thinking 注入未找到", "FAIL")
                if not agent_refresh_found:
                    self.log("  ✗ Agent切换自动刷新配置 注入未找到", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"  ✗ JS注入测试失败: {e}", "FAIL")
            self.results["js_injection"]["error"] = str(e)
            return False
            
    def test_plugin_load(self):
        """测试插件加载"""
        self.log("=" * 60)
        self.log("开始插件加载检查")
        self.log("=" * 60)
        
        # 检查QwenPaw日志或状态
        try:
            # 尝试访问健康检查端点
            response = requests.get(f"{self.base_url}/health", timeout=5)
            self.log(f"  健康检查状态: {response.status_code}")
            
            # 检查API是否可用
            response = requests.get(f"{self.base_url}/plugin/humanthinking/stats", timeout=5)
            if response.status_code == 200:
                self.log("  ✓ HumanThinking API 可用", "PASS")
                self.results["plugin_load"]["api_available"] = True
            else:
                self.log(f"  ✗ HumanThinking API 不可用: {response.status_code}", "FAIL")
                self.results["plugin_load"]["api_available"] = False
                
        except Exception as e:
            self.log(f"  警告: 无法检查插件状态: {e}", "WARN")
            self.results["plugin_load"]["error"] = str(e)
            
        return True
        
    def generate_report(self):
        """生成测试报告"""
        self.log("=" * 60)
        self.log("测试报告")
        self.log("=" * 60)
        
        # API测试统计
        api_passed = sum(1 for v in self.results["api_tests"].values() if v.get("status") == "pass")
        api_total = len(self.results["api_tests"])
        self.log(f"API测试: {api_passed}/{api_total} 通过")
        
        # JS注入统计
        js_ok = self.results["js_injection"].get("human_thinking", False) and \
                self.results["js_injection"].get("agent_refresh", False)
        self.log(f"JS注入: {'通过' if js_ok else '失败'}")
        
        # 总体结果
        all_ok = api_passed == api_total and js_ok
        self.log("=" * 60)
        if all_ok:
            self.log("✓ 所有测试通过！", "PASS")
        else:
            self.log("✗ 部分测试失败，需要修复", "FAIL")
        self.log("=" * 60)
        
        return all_ok
        
    def run_all_tests(self):
        """运行所有测试"""
        self.log("\n" + "=" * 60)
        self.log("HumanThinking 服务器完整测试")
        self.log(f"目标服务器: {self.base_url}")
        self.log("=" * 60 + "\n")
        
        # 测试API
        api_ok = self.test_api_endpoints()
        
        # 测试JS注入
        js_ok = self.test_js_injection()
        
        # 测试插件加载
        self.test_plugin_load()
        
        # 生成报告
        all_ok = self.generate_report()
        
        # 保存详细结果
        report_file = Path(__file__).parent / "server_test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        self.log(f"\n详细报告已保存到: {report_file}")
        
        return all_ok


if __name__ == "__main__":
    # 获取服务器地址
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = ServerTester(base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
