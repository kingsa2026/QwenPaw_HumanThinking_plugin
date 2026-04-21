#!/usr/bin/env python3
"""安装 HumanThinking 记忆管理器到 QwenPaw"""

import os
import shutil
from pathlib import Path

def install_human_thinking():
    """安装 HumanThinking 到 QwenPaw"""
    
    # 源目录
    source_dir = Path(__file__).parent.parent  # humThink/HumanThinking/
    
    # 目标目录
    try:
        import qwenpaw
        qwenpaw_root = Path(qwenpaw.__file__).parent.parent.parent  # QwenPaw/
        target_dir = qwenpaw_root / "src" / "qwenpaw" / "agents" / "tools" / "HumanThinkingMemoryManager"
    except ImportError:
        print("错误: 无法找到 QwenPaw 安装路径")
        return False
    
    print(f"源目录: {source_dir}")
    print(f"目标目录: {target_dir}")
    
    # 确保源目录存在
    if not source_dir.exists():
        print(f"错误: 源目录不存在: {source_dir}")
        return False
    
    # 创建目标目录
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # 需要复制的文件/目录
    items_to_copy = [
        "core",
        "search",
        "hooks",
        "utils",
        "__init__.py",
    ]
    
    for item in items_to_copy:
        source_item = source_dir / item
        target_item = target_dir / item
        
        if not source_item.exists():
            print(f"警告: 源项目不存在: {item}")
            continue
        
        if target_item.exists():
            print(f"删除已存在的: {target_item}")
            if target_item.is_dir():
                shutil.rmtree(target_item)
            else:
                target_item.unlink()
        
        if source_item.is_dir():
            print(f"复制目录: {item}")
            shutil.copytree(source_item, target_item)
        else:
            print(f"复制文件: {item}")
            shutil.copy2(source_item, target_item)
    
    print(f"\n✓ HumanThinking 记忆管理器已安装到: {target_dir}")
    return True

if __name__ == "__main__":
    success = install_human_thinking()
    if success:
        print("\n安装成功！现在可以重启 QwenPaw 并选择 Human Thinking 作为记忆管理器后端。")
    else:
        print("\n安装失败！请检查错误信息。")
