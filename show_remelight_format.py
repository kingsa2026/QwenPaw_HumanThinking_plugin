#!/usr/bin/env python3
"""
查看服务器上 JS 文件中 remelight 的实际格式
运行: python3 show_remelight_format.py
"""

import os
import re
import sys

def find_qwenpaw_console():
    try:
        import qwenpaw
        return os.path.join(os.path.dirname(qwenpaw.__file__), "console")
    except:
        return ""

def main():
    console_dir = find_qwenpaw_console()
    if not console_dir:
        print("ERROR: Cannot find QwenPaw console directory")
        return

    print(f"Console dir: {console_dir}")

    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and "bak" not in f:
                js_files.append(os.path.join(root, f))

    print(f"Found {len(js_files)} JS files")

    for js_file in js_files:
        try:
            with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if "remelight" not in content.lower():
                continue

            print(f"\n{'='*70}")
            print(f"File: {os.path.basename(js_file)}")
            print(f"Size: {len(content)} chars")

            # 查找所有 remelight 相关上下文
            for m in re.finditer(r'.{0,100}remelight.{0,100}', content, re.IGNORECASE):
                print(f"\nContext: ...{m.group(0)}...")

            # 查找选项对象
            option_match = re.search(r'\{[^}]*value\s*:\s*["\']remelight["\'][^}]*\}', content)
            if option_match:
                print(f"\nOption object found: {option_match.group(0)}")
            else:
                print(f"\nNo option object found (only text references)")

        except Exception as e:
            print(f"Error reading {js_file}: {e}")

if __name__ == "__main__":
    main()
