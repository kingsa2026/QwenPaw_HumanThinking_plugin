#!/usr/bin/env python3
"""
HumanThinking 诊断脚本 - 检查 QwenPaw 安装状态
在服务器上运行此脚本诊断问题
"""

import os
import re
import sys

def find_qwenpaw_console_static_dir():
    """查找 QwenPaw console 静态文件目录"""
    candidates = [
        # QwenPaw 包目录
        os.path.join(os.path.dirname(__file__), "qwenpaw", "console"),
        # 虚拟环境中的 QwenPaw
        os.path.join(sys.prefix, "lib", "python3.12", "site-packages", "qwenpaw", "console"),
    ]

    for candidate in candidates:
        if os.path.isdir(candidate):
            # 检查是否包含 index.html
            if os.path.isfile(os.path.join(candidate, "index.html")):
                return candidate
            # 也检查 dist 目录
            if os.path.isdir(os.path.join(candidate, "dist")):
                return os.path.join(candidate, "dist")

    # 尝试通过 qwenpaw 包定位
    try:
        import qwenpaw
        pkg_dir = os.path.dirname(qwenpaw.__file__)
        console_dir = os.path.join(pkg_dir, "console")
        if os.path.isdir(console_dir):
            dist_dir = os.path.join(console_dir, "dist")
            if os.path.isdir(dist_dir):
                return dist_dir
            return console_dir
    except ImportError:
        pass

    return ""


def diagnose():
    print("=" * 60)
    print("HumanThinking 诊断脚本")
    print("=" * 60)

    # 1. 检查 QwenPaw 版本
    print("\n[1] 检查 QwenPaw 版本...")
    try:
        import qwenpaw
        print(f"    QwenPaw 版本: {qwenpaw.__version__}")
        print(f"    QwenPaw 路径: {os.path.dirname(qwenpaw.__file__)}")
    except ImportError as e:
        print(f"    ERROR: 无法导入 qwenpaw - {e}")
        return

    # 2. 查找 console 目录
    print("\n[2] 查找 console 目录...")
    console_dir = find_qwenpaw_console_static_dir()
    if console_dir:
        print(f"    找到 console 目录: {console_dir}")
        if os.path.isdir(console_dir):
            files = os.listdir(console_dir)
            print(f"    目录内容 ({len(files)} 项):")
            for f in files[:10]:
                print(f"      - {f}")
            if len(files) > 10:
                print(f"      ... 还有 {len(files) - 10} 项")
    else:
        print("    ERROR: 无法找到 console 目录")

    # 3. 搜索 JS 文件中的 remelight 模式
    print("\n[3] 搜索 JS 文件中的 remelight 模式...")
    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js"):
                js_files.append(os.path.join(root, f))

    print(f"    找到 {len(js_files)} 个 JS 文件")

    for js_file in js_files[:5]:  # 只检查前5个
        try:
            with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 搜索 remelight 模式
            remelight_match = re.search(r'\{[^}]*value\s*:\s*["\']remelight["\'][^}]*\}', content)
            if remelight_match:
                print(f"\n    找到匹配在: {os.path.basename(js_file)}")
                print(f"    匹配内容: {remelight_match.group(0)[:100]}")

                # 显示上下文
                start = max(0, remelight_match.start() - 50)
                end = min(len(content), remelight_match.end() + 50)
                print(f"    上下文: ...{content[start:end]}...")
        except Exception as e:
            print(f"    读取文件失败 {js_file}: {e}")

    # 4. 检查 HumanThinkingMemoryManager 目录
    print("\n[4] 检查 HumanThinkingMemoryManager 目录...")
    tools_dir = os.path.join(os.path.dirname(qwenpaw.__file__), "agents", "tools")
    ht_dir = os.path.join(tools_dir, "HumanThinkingMemoryManager")
    if os.path.isdir(ht_dir):
        print(f"    找到 HumanThinkingMemoryManager: {ht_dir}")
        files = os.listdir(ht_dir)
        for f in files:
            print(f"      - {f}")
    else:
        print(f"    ERROR: HumanThinkingMemoryManager 不存在")
        print(f"    预期路径: {ht_dir}")

    # 5. 检查 backend_mappings 或 ReactAgentCard
    print("\n[5] 检查 Agent Config 组件...")
    components_dir = os.path.join(console_dir, "pages", "Agent", "Config", "components")
    if os.path.isdir(components_dir):
        print(f"    找到 components 目录: {components_dir}")
        files = os.listdir(components_dir)
        for f in files:
            print(f"      - {f}")
    else:
        print(f"    components 目录不存在 (这是正常的，v1.1.3.post1 pip 包没有源码)")

    # 6. 检查 localStorage key
    print("\n[6] 建议检查的 localStorage keys:")
    print("    - humanthinking_config (全局配置)")
    print("    - humanthinking_config_{agent_id} (Agent 级别配置)")
    print("    - qwenpaw_selected_agent (当前选中的 Agent)")

    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    diagnose()
