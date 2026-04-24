# -*- coding: utf-8 -*-
"""生产环境 UI 修补器 - 直接修改打包后的前端 JS 文件

在 QwenPaw 生产部署环境中，前端已编译为打包的 JS 文件。
本脚本通过正则匹配和替换，直接修改打包后的 JS 文件，
将 HumanThinking 添加到记忆管理器下拉选项中。
"""

import logging
import os
import re
import shutil

# Use "qwenpaw" namespace so logs are captured by QwenPaw's logging system
logger = logging.getLogger("qwenpaw.humanthinking.patcher")


def find_qwenpaw_console_static_dir(qwenpaw_root: str) -> str:
    """查找 QwenPaw 打包后的 console 静态文件目录"""
    # 方法1: 通过 Python 包查找
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
        console_dir = os.path.join(qwenpaw_pkg_dir, "console")
        if os.path.isdir(console_dir) and os.path.isfile(os.path.join(console_dir, "index.html")):
            return console_dir
    except (ImportError, AttributeError):
        pass

    # 方法2: 常见路径
    candidates = [
        os.path.join(qwenpaw_root, "console"),
        os.path.join(qwenpaw_root, "dist", "console"),
        os.path.expanduser("~/.qwenpaw/console"),
        "/root/.qwenpaw/console",
    ]

    for candidate in candidates:
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "index.html")):
            return candidate

    logger.debug("No console static directory found")
    return ""


def _make_backup(filepath: str) -> bool:
    """创建备份文件"""
    backup_path = filepath + ".humanthinking.bak"
    if os.path.exists(backup_path):
        return False
    shutil.copy2(filepath, backup_path)
    logger.debug(f"Backed up: {filepath}")
    return True


def _restore_backup(filepath: str) -> bool:
    """从备份恢复文件"""
    backup_path = filepath + ".humanthinking.bak"
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filepath)
        os.remove(backup_path)
        logger.info(f"Restored: {filepath}")
        return True
    return False


def _patch_js_files_for_human_thinking(qwenpaw_root: str) -> list:
    """
    修补打包后的 JS 文件，添加 human_thinking 选项

    v1.1.3.post1 pip 包中没有 TypeScript 源码，只有打包后的 JS 文件。
    这个函数直接修补 JS 文件。

    Returns:
        list: 成功修补的文件列表
    """
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        logger.warning("无法找到 console 目录")
        return []

    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))

    logger.info(f"扫描 {len(js_files)} 个 JS 文件...")

    patched_files = []
    for js_file in js_files:
        if patch_js_file(js_file):
            patched_files.append(os.path.basename(js_file))

    if patched_files:
        logger.info(f"成功修补 {len(patched_files)} 个 JS 文件: {', '.join(patched_files)}")
    else:
        logger.warning("没有找到需要修补的 JS 文件")

    return patched_files


def patch_js_file(filepath: str) -> bool:
    """
    修改打包后的 JS 文件，添加 HumanThinking 选项

    匹配多种可能的压缩格式：
    - {value:"remelight",label:"ReMeLight"}
    - {value:"remelight",label:i18n.t("...")}
    - [{value:"remelight",label:"ReMeLight"}]
    """
    if not os.path.isfile(filepath):
        logger.debug(f"File not found: {filepath}")
        return False

    try:
        logger.debug(f"Reading file: {os.path.basename(filepath)}")
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        logger.debug(f"File size: {len(content)} characters")

        if "human_thinking" in content:
            logger.debug(f"Already patched: {filepath}")
            return True

        # 检查是否包含 remelight 相关代码
        if "remelight" not in content.lower():
            logger.debug(f"No remelight reference in: {os.path.basename(filepath)}")
            return False

        logger.info(f"Found remelight reference in: {os.path.basename(filepath)}")

        # 快速检查：是否包含 remelight 选项对象语法
        # 必须是 {value:"remelight"...} 格式，而不是翻译文本中的 remelight
        # 使用更严格的检查：必须同时包含 value: 和 label: 字段
        remelight_option_match = re.search(r'\{\s*[^}]*?\bvalue\s*:\s*["\']remelight["\'][^}]*?\blabel\s*:', content)
        if not remelight_option_match:
            logger.info(f"  Skipping: no remelight option object (only i18n text)")
            logger.info(f"  Found 'remelight' but not as option object. Searching for context...")
            # 查找 remelight 出现的位置
            for match in re.finditer(r'.{0,50}remelight.{0,50}', content, re.IGNORECASE):
                logger.info(f"    Context: ...{match.group(0)}...")
            return False

        _make_backup(filepath)

        # 详细调试：查找 remelight 的上下文
        remelight_idx = content.lower().find("remelight")
        if remelight_idx >= 0:
            context_start = max(0, remelight_idx - 100)
            context_end = min(len(content), remelight_idx + 200)
            context = content[context_start:context_end]
            logger.info(f"  Context around 'remelight': ...{context}...")

        # 替换模式: 在 remelight 选项后添加 human_thinking
        # 关键：必须匹配选项对象（包含 value: 字段），排除翻译文本
        # 实际观察到的模式: ik=[{value:"remelight",label:"ReMeLight"},{value:"human_thinking",...}]

        patterns_to_try = [
            # 模式1: 标准紧凑格式 {value:"remelight",label:"ReMeLight"}
            r'(\{value\s*:\s*"remelight"\s*,\s*label\s*:\s*"ReMeLight"\s*\})',
            # 模式2: 单引号格式 {value:'remelight',label:'ReMeLight'}
            r"(\{value\s*:\s*'remelight'\s*,\s*label\s*:\s*'ReMeLight'\s*\})",
            # 模式3: 带额外字段的格式 {value:"remelight",label:"ReMeLight",...}（末尾可能有?号）
            r'(\{value\s*:\s*"remelight"[^}]*(?:\??)\})',
        ]

        match = None
        matched_pattern = None
        for i, pattern in enumerate(patterns_to_try, 1):
            match = re.search(pattern, content)
            if match:
                matched_pattern = i
                logger.info(f"  ✓ Pattern {i} matched: {pattern}")
                logger.info(f"  ✓ Matched text: {match.group(0)}")
                break
            else:
                logger.info(f"  ✗ Pattern {i} did not match: {pattern}")

        if not match:
            logger.warning(f"✗ No remelight option object found in {os.path.basename(filepath)}")
            logger.info(f"  Tried {len(patterns_to_try)} patterns but none matched")
            return False
        
        matched_pattern_idx = matched_pattern - 1  # 转换为 0-based 索引
        matched_pattern_str = patterns_to_try[matched_pattern_idx]
        
        def replacer(match):
            original = match.group(1)
            # 注入 HumanThinking 选项（注意：不包含方括号，直接追加到数组元素中）
            new_option = ',{value:"human_thinking",label:"Human Thinking"}'
            logger.info(f"  Original option: {original}")
            logger.info(f"  Injecting: {new_option}")
            result = original + new_option
            logger.info(f"  Result: {result}")
            return result
        
        new_content = re.sub(matched_pattern_str, replacer, content, count=1)
        
        if new_content != content:
            # 验证注入后的内容
            if "human_thinking" not in new_content:
                logger.error(f"✗ human_thinking not found in patched content!")
                return False
            
            # 查找注入位置的上下文
            ht_idx = new_content.find("human_thinking")
            ht_context_start = max(0, ht_idx - 200)
            ht_context_end = min(len(new_content), ht_idx + 300)
            ht_context = new_content[ht_context_start:ht_context_end]
            
            logger.info(f"✓ Successfully patched JS file: {os.path.basename(filepath)}")
            logger.info(f"  HumanThinking option location: position {ht_idx}")
            logger.info(f"  Context around injection point (200 chars before, 300 chars after):")
            logger.info(f"    {ht_context}")
            
            # 验证注入的内容是否包含完整的对象结构
            if 'value:"human_thinking"' in new_content or "value:'human_thinking'" in new_content:
                logger.info(f"  ✓ HumanThinking option has correct value field")
            else:
                logger.warning(f"  ✗ HumanThinking option value field may be incorrect")
            
            if 'label:"Human Thinking"' in new_content or "label:'Human Thinking'" in new_content:
                logger.info(f"  ✓ HumanThinking option has correct label field")
            else:
                logger.warning(f"  ✗ HumanThinking option label field may be incorrect")
            
            # 检查是否破坏了原有的数组结构（查找附近是否有方括号）
            nearby_content = new_content[max(0, ht_idx-500):ht_idx+500]
            has_opening_bracket = '[' in nearby_content
            has_closing_bracket = ']' in nearby_content
            logger.info(f"  Array structure check (within 500 chars): opening bracket [{'found' if has_opening_bracket else 'NOT found'}], closing bracket [{'found' if has_closing_bracket else 'NOT found'}]")
            
            # 验证 JS 语法：检查注入点附近是否有明显的语法错误
            # 检查是否有连续的逗号、缺少逗号等
            if ',,' in ht_context:
                logger.warning(f"  ✗ Warning: consecutive commas detected (possible syntax error)")
            if '},' not in ht_context and '],' not in ht_context:
                logger.debug(f"  Note: no object separator found near injection point")
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info(f"  ✓ File written successfully to: {filepath}")
            return True

        logger.warning(f"Pattern did not match in {os.path.basename(filepath)}")
        return False

    except Exception as e:
        logger.error(f"Failed to patch {filepath}: {e}", exc_info=True)
        return False


def patch_agent_config_refresh(qwenpaw_root: str) -> dict:
    """
    修补前端JS，添加agent切换时自动刷新配置的功能
    
    问题：原生UI的useAgentConfig hook在切换agent时不会重新加载配置，
    因为fetchConfig的依赖数组只有[form, t]，不包含selectedAgent。
    
    解决方案：注入一个全局的agent切换监听器，当检测到agent变化时，
    自动调用fetchConfig或刷新页面。
    """
    results = {"success": False, "patched": [], "errors": []}
    
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        results["errors"].append("无法找到 console 目录")
        return results
    
    # 查找所有JS文件
    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))
    
    logger.info(f"[AgentRefresh] Scanning {len(js_files)} JS files for agent config refresh patch...")
    
    # 要注入的代码：监听sessionStorage变化，当agent切换时刷新配置
    refresh_code = '''
// HumanThinking: Agent切换自动刷新配置
(function(){
    var lastAgent = sessionStorage.getItem("qwenpaw-agent-storage") ? JSON.parse(sessionStorage.getItem("qwenpaw-agent-storage")).state?.selectedAgent : null;
    var checkInterval = setInterval(function(){
        try {
            var storage = sessionStorage.getItem("qwenpaw-agent-storage");
            if (!storage) return;
            var data = JSON.parse(storage);
            var currentAgent = data.state?.selectedAgent;
            if (currentAgent && currentAgent !== lastAgent) {
                lastAgent = currentAgent;
                console.log("[HumanThinking] Agent switched to:", currentAgent, "- Reloading config...");
                // 方法1：尝试调用全局fetchConfig（如果存在）
                if (window.__agentConfigFetch) {
                    window.__agentConfigFetch();
                } else {
                    // 方法2：刷新页面（兜底方案）
                    window.location.reload();
                }
            }
        } catch(e) {}
    }, 500);
})();
'''
    
    # 找到最大的JS文件（通常是主chunk）
    largest_file = None
    largest_size = 0
    
    for js_file in js_files:
        try:
            size = os.path.getsize(js_file)
            if size > largest_size:
                largest_size = size
                largest_file = js_file
        except:
            pass
    
    if largest_file and largest_size > 100000:  # 主chunk通常大于100KB
        try:
            with open(largest_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # 检查是否已经注入
            if "HumanThinking: Agent切换自动刷新配置" in content:
                logger.debug(f"[AgentRefresh] Already patched: {os.path.basename(largest_file)}")
                results["success"] = True
                return results
            
            _make_backup(largest_file)
            
            # 在文件末尾注入代码
            new_content = content + "\n" + refresh_code
            
            with open(largest_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            results["patched"].append(os.path.basename(largest_file))
            logger.info(f"[AgentRefresh] ✓ Patched largest JS file: {os.path.basename(largest_file)} ({largest_size} bytes)")
        except Exception as e:
            results["errors"].append(f"Failed to patch {largest_file}: {e}")
    else:
        logger.warning(f"[AgentRefresh] No suitable JS file found (largest: {largest_size} bytes)")
        results["errors"].append("No suitable JS file found for patching")
    
    if results["patched"]:
        results["success"] = True
        logger.info(f"[AgentRefresh] Successfully patched {len(results['patched'])} files")
    else:
        logger.warning("[AgentRefresh] No files were patched")
    
    return results


def install_human_thinking_to_qwenpaw(qwenpaw_root: str, plugin_dir: str = None) -> dict:
    """安装 HumanThinkingMemoryManager 到 QwenPaw 的 agents/tools 目录
    
    这是关键步骤——必须让 HumanThinkingMemoryManager 可以被正确导入
    
    Args:
        qwenpaw_root: QwenPaw 根目录
        plugin_dir: 插件目录路径（如果为 None，则从 qwenpaw_root 推导）
    """
    results = {"success": False, "installed": False, "errors": [], "details": {}}
    
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
    except ImportError:
        results["errors"].append("无法导入 qwenpaw 包")
        return results
    
    target_dir = os.path.join(qwenpaw_pkg_dir, "agents", "tools", "HumanThinkingMemoryManager")
    logger.info(f"Target installation directory: {target_dir}")
    
    # 确定插件目录
    if plugin_dir is None:
        # 先尝试常见路径
        possible_dirs = [
            os.path.join(qwenpaw_root, "plugins", "HumanThinking"),  # /root/.qwenpaw/plugins/HumanThinking
            os.path.join(os.path.expanduser("~"), ".qwenpaw", "plugins", "HumanThinking"),
            os.path.join(os.path.dirname(qwenpaw_root), "plugins", "HumanThinking"),
        ]
        for d in possible_dirs:
            if os.path.isdir(d):
                plugin_dir = d
                break
        
        if plugin_dir is None:
            results["errors"].append(f"无法找到插件目录，尝试了: {possible_dirs}")
            return results
    
    if not os.path.isdir(plugin_dir):
        results["errors"].append(f"插件目录不存在: {plugin_dir}")
        return results
    
    logger.info(f"Using plugin directory: {plugin_dir}")
    
    source_core = os.path.join(plugin_dir, "core")
    source_search = os.path.join(plugin_dir, "search")
    source_hooks = os.path.join(plugin_dir, "hooks")
    source_utils = os.path.join(plugin_dir, "utils")
    source_init = os.path.join(plugin_dir, "__init__.py")
    
    logger.info(f"Looking for source files in: {plugin_dir}")
    logger.info(f"  core/ exists: {os.path.isdir(source_core)}")
    logger.info(f"  search/ exists: {os.path.isdir(source_search)}")
    logger.info(f"  hooks/ exists: {os.path.isdir(source_hooks)}")
    logger.info(f"  utils/ exists: {os.path.isdir(source_utils)}")
    logger.info(f"  __init__.py exists: {os.path.isfile(source_init)}")
    
    # 创建目标目录（只在不存在时创建，避免触发 WatchFiles）
    try:
        if os.path.exists(target_dir):
            # 检查是否已经安装（跳过重复安装，避免触发 WatchFiles 热重载循环）
            marker_file = os.path.join(target_dir, ".ht_installed")
            if os.path.exists(marker_file):
                with open(marker_file, "r", encoding="utf-8") as f:
                    marker_content = f.read().strip()
                
                # 标记文件记录安装时间，如果超过 24 小时则重新安装
                try:
                    install_time = float(marker_content)
                    import time
                    if time.time() - install_time < 86400:  # 24 小时内不重装
                        logger.info(f"HumanThinkingMemoryManager already installed (marker age: {(time.time() - install_time)/3600:.1f}h), skipping")
                        results["success"] = True
                        results["patched"] = True
                        results["skipped"] = True
                        return results
                except ValueError:
                    pass
            
            logger.info(f"Removing existing installation at: {target_dir}")
            shutil.rmtree(target_dir)
        
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Created target directory: {target_dir}")
    except Exception as e:
        results["errors"].append(f"创建目标目录失败: {e}")
        return results
    
    # 复制目录
    items_to_copy = [
        ("core", source_core),
        ("search", source_search),
        ("hooks", source_hooks),
        ("utils", source_utils),
    ]
    
    for name, source in items_to_copy:
        if os.path.isdir(source):
            target = os.path.join(target_dir, name)
            try:
                if os.path.exists(target):
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                logger.info(f"  ✓ Copied {name}/")
                results["details"][name] = "copied"
            except Exception as e:
                results["errors"].append(f"复制 {name}/ 失败: {e}")
        else:
            logger.warning(f"  ✗ Source {name}/ not found, skipping")
            results["details"][name] = "not_found"
    
    # 复制 __init__.py
    if os.path.isfile(source_init):
        target_init = os.path.join(target_dir, "__init__.py")
        try:
            shutil.copy2(source_init, target_init)
            logger.info(f"  ✓ Copied __init__.py")
            results["details"]["__init__.py"] = "copied"
        except Exception as e:
            results["errors"].append(f"复制 __init__.py 失败: {e}")
    else:
        # 创建基本的 __init__.py
        target_init = os.path.join(target_dir, "__init__.py")
        try:
            with open(target_init, "w") as f:
                f.write("# HumanThinking Memory Manager\n")
            logger.info(f"  ✓ Created basic __init__.py")
            results["details"]["__init__.py"] = "created"
        except Exception as e:
            results["errors"].append(f"创建 __init__.py 失败: {e}")
    
    # 验证安装
    memory_manager_file = os.path.join(target_dir, "core", "memory_manager.py")
    if os.path.isfile(memory_manager_file):
        logger.info(f"  ✓ Installation verified: core/memory_manager.py exists")
        results["success"] = True
        results["installed"] = True
        
        # 创建安装标记文件（避免下次启动重复安装触发 WatchFiles）
        import time
        marker_file = os.path.join(target_dir, ".ht_installed")
        try:
            with open(marker_file, "w", encoding="utf-8") as f:
                f.write(str(time.time()))
            logger.info(f"  ✓ Installation marker created: {marker_file}")
        except Exception as e:
            logger.warning(f"  ✗ Failed to create installation marker: {e}")
    else:
        results["errors"].append("安装验证失败: core/memory_manager.py 不存在")
    
    return results


def patch_workspace_import(qwenpaw_root: str) -> dict:
    """修复 workspace.py 使其支持 human_thinking 后端
    
    需要：
    1. 添加 HumanThinkingMemoryManager 导入
    2. 添加 elif backend == "human_thinking": 分支
    3. 修复 ConfigurationException 添加 config_key
    """
    results = {"success": False, "patched": False, "errors": []}
    
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
    except ImportError:
        results["errors"].append("无法导入 qwenpaw 包")
        return results
    
    workspace_file = os.path.join(qwenpaw_pkg_dir, "app", "workspace", "workspace.py")
    if not os.path.isfile(workspace_file):
        results["errors"].append(f"workspace.py 不存在: {workspace_file}")
        return results
    
    try:
        with open(workspace_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经修补
        if 'human_thinking' in content and 'HumanThinkingMemoryManager' in content:
            logger.info(f"workspace.py already supports human_thinking")
            results["success"] = True
            results["patched"] = True
            # 但仍需确保 config_key 存在
            if 'config_key="memory_manager_backend"' not in content and "config_key='memory_manager_backend'" not in content:
                logger.info(f"  Adding config_key to ConfigurationException...")
                content = content.replace(
                    'message=f"Unsupported memory manager backend: \'{backend}\'",\n    )',
                    'message=f"Unsupported memory manager backend: \'{backend}\'",\n        config_key="memory_manager_backend",\n    )'
                )
                if content:
                    _make_backup(workspace_file)
                    with open(workspace_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"  ✓ Added config_key")
            return results
        
        _make_backup(workspace_file)
        logger.info(f"Patching workspace.py to support human_thinking...")
        
        # 1. 添加 HumanThinkingMemoryManager 导入
        old_import = 'from ...agents.memory import ReMeLightMemoryManager'
        new_imports = '''from ...agents.memory import ReMeLightMemoryManager
    from ...agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager'''
        
        if old_import in content:
            content = content.replace(old_import, new_imports)
            logger.info(f"  ✓ Added HumanThinkingMemoryManager import")
        else:
            logger.warning(f"  ✗ Could not find ReMeLightMemoryManager import")
            results["errors"].append("未找到 ReMeLightMemoryManager 导入")
        
        # 2. 添加 human_thinking 分支
        old_branch = '''    if backend == "remelight":
        return ReMeLightMemoryManager'''
        new_branch = '''    if backend == "remelight":
        return ReMeLightMemoryManager
    elif backend == "human_thinking":
        return HumanThinkingMemoryManager'''
        
        if old_branch in content:
            content = content.replace(old_branch, new_branch)
            logger.info(f"  ✓ Added human_thinking branch")
        else:
            logger.warning(f"  ✗ Could not find remelight branch")
            results["errors"].append("未找到 remelight 分支")
        
        # 3. 添加 config_key 到 ConfigurationException
        if 'config_key="memory_manager_backend"' not in content:
            old_exception = 'message=f"Unsupported memory manager backend: \'{backend}\'",\n    )'
            new_exception = 'message=f"Unsupported memory manager backend: \'{backend}\'",\n        config_key="memory_manager_backend",\n    )'
            if old_exception in content:
                content = content.replace(old_exception, new_exception)
                logger.info(f"  ✓ Added config_key to ConfigurationException")
            else:
                logger.warning(f"  ✗ Could not find ConfigurationException pattern")
        
        # 写入文件
        if content:
            with open(workspace_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"✓ workspace.py patched successfully")
            results["success"] = True
            results["patched"] = True
    
    except Exception as e:
        logger.error(f"Failed to patch workspace.py: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def patch_backend_config(qwenpaw_root: str) -> dict:
    """修改后端配置，使 memory_manager_backend 接受 human_thinking
    
    服务器上安装的 QwenPaw 版本中，config.py 的 memory_manager_backend 
    类型定义是 Literal["remelight"]，需要改为 Literal["remelight", "human_thinking"]
    """
    results = {"success": True, "patched_files": [], "errors": []}
    
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
    except ImportError:
        results["success"] = False
        results["errors"].append("无法导入 qwenpaw 包")
        return results
    
    config_dir = os.path.join(qwenpaw_pkg_dir, "config")
    if not os.path.isdir(config_dir):
        results["success"] = False
        results["errors"].append(f"配置目录不存在: {config_dir}")
        return results
    
    logger.info(f"Patching backend config in: {config_dir}")
    
    # 查找 config.py 文件
    config_file = os.path.join(config_dir, "config.py")
    if not os.path.isfile(config_file):
        results["success"] = False
        results["errors"].append(f"config.py 不存在: {config_file}")
        return results
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经包含 human_thinking
        if 'human_thinking' in content and 'memory_manager_backend' in content:
            # 验证是否是正确的格式
            if 'Literal["remelight", "human_thinking"]' in content or "Literal['remelight', 'human_thinking']" in content:
                logger.info(f"Backend config already patched: {config_file}")
                results["patched_files"].append(os.path.basename(config_file))
                return results
        
        # 查找 memory_manager_backend 的 Literal 定义
        # 模式1: Literal["remelight"]
        pattern1 = r'Literal\["remelight"\]'
        # 模式2: Literal['remelight']
        pattern2 = r"Literal\['remelight'\]"
        
        match = re.search(pattern1, content)
        if match:
            logger.info(f"Found Literal['remelight'] in config.py (double quotes)")
            logger.info(f"  Match: {match.group(0)} at position {match.start()}")
            
            # 创建备份
            _make_backup(config_file)
            
            # 替换为包含 human_thinking 的版本
            new_content = content.replace(
                'Literal["remelight"]',
                'Literal["remelight", "human_thinking"]'
            )
            
            if new_content != content:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"✓ Patched backend config: {config_file}")
                logger.info(f"  Changed: Literal['remelight'] -> Literal['remelight', 'human_thinking']")
                results["patched_files"].append(os.path.basename(config_file))
                
                # ====== 关键：强制重新加载模块 ======
                # 修改磁盘文件后，需要强制重新加载模块才能让运行时生效
                try:
                    import qwenpaw.config.config as config_module
                    import sys
                    
                    # 从 sys.modules 中移除，然后重新导入
                    module_name = 'qwenpaw.config.config'
                    if module_name in sys.modules:
                        old_module = sys.modules.pop(module_name)
                    else:
                        old_module = None
                    
                    # 重新导入
                    import importlib
                    new_module = importlib.import_module('qwenpaw.config.config')
                    
                    # 同时清理 pydantic 缓存
                    import pydantic.main
                    if hasattr(pydantic.main, '_cache'):
                        pydantic.main._cache.clear()
                    
                    logger.info("  ✓ Reloaded qwenpaw.config.config module")
                except Exception as e:
                    logger.warning(f"  ✗ Failed to reload module: {e}")
            else:
                logger.warning(f"Pattern matched but replacement produced no change")
        
        elif re.search(pattern2, content):
            logger.info(f"Found Literal['remelight'] in config.py (single quotes)")
            _make_backup(config_file)
            
            new_content = content.replace(
                "Literal['remelight']",
                "Literal['remelight', 'human_thinking']"
            )
            
            if new_content != content:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"✓ Patched backend config: {config_file}")
                results["patched_files"].append(os.path.basename(config_file))
        
        else:
            # 可能已经是多值 Literal 或者格式不同
            logger.warning(f"Could not find Literal['remelight'] pattern in config.py")
            logger.warning(f"  memory_manager_backend may already support multiple values")
            logger.warning(f"  Or the format is different than expected")
            
            # 搜索 memory_manager_backend 附近的上下文
            mmb_idx = content.find("memory_manager_backend")
            if mmb_idx >= 0:
                start = max(0, mmb_idx - 50)
                end = min(len(content), mmb_idx + 300)
                logger.info(f"  Context: {content[start:end]}")
            
            results["errors"].append("未找到 Literal['remelight'] 模式")
    
    except Exception as e:
        logger.error(f"Failed to patch backend config: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def patch_runtime_config_model() -> dict:
    """修补运行时内存中的 Pydantic 模型，使其接受 human_thinking
    
    关键问题：即使修改了磁盘上的 config.py 文件，Python 进程已经在内存中
    缓存了旧的 AgentsRunningConfig 类定义。Pydantic 验证使用的是内存中的
    类定义，所以必须同时修补内存中的模型。
    
    修补方式：
    1. 修改 __annotations__ 中的 Literal 类型定义
    2. 同步更新 model_fields
    3. 清理 Pydantic 内部缓存（核心！）
    4. 调用 model_rebuild() 重新构建模型
    """
    results = {"success": False, "patched": False, "errors": []}
    
    try:
        import qwenpaw.config.config
        from qwenpaw.config.config import AgentsRunningConfig
        from typing import Literal, get_args
        import pydantic
        
        # 检查当前类型定义
        current_annotation = AgentsRunningConfig.__annotations__.get('memory_manager_backend')
        current_args = get_args(current_annotation) if hasattr(current_annotation, '__args__') else ()
        
        if 'human_thinking' in current_args:
            logger.info("Runtime AgentsRunningConfig already accepts human_thinking")
            results["success"] = True
            results["patched"] = True
            return results
        
        logger.info(f"Current memory_manager_backend Literal values: {current_args}")
        logger.info("Patching runtime AgentsRunningConfig.__annotations__...")
        
        # 核心修补：直接修改 __annotations__
        new_literal = Literal["remelight", "human_thinking"]
        qwenpaw.config.config.AgentsRunningConfig.__annotations__['memory_manager_backend'] = new_literal
        AgentsRunningConfig.__annotations__['memory_manager_backend'] = new_literal
        
        # 同步更新 model_fields（Pydantic v2 运行时）
        field = AgentsRunningConfig.model_fields.get('memory_manager_backend')
        if field is not None:
            field.annotation = new_literal
            logger.info(f"Patched model_fields['memory_manager_backend'].annotation = {new_literal}")
        
        # ========== 关键：清理 Pydantic 内部缓存 ==========
        # Pydantic 会在模块加载时缓存 validator，即使修改了 __annotations__
        # 也需要清理这些缓存才能让新的 Literal 值生效
        
        try:
            # 清理模型级别的缓存
            if hasattr(AgentsRunningConfig, '__pydantic_validator__'):
                del AgentsRunningConfig.__pydantic_validator__
            if hasattr(AgentsRunningConfig, '__pydantic_fields_schema__'):
                del AgentsRunningConfig.__pydantic_fields_schema__
            if hasattr(AgentsRunningConfig, '__pydantic_complete__'):
                AgentsRunningConfig.__pydantic_complete__ = False
            if hasattr(AgentsRunningConfig, '_cache_key'):
                del AgentsRunningConfig._cache_key
            logger.info("Cleared Pydantic model caches")
        except (AttributeError, KeyError) as e:
            logger.debug(f"Some Pydantic caches not found (may be normal): {e}")
        
        # 尝试清理全局 Pydantic 缓存
        try:
            if hasattr(pydantic.main, '_cache'):
                pydantic.main._cache.clear()
                logger.info("Cleared global Pydantic cache")
        except:
            pass
        
        # 重建模型
        logger.info("Rebuilding Pydantic model...")
        AgentsRunningConfig.model_rebuild(force=True)
        
        # 再次清理缓存（双重保险）
        try:
            if hasattr(AgentsRunningConfig, '__pydantic_complete__'):
                AgentsRunningConfig.__pydantic_complete__ = False
        except:
            pass
        
        # 验证
        verify_field = AgentsRunningConfig.model_fields.get('memory_manager_backend')
        if verify_field:
            field_args = get_args(verify_field.annotation) if hasattr(verify_field.annotation, '__args__') else ()
            if 'human_thinking' in field_args:
                logger.info(f"✓ Runtime AgentsRunningConfig patched successfully")
                logger.info(f"  New Literal values: {field_args}")
                results["success"] = True
                results["patched"] = True
            else:
                results["errors"].append(f"Verification failed: human_thinking not in Literal after patch, got {field_args}")
                logger.warning(f"✗ Runtime patch verification failed, field_args: {field_args}")
        else:
            results["errors"].append("model_fields verification failed")
            logger.warning(f"✗ Cannot find memory_manager_backend in model_fields")
    
    except Exception as e:
        logger.error(f"Failed to patch runtime config model: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def patch_production_ui(qwenpaw_root: str) -> dict:
    """
    修改生产环境的前端文件

    Args:
        qwenpaw_root: QwenPaw 根目录

    Returns:
        修改结果
    """
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)

    if not console_dir:
        return {
            "success": False,
            "error": "无法找到 QwenPaw console 静态文件目录",
        }

    logger.info(f"Found console directory: {console_dir}")
    logger.info(f"Console directory contents (first level):")
    try:
        items = os.listdir(console_dir)
        logger.info(f"  Files/dirs: {', '.join(items[:20])}")
        if len(items) > 20:
            logger.info(f"  ... and {len(items) - 20} more items")
    except Exception as e:
        logger.warning(f"  Cannot list directory: {e}")

    results = {
        "success": True,
        "console_dir": console_dir,
        "patched_files": [],
    }

    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))

    logger.info(f"Scanning {len(js_files)} JS files for remelight references...")

    patched_count = 0
    for idx, js_file in enumerate(js_files, 1):
        if patch_js_file(js_file):
            results["patched_files"].append(os.path.basename(js_file))
            patched_count += 1

    if patched_count > 0:
        logger.info(f"Successfully patched {patched_count} file(s)")
    else:
        logger.warning("No files were patched - may need manual review")
        results["success"] = False
        results["error"] = "未找到包含 remelight 选项对象的 JS 文件"

    return results


def restore_production_ui(qwenpaw_root: str) -> dict:
    """恢复生产环境的前端文件"""
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)

    if not console_dir:
        return {"success": False, "error": "无法找到 console 目录"}

    results = {"success": True, "restored": []}

    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".humanthinking.bak"):
                original = f.replace(".humanthinking.bak", "")
                backup = os.path.join(root, f)
                original_path = os.path.join(root, original)
                
                if _restore_backup(original_path):
                    results["restored"].append(original)

    return results


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python prod_ui_patcher.py <qwenpaw_root>")
        sys.exit(1)

    qwenpaw_root = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--restore":
        result = restore_production_ui(qwenpaw_root)
        print(f"Restore result: {result}")
    else:
        result = patch_production_ui(qwenpaw_root)
        print(f"Patch result: {result}")
