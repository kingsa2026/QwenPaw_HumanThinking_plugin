# -*- coding: utf-8 -*-
"""生产环境 UI 修补- 直接modify bundled的前端 JS 文件

?QwenPaw 生产部署环境中，前端已编译为打包JS 文件
本脚本通过正则匹配和替换，直接modify bundled的 JS 文件
?HumanThinking 添加到记忆管理器下拉选项中

适配多环境：Docker、Windows、macOS、Linux
"""

import logging
import os
import re
import shutil
import sys
from pathlib import Path

# 导入环境检测模
sys.path.insert(0, str(Path(__file__).parent))
from utils.env_detector import detect_qwenpaw_env, get_qwenpaw_console_dir

# Use "qwenpaw" namespace so logs are captured by QwenPaw's logging system
logger = logging.getLogger("qwenpaw.humanthinking.patcher")


def find_qwenpaw_console_static_dir(qwenpaw_root: str) -> str:
    """查找 QwenPaw 打包后的 console 静态文件目- 使用环境检"""
    # 方法1: 使用环境检测模
    env = detect_qwenpaw_env()
    console_dir = get_qwenpaw_console_dir(env)
    if console_dir:
        logger.info(f"Found console directory via env detection: {console_dir}")
        return str(console_dir)
    
    # 方法2: 通过 Python 包查
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
        console_dir = os.path.join(qwenpaw_pkg_dir, "console")
        if os.path.isdir(console_dir) and os.path.isfile(os.path.join(console_dir, "index.html")):
            return console_dir
    except (ImportError, AttributeError):
        pass

    # 方法3: common paths径（包venv 中的 site-packages?
    candidates = [
        os.path.join(qwenpaw_root, "console"),
        os.path.join(qwenpaw_root, "dist", "console"),
        os.path.expanduser("~/.qwenpaw/console"),
        "/root/.qwenpaw/console",
        "/app/working/console",  # Docker默认路径
    ]
    
    # 动态添加venv路径
    env = detect_qwenpaw_env()
    if env.venv_dir:
        for python_dir in (env.venv_dir / "lib").glob("python3.*"):
            candidates.append(str(python_dir / "site-packages" / "qwenpaw" / "console"))
    
    # 系统级installation路
    candidates.extend([
        "/usr/local/lib/python3.12/site-packages/qwenpaw/console",
        "/usr/local/lib/python3.11/site-packages/qwenpaw/console",
        "/usr/local/lib/python3.10/site-packages/qwenpaw/console",
        "/usr/lib/python3.12/site-packages/qwenpaw/console",
        "/usr/lib/python3.11/site-packages/qwenpaw/console",
        "/usr/lib/python3.10/site-packages/qwenpaw/console",
    ])

    for candidate in candidates:
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "index.html")):
            logger.info(f"Found console directory: {candidate}")
            return candidate

    logger.warning("No console static directory found")
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
    """从备份恢复文"""
    backup_path = filepath + ".humanthinking.bak"
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, filepath)
        os.remove(backup_path)
        logger.info(f"Restored: {filepath}")
        return True
    return False


def _patch_js_files_for_human_thinking(qwenpaw_root: str) -> list:
    """
    修补打包后的 JS 文件，添human_thinking 选项

    v1.1.3.post1 pip 包中没有 TypeScript 源码，只有打包后JS 文件
    这个函数直接修补 JS 文件

    Returns:
        list: 成功修补的文件列
    """
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        logger.warning("Cannot find console directory")
        return []

    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))

    logger.info(f"扫描 {len(js_files)} ?JS 文件...")

    patched_files = []
    for js_file in js_files:
        if patch_js_file(js_file):
            patched_files.append(os.path.basename(js_file))

    if patched_files:
        logger.info(f"成功修补 {len(patched_files)} ?JS 文件: {', '.join(patched_files)}")
    else:
        logger.warning("没有找到需要修补的 JS 文件")

    return patched_files


def patch_js_file(filepath: str) -> bool:
    """
    modify bundled的 JS 文件，添HumanThinking 选项

    支持 v1.1.3.post1 ?v1.1.4 两种格式
    - v1.1.3.post1: {value:"remelight",label:"ReMeLight"} 内联数组格式
    - v1.1.4: backendMappings-DNEC3qGm.js 独立 chunk 格式
      var r={remelight:{...}}, a=Object.entries(r).map(...)
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

        # 检查是否包remelight 相关代码
        if "remelight" not in content.lower():
            logger.debug(f"No remelight reference in: {os.path.basename(filepath)}")
            return False

        logger.info(f"Found remelight reference in: {os.path.basename(filepath)}")

        _make_backup(filepath)

        # ============================================
        # 模式 A0: Ta= 格式 (新版 QwenPaw bundled JS)
        # Ta={remelight:{configField:"reme_light_memory_config",component:Ca,label:"remelight",tabKey:"remeLightMemory"}}
        # GT=Object.entries(Ta).map(...) -> 下拉菜单选项
        # ============================================
        ta_match = re.search(r"Ta\s*=\s*\{[^}]*remelight[^}]*\}", content)
        if ta_match:
            logger.info(f"  ?Detected Ta= format in {os.path.basename(filepath)}")
            original_ta = ta_match.group(0)

            component_match = re.search(r'component:([A-Za-z0-9_$]+)', original_ta)
            if component_match:
                component_var = component_match.group(1)
                logger.info(f"  ?Extracted component var: {component_var}")
            else:
                component_var = 'Ca'
                logger.warning(f"  ?Could not extract component var, using default: {component_var}")

            ht_entry = f',human_thinking:{{configField:"human_thinking_config",component:{component_var},label:"human_thinking",tabKey:"remeLightMemory"}}'

            # 在 Ta 对象的最后一个 } 之前插入 human_thinking 条目
            # 精确替换整个 Ta={...} 块
            new_ta = re.sub(
                r'(remelight:\{[^}]*\})',
                rf'\1{ht_entry}',
                original_ta,
                count=1
            )

            if new_ta != original_ta:
                content = content.replace(original_ta, new_ta)
                if "human_thinking" not in content:
                    logger.error(f"?Failed to inject human_thinking into Ta=")
                    return False
                logger.info(f"  ?Patched Ta= mapping with human_thinking in {os.path.basename(filepath)}")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"?Successfully patched Ta= format: {os.path.basename(filepath)}")
                return True
            else:
                logger.warning(f"  ?Ta= substitution produced no change, trying fallback...")
                # fallback: 直接用字符串替换
                fallback_new = original_ta.rstrip("}") + ht_entry + "}"
                if fallback_new != original_ta:
                    content = content.replace(original_ta, fallback_new)
                    if "human_thinking" in content:
                        logger.info(f"  ?Fallback Ta= patching succeeded")
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        logger.info(f"?Successfully patched Ta= format (fallback): {os.path.basename(filepath)}")
                        return True

        # ============================================
        # 模式 A: v1.1.4 backendMappings chunk 格式
        # var r={remelight:{configField:`...`,component:_a,label:`remelight`,tabKey:`remeLightMemory`}}
        # var a=Object.entries(r).map(([e,{label:t}])=>({value:e,label:t}));
        # ============================================
        # 关键修改
        # 1. human_thinking 使用 tabKey: remeLightMemory（显长期记忆"
        # 2. component 必须指向 ReMeLightMemoryCard 组件（变量名 _a?
        # 3. 不使human_thinking_config，因为前端只查找 xa[memoryBackend]（即 xa['human_thinking']?
        # ============================================
        v114_mapping_pattern = r'var\s+\w+\s*=\s*\{[^}]*remelight[^}]*\}'
        v114_match = re.search(v114_mapping_pattern, content)
        
        if v114_match:
            logger.info(f"  ?Detected v1.1.4 backendMappings chunk format")
            
            # ?r 对象中添human_thinking 映射
            original_mapping = v114_match.group(0)
            
            # 提取 remelight 使用component 变量名（?_a?
            component_match = re.search(r'component:([A-Za-z0-9_$]+)', original_mapping)
            if component_match:
                component_var = component_match.group(1)
                logger.info(f"  ?Found ReMeLightMemoryCard component variable: {component_var}")
            else:
                component_var = '_a'  # 默认
                logger.warning(f"  ?Could not detect component variable, using default: {component_var}")
            
            # human_thinking: 使用 remeLightMemory tabKey（显长期记忆"
            # component 使用remelight 相同的组件变量（ReMeLightMemoryCard?
            ht_mapping = f',human_thinking:{{configField:`human_thinking_config`,component:{component_var},label:`human_thinking`,tabKey:`remeLightMemory`}}'
            
            # ?remelight 条目后添human_thinking 条目
            new_mapping = original_mapping.replace(
                'remelight:{configField:`reme_light_memory_config`,component:t,label:`remelight`,tabKey:`remeLightMemory`}',
                'remelight:{configField:`reme_light_memory_config`,component:t,label:`remelight`,tabKey:`remeLightMemory`}' + ht_mapping
            )
            
            if new_mapping == original_mapping:
                # 可能是反引号格式不同，尝试更宽松的匹
                new_mapping = re.sub(
                    r'(remelight\s*:\s*\{[^}]*\})',
                    rf'\1,human_thinking:{{configField:`human_thinking_config`,component:{component_var},label:`human_thinking`,tabKey:`remeLightMemory`}}',
                    original_mapping,
                    count=1
                )
            
            content = content.replace(original_mapping, new_mapping)
            
            # 验证 human_thinking 是否已添
            if "human_thinking" not in content:
                logger.error(f"?Failed to inject human_thinking mapping")
                return False
            
            logger.info(f"  ?Injected human_thinking into MEMORY_MANAGER_BACKEND_MAPPINGS")
            logger.info(f"  ?tabKey 'remeLightMemory' -> 显示'长期记忆'")
            logger.info(f"  ?component '{component_var}' -> ReMeLightMemoryCard")
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"?Successfully patched v1.1.4 chunk: {os.path.basename(filepath)}")
            return True

        # ============================================
        # 模式 B: v1.1.5+ 动态组件映射格
        # 使用 fa[C] ?xa[T] 作为组件查找
        # ============================================
        # 检查是否使用了动态组件映射系
        if "fa[C]" in content and "xa[T]" in content:
            logger.info(f"  ?Detected v1.1.5+ dynamic component mapping format")
            
            # 这个版本使用动态映射，我们需要直接修xT 数组xa 映射
            # xT 是选项数组，xa 是组件映射表
            patched = False
            
            # 1. 修改 xT 数组（选项列表
            # 查找 xT=[{value:"remelight",label:"ReMeLight"}] 或类似格
            xT_patterns = [
                (r'(xT=\[\{value:"remelight",label:"ReMeLight"\}\])', r'xT=[{value:"remelight",label:"ReMeLight"},{value:"human_thinking",label:"Human Thinking"}]'),
                (r"(xT=\[\{value:'remelight',label:'ReMeLight'\}\])", r"xT=[{value:'remelight',label:'ReMeLight'},{value:'human_thinking',label:'Human Thinking'}]"),
                (r'(xT=\[\{value:"remelight"[^}]*\}\])', r'\1,xT.push({value:"human_thinking",label:"Human Thinking"})'),
            ]
            
            for pattern, replacement in xT_patterns:
                if re.search(pattern, content):
                    if 'human_thinking' not in content:
                        _make_backup(filepath)
                    new_content = re.sub(pattern, replacement, content, count=1)
                    if new_content != content:
                        content = new_content
                        patched = True
                        logger.info(f"  ?Patched xT array with human_thinking option")
                    break
            
            # 2. 修改 xa 映射表（组件映射
            # 关键修复：tabKey 必须remeLightMemory（使用已有的 i18n 翻译
            # component 必须使用 _a（ReMeLightMemoryCard），不能使用 function(){return null}
            # 查找 xa={remelight:{...}} 或类似格式，直接合并到对象中
            xa_patterns = [
                # 模式1: xa={remelight:{...}} ?xa={remelight:{...},human_thinking:{...}}
                # tabKey 使用 remeLightMemory 而不humanThinkingMemory，避i18n 缺失问题
                # component 使用 _a（ReMeLightMemoryCard?
                (r'(xa=\{remelight:\{[^}]*\}\})', r'xa={remelight:{configField:"reme_light_memory_config",component:_a,label:"remelight",tabKey:"remeLightMemory"},human_thinking:{configField:"human_thinking_config",component:_a,label:"human_thinking",tabKey:"remeLightMemory"}}'),
            ]
            
            for pattern, replacement in xa_patterns:
                if re.search(pattern, content):
                    new_content = re.sub(pattern, replacement, content, count=1)
                    if new_content != content:
                        content = new_content
                        patched = True
                        logger.info(f"  ?Patched xa mapping with human_thinking component")
                        logger.info(f"  ?tabKey set to 'remeLightMemory' (uses existing i18n)")
                    break
            
            if patched:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"?Successfully patched v1.1.5+ JS file: {os.path.basename(filepath)}")
                return True
            else:
                # 如果直接修改失败，使用兜底方案：在文件末尾注入动态注册代
                # 关键修复：tabKey 使用 remeLightMemory 而不humanThinkingMemory
                injection_code = '''
// HumanThinking: Dynamic backend registration for v1.1.5+
(function(){
    if (window.__humanThinkingRegistered) return;
    window.__humanThinkingRegistered = true;
    
    // 拦截 xT 数组访问
    Object.defineProperty(window, 'xT', {
        get: function() {
            return window.__xT || [];
        },
        set: function(val) {
            window.__xT = val;
            // 添加 Human Thinking 选项
            if (val && Array.isArray(val) && !val.find(function(o){return o.value==='human_thinking'})) {
                val.push({value:"human_thinking",label:"Human Thinking"});
                console.log('[HumanThinking] ?Added to xT array');
            }
        }
    });
    
    // 拦截 xa 映射访问
    // 关键：tabKey 必须remeLightMemory（前端已存在i18n 翻译
    // 如果使用 humanThinkingMemory，前端会查找 agentConfig.humanThinkingMemoryTitle，但该翻译 not found在
    Object.defineProperty(window, 'xa', {
        get: function() {
            return window.__xa || {};
        },
        set: function(val) {
            window.__xa = val;
            // 添加 Human Thinking 组件映射
            if (val && typeof val === 'object' && !val.human_thinking) {
                val.human_thinking = {component:function(){return null},tabKey:"remeLightMemory",label:"human_thinking"};
                console.log('[HumanThinking] ?Added to xa mapping (tabKey: remeLightMemory)');
            }
        }
    });
})();
'''
                if "__humanThinkingRegistered" not in content:
                    _make_backup(filepath)
                    new_content = content + injection_code
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    logger.info(f"?Successfully patched v1.1.5+ JS file (fallback): {os.path.basename(filepath)}")
                    return True
                else:
                    logger.debug(f"Already patched v1.1.5+: {filepath}")
                    return True
        
        # ============================================
        # 模式 C: v1.1.3.post1 内联数组格式
        # {value:"remelight",label:"ReMeLight"}
        # ============================================
        
        # 快速检查：是否包含 remelight 选项对象语法
        remelight_option_match = re.search(r'\{\s*[^}]*?\bvalue\s*:\s*["\']remelight["\'][^}]*?\blabel\s*:', content)
        if not remelight_option_match:
            logger.info(f"  Skipping: no remelight option object (only i18n text)")
            logger.info(f"  Found 'remelight' but not as option object. Searching for context...")
            # 查找 remelight 出现的位
            for match in re.finditer(r'.{0,50}remelight.{0,50}', content, re.IGNORECASE):
                logger.info(f"    Context: ...{match.group(0)}...")
            return False

        # 详细调试：查remelight 的上下文
        remelight_idx = content.lower().find("remelight")
        if remelight_idx >= 0:
            context_start = max(0, remelight_idx - 100)
            context_end = min(len(content), remelight_idx + 200)
            context = content[context_start:context_end]
            logger.info(f"  Context around 'remelight': ...{context}...")

        # 替换模式: ?remelight 选项后添human_thinking
        patterns_to_try = [
            # 模式1: 标准紧凑格式 {value:"remelight",label:"ReMeLight"}
            r'(\{value\s*:\s*"remelight"\s*,\s*label\s*:\s*"ReMeLight"\s*\})',
            # 模式2: 单引号格{value:'remelight',label:'ReMeLight'}
            r"(\{value\s*:\s*'remelight'\s*,\s*label\s*:\s*'ReMeLight'\s*\})",
            # 模式3: 带额外字段的格式 {value:"remelight",label:"ReMeLight",...}
            r'(\{value\s*:\s*"remelight"[^}]*(?:\??)\})',
        ]

        match = None
        matched_pattern = None
        for i, pattern in enumerate(patterns_to_try, 1):
            match = re.search(pattern, content)
            if match:
                matched_pattern = i
                logger.info(f"  ?Pattern {i} matched: {pattern}")
                logger.info(f"  ?Matched text: {match.group(0)}")
                break
            else:
                logger.info(f"  ?Pattern {i} did not match: {pattern}")

        if not match:
            logger.warning(f"?No remelight option object found in {os.path.basename(filepath)}")
            return False
        
        matched_pattern_idx = matched_pattern - 1
        matched_pattern_str = patterns_to_try[matched_pattern_idx]
        
        def replacer(match):
            original = match.group(1)
            new_option = ',{value:"human_thinking",label:"Human Thinking"}'
            logger.info(f"  Original option: {original}")
            logger.info(f"  Injecting: {new_option}")
            result = original + new_option
            logger.info(f"  Result: {result}")
            return result
        
        new_content = re.sub(matched_pattern_str, replacer, content, count=1)
        
        if new_content != content:
            if "human_thinking" not in new_content:
                logger.error(f"?human_thinking not found in patched content!")
                return False
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info(f"?Successfully patched v1.1.3 JS file: {os.path.basename(filepath)}")
            return True

        logger.warning(f"Pattern did not match in {os.path.basename(filepath)}")
        return False

    except Exception as e:
        logger.error(f"Failed to patch {filepath}: {e}", exc_info=True)
        return False


def patch_index_html(qwenpaw_root: str, plugin_dir: str = None) -> dict:
    """
    修补 index.html，注入 frontend.js 脚本标签
    
    frontend.js 包含完整的 HT Config UI（压缩模式、跨会话记忆等设置面板）
    以及记忆管理器下拉菜单增强和 HT 配置标签页。
    
    这是核心注入点——之前的实现只是修补 bundled JS 添加 dropdown 选项，
    但 frontend.js 本身从未被加载，导致 showHTConfigTab() 等函数无法运行。
    """
    results = {"success": False, "errors": []}
    
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        results["errors"].append("Cannot find console directory")
        return results
    
    index_html = os.path.join(console_dir, "index.html")
    if not os.path.isfile(index_html):
        results["errors"].append(f"index.html not found: {index_html}")
        return results
    
    try:
        with open(index_html, "r", encoding="utf-8") as f:
            content = f.read()
        
        if 'frontend.js' in content:
            logger.info("[patch_index_html] Already injected")
            results["success"] = True
            return results
        
        # 复制 frontend.js 到 assets 目录
        if plugin_dir and os.path.isdir(plugin_dir):
            source_js = os.path.join(plugin_dir, "frontend.js")
        else:
            source_js = os.path.join(qwenpaw_root, "plugins", "HumanThinking", "frontend.js")
            if not os.path.isfile(source_js):
                source_js = os.path.join(os.path.expanduser("~"), ".qwenpaw", "plugins", "HumanThinking", "frontend.js")
        
        assets_dir = os.path.join(console_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        target_js = os.path.join(assets_dir, "frontend.js")
        
        if os.path.isfile(source_js):
            shutil.copy2(source_js, target_js)
            logger.info(f"[patch_index_html] Copied frontend.js to {target_js}")
        else:
            logger.warning(f"[patch_index_html] frontend.js source not found: {source_js}")
            results["errors"].append(f"Source frontend.js not found: {source_js}")
        
        _make_backup(index_html)
        
        script_tag = '    <script defer src="/assets/frontend.js"></script>\n  </body>'
        new_content = content.replace('</body>', script_tag)
        
        if new_content != content:
            with open(index_html, "w", encoding="utf-8") as f:
                f.write(new_content)
            logger.info("[patch_index_html] ✓ Injected frontend.js script into index.html")
            results["success"] = True
        else:
            results["errors"].append("Content unchanged after replacement")
    
    except Exception as e:
        results["errors"].append(str(e))
        logger.error(f"[patch_index_html] Failed: {e}", exc_info=True)
    
    return results


def patch_human_thinking_config_tab(qwenpaw_root: str) -> dict:
    """
    修补前端JS，在选择 HumanThinking 时添加"HT记忆配置" tab
    
    问题：原生UI只支持一个记忆管理tab。选择 HumanThinking 后，
    需要显示两个tab?长期记忆" + "HT记忆配置"
    解决方案：modify bundled的JS，在 dynamicTabs 生成逻辑中注入额外的tab?
    ?memoryBackend ?human_thinking 时，额外添加一HT记忆配置 tab?
    """
    results = {"success": False, "patched": [], "errors": []}
    
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        results["errors"].append("Cannot find console directory")
        return results
    
    # 查找所有JS文件
    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))
    
    logger.info(f"[HTConfigTab] Scanning {len(js_files)} JS files for tab injection...")
    
    # 找到最大的JS文件（通常是主chunk，包Agent/Config/index.tsx?
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
    
    if not largest_file or largest_size < 100000:
        results["errors"].append(f"No suitable JS file found (largest: {largest_size} bytes)")
        return results
    
    try:
        with open(largest_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # 检查是否已经注
        if "HumanThinking: HT记忆配置 tab" in content:
            logger.info(f"[HTConfigTab] Already patched: {os.path.basename(largest_file)}")
            results["success"] = True
            return results
        
        # 查找 dynamicTabs 生成逻辑中的 memoryMapping 处理代码
        # 打包后的代码类似：const v=xa[T];if(v){const j=v.component;R.push({key:v.tabKey,label:...,children:...})}
        # 我们需要在这段代码后面注入额外tab
        
        # 模式1：查memoryMapping 处理代码（压缩后的变量名可能不同
        # 关键特征：xa[T] 或类似的后端映射查找
        memory_mapping_patterns = [
            # v1.1.4 打包后模式：const v=xa[T];if(v){const j=v.component;R.push({key:v.tabKey,...})}
            r'(const\s+\w+=\w+\[T\];if\(\w+\)\{const\s+\w+=\w+\.component;\w+\.push\(\{key:\w+\.tabKey,label:[^}]+\},children:[^}]+\}\)\}\))',
            # 更宽松的模式
            r'(\w+\.push\(\{key:\w+\.tabKey,label:[^}]*agentConfig\.\$\{\w+\.tabKey\}Title[^}]*\},children:[^}]+\}\)\}\))',
        ]
        
        patched = False
        for pattern in memory_mapping_patterns:
            match = re.search(pattern, content)
            if match:
                logger.info(f"[HTConfigTab] Found memoryMapping push code")
                original_code = match.group(1)
                
                # 注入额外HT记忆配置 tab
                # ?memoryBackend ?human_thinking 时，添加额外tab
                injection_code = '''
// HumanThinking: HT记忆配置 tab
(function(){
    // 检查当前是否为 human_thinking 后端
    var memoryBackend = (function(){
        try {
            var storage = sessionStorage.getItem('qwenpaw-agent-storage');
            if (storage) {
                var data = JSON.parse(storage);
                return data.state?.selectedAgent ? 'human_thinking' : 'remelight';
            }
        } catch(e) {}
        return 'remelight';
    })();
    
    if (memoryBackend === 'human_thinking' || true) {  // 总是添加，让前端控制显示
        // 添加 HT记忆配置 tab
        var htConfigTab = {
            key: "humanThinkingConfig",
            label: React.createElement("span", {className: "ht-tab-label"}, "HT记忆配置"),
            children: React.createElement("div", {className: "ht-tab-content"}, 
                React.createElement("div", {style: {padding: 16}},
                    React.createElement("h3", null, "HumanThinking 记忆配置"),
                    React.createElement("p", null, "此配置已移至侧边HumanThinking 记忆管理页面),
                    React.createElement("p", null, "请使用右侧侧边栏进行配置)
                )
            )
        };
        
        // 找到 tab 数组并添
        if (typeof R !== 'undefined' && Array.isArray(R)) {
            R.push(htConfigTab);
            console.log('[HumanThinking] ?Added HT记忆配置 tab');
        }
    }
})();
'''
                # 在原始代码后面添加注入代
                new_content = content.replace(original_code, original_code + injection_code)
                
                if new_content != content:
                    _make_backup(largest_file)
                    with open(largest_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    results["patched"].append(os.path.basename(largest_file))
                    results["success"] = True
                    patched = True
                    logger.info(f"[HTConfigTab] ?Patched: {os.path.basename(largest_file)}")
                    break
        
        if not patched:
            logger.warning(f"[HTConfigTab] Could not find memoryMapping pattern in {os.path.basename(largest_file)}")
            results["errors"].append("Could not find injection point")
            
    except Exception as e:
        results["errors"].append(str(e))
        logger.error(f"[HTConfigTab] Failed to patch: {e}", exc_info=True)
    
    return results


def patch_agent_config_refresh(qwenpaw_root: str) -> dict:
    """
    修补前端JS，添加agent切换时自动刷新配置的功能
    
    问题：原生UI的useAgentConfig hook在切换agent时不会重新加载配置，
    因为fetchConfig的依赖数组只有[form, t]，不包含selectedAgent?
    
    解决方案：注入一个全局的agent切换监听器，当检测到agent变化时，
    自动调用fetchConfig或刷新页面
    """
    results = {"success": False, "patched": [], "errors": []}
    
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)
    if not console_dir:
        results["errors"].append("Cannot find console directory")
        return results
    
    # 查找所有JS文件
    js_files = []
    for root, dirs, files in os.walk(console_dir):
        for f in files:
            if f.endswith(".js") and not f.endswith(".humanthinking.bak"):
                js_files.append(os.path.join(root, f))
    
    logger.info(f"[AgentRefresh] Scanning {len(js_files)} JS files for agent config refresh patch...")
    
    # 要注入的代码：监听sessionStorage变化，当agent切换时刷新配
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
                    // 方法2：刷新页面（兜底方案
                    window.location.reload();
                }
            }
        } catch(e) {}
    }, 500);
})();
'''
    
    # 找到最大的JS文件（通常是主chunk?
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
            
            # 检查是否已经注
            if "HumanThinking: Agent切换自动刷新配置" in content:
                logger.debug(f"[AgentRefresh] Already patched: {os.path.basename(largest_file)}")
                results["success"] = True
                return results
            
            _make_backup(largest_file)
            
            # 在文件末尾注入代
            new_content = content + "\n" + refresh_code
            
            with open(largest_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            results["patched"].append(os.path.basename(largest_file))
            logger.info(f"[AgentRefresh] ?Patched largest JS file: {os.path.basename(largest_file)} ({largest_size} bytes)")
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
    """installation HumanThinkingMemoryManager ?QwenPaw ?agents/tools 目录
    
    这是关键步骤——必须让 HumanThinkingMemoryManager 可以被正确导
    
    Args:
        qwenpaw_root: QwenPaw 根目
        plugin_dir: 插件目录路径（如果为 None，则qwenpaw_root 推导
    """
    results = {"success": False, "installed": False, "errors": [], "details": {}}
    
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
    except ImportError:
        results["errors"].append("Cannot import qwenpaw")
        return results
    
    target_dir = os.path.join(qwenpaw_pkg_dir, "agents", "tools", "HumanThinking")
    legacy_dir = os.path.join(qwenpaw_pkg_dir, "agents", "tools", "HumanThinkingMemoryManager")
    logger.info(f"Target installation directory: {target_dir}")
    
    if os.path.exists(legacy_dir) and not os.path.exists(target_dir):
        try:
            os.rename(legacy_dir, target_dir)
            logger.info(f"Renamed legacy directory: {legacy_dir} -> {target_dir}")
        except Exception as e:
            logger.warning(f"Failed to rename legacy directory: {e}")
    
    # 确定插件目录
    if plugin_dir is None:
        # 先尝试common paths
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
            results["errors"].append(f"Cannot find plugin directory，tried:: {possible_dirs}")
            return results
    
    if not os.path.isdir(plugin_dir):
        results["errors"].append(f"Plugin directory not found: {plugin_dir}")
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
    
    # 创建目标目录（只在 not found在时创建，避免触发 WatchFiles?
    try:
        if os.path.exists(target_dir):
            # 检查是否已经installation（跳过重复installation，避免触WatchFiles 热重载循环）
            marker_file = os.path.join(target_dir, ".ht_installed")
            if os.path.exists(marker_file):
                with open(marker_file, "r", encoding="utf-8") as f:
                    marker_content = f.read().strip()
                
                # 标记文件记录installation时间，如果超24 小时则重新安
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
        results["errors"].append(f"Failed to create target directory: {e}")
        return results
    
    # 复制目录
    items_to_copy = [
        ("core", source_core),
        ("search", source_search),
        ("hooks", source_hooks),
        ("utils", source_utils),
        ("api", os.path.join(plugin_dir, "api")),
        ("locales", os.path.join(plugin_dir, "locales")),
    ]
    
    files_to_copy = [
        ("__init__.py", source_init),
        ("frontend.js", os.path.join(plugin_dir, "frontend.js")),
        ("prod_ui_patcher.py", os.path.join(plugin_dir, "prod_ui_patcher.py")),
        ("plugin.json", os.path.join(plugin_dir, "plugin.json")),
        ("AGENT.md", os.path.join(plugin_dir, "AGENT.md")),
    ]
    
    for name, source in items_to_copy:
        if os.path.isdir(source):
            target = os.path.join(target_dir, name)
            try:
                if os.path.exists(target):
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                logger.info(f"  ?Copied {name}/")
                results["details"][name] = "copied"
            except Exception as e:
                results["errors"].append(f"Copy {name}/ 失败: {e}")
        else:
            logger.warning(f"  ?Source {name}/ not found, skipping")
            results["details"][name] = "not_found"
    
    # 复制 __init__.py
    if os.path.isfile(source_init):
        target_init = os.path.join(target_dir, "__init__.py")
        try:
            shutil.copy2(source_init, target_init)
            logger.info(f"  ?Copied __init__.py")
            results["details"]["__init__.py"] = "copied"
        except Exception as e:
            results["errors"].append(f"Copy __init__.py 失败: {e}")
    else:
        target_init = os.path.join(target_dir, "__init__.py")
        try:
            with open(target_init, "w") as f:
                f.write("# HumanThinking Memory Manager\n")
            logger.info(f"  ?Created basic __init__.py")
            results["details"]["__init__.py"] = "created"
        except Exception as e:
            results["errors"].append(f"创建 __init__.py 失败: {e}")
    
    for name, source in files_to_copy:
        if name == "__init__.py":
            continue
        if os.path.isfile(source):
            target_file = os.path.join(target_dir, name)
            try:
                shutil.copy2(source, target_file)
                logger.info(f"  ?Copied {name}")
                results["details"][name] = "copied"
            except Exception as e:
                results["errors"].append(f"Copy {name} 失败: {e}")
        else:
            logger.warning(f"  ?Source {name} not found, skipping")
            results["details"][name] = "not_found"
    
    # 验证installation
    memory_manager_file = os.path.join(target_dir, "core", "memory_manager.py")
    if os.path.isfile(memory_manager_file):
        logger.info(f"  ?Installation verified: core/memory_manager.py exists")
        results["success"] = True
        results["installed"] = True
        
        # 创建installation标记文件（避免下次启动重复installation触WatchFiles?
        import time
        marker_file = os.path.join(target_dir, ".ht_installed")
        try:
            with open(marker_file, "w", encoding="utf-8") as f:
                f.write(str(time.time()))
            logger.info(f"  ?Installation marker created: {marker_file}")
        except Exception as e:
            logger.warning(f"  ?Failed to create installation marker: {e}")
        
        # installation successful功后，修补 plugins.py 添加 API 路由
        logger.info("  ?Patching plugins.py for API routes...")
        router_result = patch_plugins_router(qwenpaw_root)
        if router_result.get("success"):
            logger.info(f"  ?Plugins router patched: {router_result.get('patched', False)}")
        else:
            logger.warning(f"  ?Plugins router patch failed: {router_result.get('errors', [])}")
    else:
        results["errors"].append("Installation verification failed: core/memory_manager.py not found")
    
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
        results["errors"].append("Cannot import qwenpaw")
        return results
    
    workspace_file = os.path.join(qwenpaw_pkg_dir, "app", "workspace", "workspace.py")
    if not os.path.isfile(workspace_file):
        results["errors"].append(f"workspace.py not found: {workspace_file}")
        return results
    
    try:
        with open(workspace_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经修
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
                    logger.info(f"  ?Added config_key")
            return results
        
        _make_backup(workspace_file)
        logger.info(f"Patching workspace.py to support human_thinking...")
        
        # 1. 添加 HumanThinkingMemoryManager 导入
        old_import = 'from ...agents.memory import ReMeLightMemoryManager'
        new_imports = '''from ...agents.memory import ReMeLightMemoryManager
    from ...agents.tools.HumanThinking.core.memory_manager import HumanThinkingMemoryManager'''
        
        if old_import in content:
            content = content.replace(old_import, new_imports)
            logger.info(f"  ?Added HumanThinkingMemoryManager import")
        else:
            logger.warning(f"  ?Could not find ReMeLightMemoryManager import")
            results["errors"].append("Not foundReMeLightMemoryManager 导入")
        
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
            results["errors"].append("Not found到 remelight 分支")
        
        # 3. 添加 config_key ?ConfigurationException
        if 'config_key="memory_manager_backend"' not in content:
            old_exception = 'message=f"Unsupported memory manager backend: \'{backend}\'",\n    )'
            new_exception = 'message=f"Unsupported memory manager backend: \'{backend}\'",\n        config_key="memory_manager_backend",\n    )'
            if old_exception in content:
                content = content.replace(old_exception, new_exception)
                logger.info(f"  ?Added config_key to ConfigurationException")
            else:
                logger.warning(f"  ?Could not find ConfigurationException pattern")
        
        # 写入文件
        if content:
            with open(workspace_file, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"?workspace.py patched successfully")
            results["success"] = True
            results["patched"] = True
    
    except Exception as e:
        logger.error(f"Failed to patch workspace.py: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def patch_backend_config(qwenpaw_root: str) -> dict:
    """修改后端配置，使 memory_manager_backend 接受 human_thinking
    
    服务器上installationQwenPaw 版本中，config.py ?memory_manager_backend 
    类型定义Literal["remelight"]，需要改Literal["remelight", "human_thinking"]
    """
    results = {"success": True, "patched_files": [], "errors": []}
    
    try:
        import qwenpaw
        qwenpaw_pkg_dir = os.path.dirname(qwenpaw.__file__)
    except ImportError:
        results["success"] = False
        results["errors"].append("Cannot import qwenpaw")
        return results
    
    config_dir = os.path.join(qwenpaw_pkg_dir, "config")
    if not os.path.isdir(config_dir):
        results["success"] = False
        results["errors"].append(f"Config directory not found: {config_dir}")
        return results
    
    logger.info(f"Patching backend config in: {config_dir}")
    
    # 查找 config.py 文件
    config_file = os.path.join(config_dir, "config.py")
    if not os.path.isfile(config_file):
        results["success"] = False
        results["errors"].append(f"config.py not found: {config_file}")
        return results
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查是否已经包human_thinking
        if 'human_thinking' in content and 'memory_manager_backend' in content:
            # 验证是否是正确的格式
            if 'Literal["remelight", "human_thinking"]' in content or "Literal['remelight', 'human_thinking']" in content:
                logger.info(f"Backend config already patched: {config_file}")
                results["patched_files"].append(os.path.basename(config_file))
                return results
        
        # 查找 memory_manager_backend ?Literal 定义
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
            
            # 替换为包human_thinking 的版
            new_content = content.replace(
                'Literal["remelight"]',
                'Literal["remelight", "human_thinking"]'
            )
            
            if new_content != content:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                logger.info(f"?Patched backend config: {config_file}")
                logger.info(f"  Changed: Literal['remelight'] -> Literal['remelight', 'human_thinking']")
                results["patched_files"].append(os.path.basename(config_file))
                
                # ====== 关键：强制重新加载模======
                # 修改磁盘文件后，需要强制重新加载模块才能让运行时生
                try:
                    import qwenpaw.config.config as config_module
                    import sys
                    
                    # ?sys.modules 中移除，然后重新导入
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
                    
                    logger.info("  ?Reloaded qwenpaw.config.config module")
                except Exception as e:
                    logger.warning(f"  ?Failed to reload module: {e}")
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
                logger.info(f"?Patched backend config: {config_file}")
                results["patched_files"].append(os.path.basename(config_file))
        
        else:
            # 可能已经是多Literal 或者格式不
            logger.warning(f"Could not find Literal['remelight'] pattern in config.py")
            logger.warning(f"  memory_manager_backend may already support multiple values")
            logger.warning(f"  Or the format is different than expected")
            
            # 搜索 memory_manager_backend 附近的上下文
            mmb_idx = content.find("memory_manager_backend")
            if mmb_idx >= 0:
                start = max(0, mmb_idx - 50)
                end = min(len(content), mmb_idx + 300)
                logger.info(f"  Context: {content[start:end]}")
            
            results["errors"].append("Not foundLiteral['remelight'] 模式")
    
    except Exception as e:
        logger.error(f"Failed to patch backend config: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def patch_runtime_config_model() -> dict:
    """修补运行时内存中Pydantic 模型，使其接human_thinking
    
    关键问题：即使修改了磁盘上的 config.py 文件，Python 进程已经在内存中
    缓存了旧AgentsRunningConfig 类定义。Pydantic 验证使用的是内存中的
    类定义，所以必须同时修补内存中的模型
    
    修补方式
    1. 修改 __annotations__ 中的 Literal 类型定义
    2. 同步更新 model_fields
    3. 清理 Pydantic 内部缓存（核心！?
    4. 调用 model_rebuild() 重新构建模型
    """
    results = {"success": False, "patched": False, "errors": []}
    
    try:
        import qwenpaw.config.config
        from qwenpaw.config.config import AgentsRunningConfig
        from typing import Literal, get_args
        import pydantic
        
        # 检查当前类型定
        current_annotation = AgentsRunningConfig.__annotations__.get('memory_manager_backend')
        current_args = get_args(current_annotation) if hasattr(current_annotation, '__args__') else ()
        
        if 'human_thinking' in current_args:
            logger.info("Runtime AgentsRunningConfig already accepts human_thinking")
            results["success"] = True
            results["patched"] = True
            return results
        
        logger.info(f"Current memory_manager_backend Literal values: {current_args}")
        logger.info("Patching runtime AgentsRunningConfig.__annotations__...")
        
        # 核心修补：直接修__annotations__
        new_literal = Literal["remelight", "human_thinking"]
        qwenpaw.config.config.AgentsRunningConfig.__annotations__['memory_manager_backend'] = new_literal
        AgentsRunningConfig.__annotations__['memory_manager_backend'] = new_literal
        
        # 同步更新 model_fields（Pydantic v2 运行时）
        field = AgentsRunningConfig.model_fields.get('memory_manager_backend')
        if field is not None:
            field.annotation = new_literal
            logger.info(f"Patched model_fields['memory_manager_backend'].annotation = {new_literal}")
            if field.default == "remelight":
                field.default = "human_thinking"
                logger.info(f"Changed default memory_manager_backend: 'remelight' -> 'human_thinking'")
        
        # ========== 关键：清Pydantic 内部缓存 ==========
        # Pydantic 会在模块加载时缓validator，即使修改了 __annotations__
        # 也需要清理这些缓存才能让新的 Literal 值生
        
        try:
            # 清理模型级别的缓
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
                logger.info(f"?Runtime AgentsRunningConfig patched successfully")
                logger.info(f"  New Literal values: {field_args}")
                results["success"] = True
                results["patched"] = True
            else:
                results["errors"].append(f"Verification failed: human_thinking not in Literal after patch, got {field_args}")
                logger.warning(f"?Runtime patch verification failed, field_args: {field_args}")
        else:
            results["errors"].append("model_fields verification failed")
            logger.warning(f"?Cannot find memory_manager_backend in model_fields")
    
    except Exception as e:
        logger.error(f"Failed to patch runtime config model: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


def inject_persistent_config() -> dict:
    """注入 QwenPaw 持久配置：memory_manager_backend + auto_memory_interval
    
    1. memory_manager_backend → "human_thinking"（全局 config.json）
    2. auto_memory_interval → 3（每个 agent 的 agent.json，per-agent 独立配置）
    
    配合 inject_registry_preload()，需要重启两次生效。
    """
    import json
    import os
    import glob as glob_mod
    
    result = {"success": True, "injected": False, "changes": [], "errors": []}
    
    # ── 1. 注入全局 memory_manager_backend ──
    config_path = "/root/.qwenpaw/config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
            
            agents = config.get("agents", {})
            running = agents.get("running", {})
            
            backend_current = running.get("memory_manager_backend")
            if backend_current != "human_thinking":
                running["memory_manager_backend"] = "human_thinking"
                if "agents" not in config:
                    config["agents"] = {}
                config["agents"]["running"] = running
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                result["changes"].append(f"memory_manager_backend: {backend_current} -> human_thinking")
                result["injected"] = True
                logger.info(f"Persistent config: memory_manager_backend -> human_thinking")
        except Exception as e:
            result["errors"].append(f"config.json: {e}")
            logger.error(f"Failed to inject memory_manager_backend: {e}")
    
    # ── 2. 注入每个 agent 的 auto_memory_interval ──
    agent_json_pattern = "/root/.qwenpaw/workspaces/*/agent.json"
    agent_files = glob_mod.glob(agent_json_pattern)
    
    if not agent_files:
        result["errors"].append("No agent.json files found")
        logger.warning("No agent.json files found for auto_memory_interval injection")
        return result
    
    for agent_path in agent_files:
        try:
            agent_name = agent_path.split("/")[-2]
            with open(agent_path, "r") as f:
                agent_config = json.load(f)
            
            running = agent_config.get("running", {})
            rlmc = running.get("reme_light_memory_config", {})
            if not isinstance(rlmc, dict):
                rlmc = {}
            
            interval_current = rlmc.get("auto_memory_interval")
            if interval_current is None or interval_current <= 0:
                if "running" not in agent_config:
                    agent_config["running"] = {}
                if "reme_light_memory_config" not in agent_config["running"]:
                    agent_config["running"]["reme_light_memory_config"] = {}
                agent_config["running"]["reme_light_memory_config"]["auto_memory_interval"] = 3
                
                with open(agent_path, "w") as f:
                    json.dump(agent_config, f, indent=2, ensure_ascii=False)
                
                result["changes"].append(f"agent[{agent_name}] auto_memory_interval: {interval_current} -> 3")
                result["injected"] = True
                logger.info(f"agent.json [{agent_name}]: auto_memory_interval -> 3")
        except Exception as e:
            result["errors"].append(f"agent.json {agent_path}: {e}")
            logger.error(f"Failed to inject auto_memory_interval for {agent_path}: {e}")
    
    if not result["changes"]:
        result["message"] = "All config values already correct, no change needed"
    
    return result


def inject_registry_preload() -> dict:
    """注入 registry 预加载：创建 sitecustomize.py 在 Agent 创建前注册 human_thinking
    
    在 QwenPaw 虚拟环境的 site-packages 中创建 sitecustomize.py，
    Python 解释器在导入任何模块之前会自动执行它。
    这样 @memory_registry.register("human_thinking") 在 Agent 创建之前就已执行。
    """
    import os
    
    sitecustomize_content = """# Auto-generated by HumanThinking plugin - DO NOT EDIT
# Pre-registers HumanThinking in memory_registry before QwenPaw agents are created.
try:
    from qwenpaw.agents.tools.HumanThinking.core.memory_manager import HumanThinkingMemoryManager  # noqa: F401
except ImportError:
    pass
"""
    
    # 找到 venv 的 site-packages 路径
    candidates = [
        "/root/.qwenpaw/venv/lib/python3.12/site-packages/sitecustomize.py",
    ]
    
    try:
        import site
        for sp in site.getsitepackages():
            if "qwenpaw" in sp or "venv" in sp:
                candidates.append(os.path.join(sp, "sitecustomize.py"))
    except Exception:
        pass
    
    injected_paths = []
    for path in candidates:
        dirname = os.path.dirname(path)
        if not os.path.isdir(dirname):
            continue
        try:
            with open(path, "w") as f:
                f.write(sitecustomize_content)
            injected_paths.append(path)
        except Exception as e:
            logger.warning(f"Failed to write sitecustomize.py to {path}: {e}")
    
    if injected_paths:
        logger.info(f"Registry preload injected: sitecustomize.py -> {injected_paths}")
        return {"success": True, "injected": True, "paths": injected_paths}
    else:
        return {"success": False, "injected": False, "error": "No writable site-packages found"}


def patch_production_ui(qwenpaw_root: str) -> dict:
    """
    修改生产环境的前端文

    Args:
        qwenpaw_root: QwenPaw 根目

    Returns:
        修改结果
    """
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)

    if not console_dir:
        return {
            "success": False,
            "error": "Cannot find QwenPaw console static directory",
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
        results["error"] = "Not found到包remelight 选项对象JS 文件"
    
    # 注入 frontend.js 脚本到 index.html（核心：加载完整的HT Config UI）
    logger.info("[patch_production_ui] Injecting frontend.js into index.html...")
    index_result = patch_index_html(qwenpaw_root)
    if index_result.get("success"):
        logger.info("[patch_production_ui] ✓ frontend.js injected into index.html")
        results["frontend_injected"] = True
    else:
        logger.warning(f"[patch_production_ui] ✗ index.html injection failed: {index_result.get('errors', [])}")

    # 额外注入 HT记忆配置 tab
    logger.info("[patch_production_ui] Injecting HT记忆配置 tab...")
    ht_result = patch_human_thinking_config_tab(qwenpaw_root)
    if ht_result.get("success"):
        logger.info("[patch_production_ui] ✓ HT记忆配置 tab injected")
    else:
        logger.warning(f"[patch_production_ui] ✗ HT记忆配置 tab injection failed: {ht_result.get('errors', [])}")

    # 修改注释文字：记忆管理器的后端类型，目前only when支remelight -> 记忆管理器的后端类型，目前可支持 remelight ?HumanThinking
    logger.info("[patch_production_ui] Updating tooltip text...")
    tooltip_result = patch_memory_manager_tooltip(js_files)
    if tooltip_result.get("success"):
        logger.info("[patch_production_ui] ?Tooltip text updated")
    else:
        logger.warning(f"[patch_production_ui] ?Tooltip update failed: {tooltip_result.get('errors', [])}")
    
    # 确保 xa 映射表中包含 human_thinking
    logger.info("[patch_production_ui] Ensuring xa mapping has human_thinking...")
    xa_result = ensure_xa_human_thinking(js_files)
    if xa_result.get("success"):
        logger.info("[patch_production_ui] ?xa mapping verified")
    else:
        logger.warning(f"[patch_production_ui] ?xa mapping fix failed: {xa_result.get('errors', [])}")

    return results


def patch_memory_manager_tooltip(js_files: list) -> dict:
    """
    修改前端 JS 中的注释文字
    "记忆管理器的后端类型，目前only when支持 remelight" -> "记忆管理器的后端类型，目前可支持 remelight ?HumanThinking"
    """
    results = {"success": False, "patched": [], "errors": []}
    
    old_text = "记忆管理器的后端类型，目前仅支持 remelight"
    new_text = "记忆管理器的后端类型，目前可支持 remelight和HumanThinking"
    
    patched_count = 0
    for js_file in js_files:
        try:
            with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            if old_text in content:
                new_content = content.replace(old_text, new_text)
                if new_content != content:
                    _make_backup(js_file)
                    with open(js_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    results["patched"].append(os.path.basename(js_file))
                    patched_count += 1
                    logger.info(f"  ?Updated tooltip in {os.path.basename(js_file)}")
        except Exception as e:
            results["errors"].append(str(e))
    
    if patched_count > 0:
        results["success"] = True
    
    return results


def ensure_xa_human_thinking(js_files: list) -> dict:
    """
    确保 xa 映射表中包含 human_thinking 条目
    
    问题：QwenPaw 启动时可能会从备份恢JS 文件，导human_thinking 丢失
    解决方案：直接检查并修复 xa 映射表
    """
    results = {"success": False, "patched": [], "errors": []}
    
    for js_file in js_files:
        try:
            with open(js_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # 查找 xa= 映射
            match = re.search(r'xa=\{[^}]*\}', content)
            if match:
                old_mapping = match.group()
                
                # 检查是否已包含 human_thinking
                if 'human_thinking' not in old_mapping:
                    # 提取 remelight ?configField ?component
                    reme_match = re.search(r'remelight:\{([^}]+)\}', old_mapping)
                    if reme_match:
                        reme_content = reme_match.group(1)
                        # 构建 human_thinking 映射
                        ht_mapping = f'human_thinking:{{{reme_content}}}'
                        # ?remelight 后添human_thinking
                        new_mapping = old_mapping.replace(
                            f'remelight:{{{reme_content}}}',
                            f'remelight:{{{reme_content}}},{ht_mapping}'
                        )
                        
                        if new_mapping != old_mapping:
                            content = content.replace(old_mapping, new_mapping)
                            with open(js_file, "w", encoding="utf-8") as f:
                                f.write(content)
                            results["patched"].append(os.path.basename(js_file))
                            results["success"] = True
                            logger.info(f"  ?Added human_thinking to xa in {os.path.basename(js_file)}")
                            break
        except Exception as e:
            results["errors"].append(str(e))
    
    return results


def patch_plugins_router(qwenpaw_root: str) -> dict:
    """
    修改 plugins.py 添加 HumanThinking API 路由
    
    由于 QwenPaw 不支持插件动态注API 路由
    我们需要直接修plugins.py 文件来添加我们的路由
    """
    results = {"success": False, "patched": False, "errors": []}
    
    try:
        plugins_py = None
        search_paths = [
            os.path.join(qwenpaw_root, "app", "routers", "plugins.py"),
            os.path.join(qwenpaw_root, "site-packages", "qwenpaw", "app", "routers", "plugins.py"),
            os.path.join(qwenpaw_root, "venv", "lib", "python3.12", "site-packages", "qwenpaw", "app", "routers", "plugins.py"),
        ]
        for p in search_paths:
            if os.path.isfile(p):
                plugins_py = p
                break
        
        if not plugins_py:
            results["errors"].append(f"plugins.py not found in: {search_paths}")
            return results
        
        with open(plugins_py, "r", encoding="utf-8") as f:
            content = f.read()
        
        begin_marker = "# ── HumanThinking Plugin Routes [BEGIN"
        end_marker = "# ── HumanThinking Plugin Routes [END"
        
        if begin_marker in content:
            start_idx = content.find(begin_marker)
            end_idx = content.find(end_marker)
            if end_idx > start_idx:
                end_idx = content.find("\n", end_idx) + 1
                content = content[:start_idx] + content[end_idx:]
                logger.info("[PluginsRouter] Removed old marked HumanThinking routes block")
        
        bak_file = plugins_py + ".humanthinking.bak"
        if "/humanthinking/" in content and begin_marker not in content:
            if os.path.isfile(bak_file):
                with open(bak_file, "r", encoding="utf-8") as bf:
                    content = bf.read()
                logger.info("[PluginsRouter] Restored from backup to remove old inline routes")
            else:
                while True:
                    idx = content.find("@router.")
                    if idx == -1:
                        break
                    route_line_end = content.find("\n", idx)
                    route_line = content[idx:route_line_end]
                    if '"/humanthinking/' in route_line:
                        func_start = content.find("async def ", route_line_end)
                        if func_start == -1 or func_start > route_line_end + 200:
                            break
                        func_name_end = content.find("(", func_start)
                        func_name = content[func_start:func_name_end]
                        next_router = content.find("\n@router.", func_start)
                        next_class = content.find("\nclass ", func_start)
                        next_marker = content.find("\n# ──", func_start)
                        end_pos = len(content)
                        for pos in [next_router, next_class, next_marker]:
                            if pos > func_start and (pos < end_pos):
                                end_pos = pos
                        content = content[:idx] + content[end_pos:]
                    else:
                        break
        
        _make_backup(plugins_py)
        
        logger.info("[PluginsRouter] HumanThinking routes now handled by plugin.py include_router, skipping injection")
        with open(plugins_py, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "patched": False, "note": "Routes handled by plugin.py include_router"}
    except Exception as e:
        results["errors"].append(str(e))
        logger.error(f"[PluginsRouter] Failed to patch plugins.py: {e}", exc_info=True)
    
    return results


def restore_production_ui(qwenpaw_root: str) -> dict:
    """恢复生产环境的前端文"""
    console_dir = find_qwenpaw_console_static_dir(qwenpaw_root)

    if not console_dir:
        return {"success": False, "error": "Cannot find console directory"}

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


def ensure_memory_registry_registration() -> dict:
    """确保 human_thinking 已注册到 memory_registry
    
    这是一个防御性函数，作为 @memory_registry.register 装饰器的补充。
    如果由于某种原因装饰器未触发，此函数会显式检查并注册。
    
    Returns:
        dict: {success: bool, registered: bool, backends: list, message: str}
    """
    try:
        from qwenpaw.agents.memory.base_memory_manager import memory_registry
        
        # 检查当前注册列表
        registered = memory_registry.list_registered()
        
        if "human_thinking" in registered:
            logger.info(
                f"[RegistryGuard] human_thinking already registered. "
                f"Backends: {registered}"
            )
            return {
                "success": True,
                "registered": True,
                "already_registered": True,
                "backends": registered,
                "message": "human_thinking was already registered"
            }
        
        # 未注册 → 尝试导入模块触发装饰器
        logger.info("[RegistryGuard] human_thinking not found in registry, importing module...")
        
        try:
            from qwenpaw.agents.tools.HumanThinking.core.memory_manager import HumanThinkingMemoryManager
            registered = memory_registry.list_registered()
            
            if "human_thinking" in registered:
                logger.info(f"[RegistryGuard] Registered via import. Backends: {registered}")
                return {
                    "success": True,
                    "registered": True,
                    "already_registered": False,
                    "backends": registered,
                    "message": "human_thinking registered via module import"
                }
            else:
                # 装饰器未生效 → 尝试手动注册
                logger.warning("[RegistryGuard] Decorator didn't register, trying manual registration...")
                memory_registry.register("human_thinking")(HumanThinkingMemoryManager)
                registered = memory_registry.list_registered()
                
                if "human_thinking" in registered:
                    logger.info(f"[RegistryGuard] Manually registered. Backends: {registered}")
                    return {
                        "success": True,
                        "registered": True,
                        "already_registered": False,
                        "manual_register": True,
                        "backends": registered,
                        "message": "human_thinking manually registered"
                    }
                else:
                    logger.error("[RegistryGuard] All registration attempts failed!")
                    return {
                        "success": False,
                        "registered": False,
                        "backends": registered,
                        "message": "Failed to register human_thinking"
                    }
        except ImportError as ie:
            logger.error(f"[RegistryGuard] Cannot import HumanThinkingMemoryManager: {ie}")
            return {
                "success": False,
                "registered": False,
                "backends": registered,
                "message": f"Import failed: {ie}"
            }
    except Exception as e:
        logger.error(f"[RegistryGuard] Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "registered": False,
            "backends": [],
            "message": str(e)
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python prod_ui_patcher.py <qwenpaw_root> [--patch-plugins-router|--restore]")
        sys.exit(1)

    qwenpaw_root = sys.argv[1]

    if len(sys.argv) > 2 and sys.argv[2] == "--restore":
        result = restore_production_ui(qwenpaw_root)
        print(f"Restore result: {result}")
    elif len(sys.argv) > 2 and sys.argv[2] == "--patch-plugins-router":
        result = patch_plugins_router(qwenpaw_root)
        print(f"Plugins router patch result: {result}")
    else:
        result = patch_production_ui(qwenpaw_root)
        print(f"Patch result: {result}")
