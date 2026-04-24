#!/usr/bin/env python3
"""
HumanThinking 详细诊断脚本 - 在服务器上运行此脚本查看修补详情
"""

import os
import re
import sys

def find_qwenpaw_console_static_dir():
    """查找 QwenPaw console 静态文件目录"""
    candidates = [
        "/root/.qwenpaw/console",
        os.path.expanduser("~/.qwenpaw/console"),
    ]

    try:
        import qwenpaw
        pkg_dir = os.path.dirname(qwenpaw.__file__)
        console_dir = os.path.join(pkg_dir, "console")
        if os.path.isdir(console_dir) and os.path.isfile(os.path.join(console_dir, "index.html")):
            return console_dir
        dist_dir = os.path.join(console_dir, "dist")
        if os.path.isdir(dist_dir):
            return dist_dir
    except ImportError:
        pass

    for candidate in candidates:
        if os.path.isdir(candidate):
            if os.path.isfile(os.path.join(candidate, "index.html")):
                return candidate
            dist_dir = os.path.join(candidate, "dist")
            if os.path.isdir(dist_dir):
                return dist_dir

    return ""


def diagnose_patch():
    print("=" * 70)
    print("HumanThinking 详细诊断 - JS 修补分析")
    print("=" * 70)

    console_dir = find_qwenpaw_console_static_dir()
    if not console_dir:
        print("ERROR: 无法找到 console 目录")
        return

    print(f"\n[1] Console 目录: {console_dir}")

    # 查找所有 JS 文件
    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js"):
                js_files.append(os.path.join(root, f))

    print(f"\n[2] 找到 {len(js_files)} 个 JS 文件")

    # 查找包含 remelight 的文件
    remelight_files = []
    for js_file in js_files:
        try:
            with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if "remelight" in content.lower():
                remelight_files.append(js_file)
        except Exception as e:
            pass

    print(f"\n[3] 找到 {len(remelight_files)} 个包含 'remelight' 的 JS 文件")

    # 分析每个包含 remelight 的文件
    for js_file in remelight_files:
        print(f"\n{'='*70}")
        print(f"文件: {os.path.basename(js_file)}")
        print(f"完整路径: {js_file}")

        with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        print(f"文件大小: {len(content)} 字符")

        # 查找所有 remelight 出现的位置
        print(f"\n[3.1] 'remelight' 出现位置:")
        for i, match in enumerate(re.finditer(r'.{0,80}remelight.{0,80}', content, re.IGNORECASE)):
            start = match.start()
            end = match.end()
            print(f"  位置 {start}-{end}: ...{match.group(0)}...")

        # 快速检查：是否包含选项对象
        option_match = re.search(r'\{[^}]*value\s*:\s*["\']remelight["\']', content)
        if option_match:
            print(f"\n[3.2] ✓ 找到 remelight 选项对象")
            print(f"  匹配文本: {option_match.group(0)}")
        else:
            print(f"\n[3.2] ✗ 没有找到 remelight 选项对象（只有翻译文本）")
            continue

        # 测试所有模式
        print(f"\n[3.3] 测试正则模式:")

        patterns = [
            ("模式1: 标准紧凑", r'(\{value\s*:\s*"remelight"\s*,\s*label\s*:\s*"ReMeLight"\s*\})'),
            ("模式2: 单引号", r"(\{value\s*:\s*'remelight'\s*,\s*label\s*:\s*'ReMeLight'\s*\})"),
            ("模式3: 带额外字段", r'(\{value\s*:\s*"remelight"[^}]*\})'),
            ("模式4: 最宽松", r'(\{[^}]*value\s*:\s*["\']remelight["\'][^}]*\})'),
        ]

        matched = False
        for name, pattern in patterns:
            match = re.search(pattern, content)
            if match:
                print(f"  ✓ {name}: 匹配成功")
                print(f"    匹配内容: {match.group(0)[:150]}")
                matched = True

                # 测试替换
                new_option = ',{value:"human_thinking",label:"Human Thinking"}'
                result = match.group(0) + new_option
                print(f"    替换结果: {result[:150]}")
            else:
                print(f"  ✗ {name}: 不匹配")

        if not matched:
            print(f"\n[3.4] ✗ 警告: 所有模式都不匹配！")
            print(f"  可能的原因：")
            print(f"  1. JS 文件使用了不同的格式")
            print(f"  2. 需要添加新的正则模式")

            # 查找实际的格式
            print(f"\n[3.5] 分析实际格式:")
            # 找到包含 value: 的 remelight 上下文
            for m in re.finditer(r'value\s*:\s*["\'][^"\']*["\']', content):
                pos = m.start()
                context_start = max(0, pos - 50)
                context_end = min(len(content), pos + 100)
                context = content[context_start:context_end]
                if 'remelight' in context.lower():
                    print(f"  找到相关上下文: ...{context}...")

    print(f"\n{'='*70}")
    print("诊断完成")
    print("=" * 70)


if __name__ == "__main__":
    diagnose_patch()
