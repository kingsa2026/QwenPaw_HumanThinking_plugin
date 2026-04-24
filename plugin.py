# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - QwenPaw Plugin Entry Point

v1.0.0-beta0.1 - 解决 QwenPaw Agent 跨Session认知与情感连续性问题
"""

from qwenpaw.plugins.api import PluginApi
import logging
import os
import sys
import json
from pathlib import Path

# Use "qwenpaw" namespace so logs are captured by QwenPaw's logging system
logger = logging.getLogger("qwenpaw.humanthinking")

CONFIG_KEY = 'humanthinking_config'
BACKUP_CONFIG_KEY = 'humanthinking_backup_config'
SLEEP_CONFIG_KEY = 'humanthinking_sleep_config'


def load_backup_config() -> dict:
    """加载备份配置"""
    try:
        config_path = Path.home() / ".qwenpaw" / "config" / f"{BACKUP_CONFIG_KEY}.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load backup config: {e}")
    
    return {"auto_backup_enabled": False, "auto_backup_interval_hours": 24}


def load_humanthinking_config() -> dict:
    """加载记忆设置配置"""
    try:
        config_path = Path.home() / ".qwenpaw" / "config" / f"{CONFIG_KEY}.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load humanthinking config: {e}")
    
    return {}


def load_sleep_config() -> dict:
    """加载睡眠配置"""
    try:
        config_path = Path.home() / ".qwenpaw" / "config" / f"{SLEEP_CONFIG_KEY}.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load sleep config: {e}")
    
    return {
        "enable_agent_sleep": True,
        "sleep_idle_hours": 2,
        "auto_consolidate": True,
        "consolidate_interval_hours": 6,
    }


class HumanThinkingMemoryPlugin:
    """HumanThinking Memory Manager Plugin."""

    def register(self, api: PluginApi):
        """注册插件到 QwenPaw

        Args:
            api: PluginApi instance
        """
        logger.info("=" * 60)
        logger.info("Registering HumanThinking Memory Manager v1.0.0-beta0.1...")
        logger.info(f"Plugin module: {__name__}")
        logger.info(f"Plugin file: {__file__}")

        try:
            # 获取 QwenPaw 根目录
            logger.info("Searching for QwenPaw root...")
            qwenpaw_root = self._find_qwenpaw_root()

            if qwenpaw_root:
                logger.info(f"QwenPaw root found: {qwenpaw_root}")
                # 注入 UI 修改（仅在 console 目录存在时）
                logger.info("Attempting UI injection...")
                ui_injected = self._inject_ui(qwenpaw_root)
                logger.info(f"UI injection result: {'✓ SUCCESS' if ui_injected else '✗ FAILED'}")
            else:
                logger.warning("QwenPaw root not found, skipping UI injection")
                logger.warning("This means HumanThinking option will NOT appear in the dropdown")

            # 注册启动钩子 - 初始化记忆管理器
            logger.info("Registering startup hook 'human_thinking_init'...")
            api.register_startup_hook(
                hook_name="human_thinking_init",
                callback=self._startup_hook,
                priority=10,
            )
            logger.info("✓ Startup hook registered")

            # 注册关闭钩子 - 清理记忆管理器
            logger.info("Registering shutdown hook 'human_thinking_cleanup'...")
            api.register_shutdown_hook(
                hook_name="human_thinking_cleanup",
                callback=self._shutdown_hook,
                priority=10,
            )
            logger.info("✓ Shutdown hook registered")

            # 注册 API 路由
            logger.info("Registering API routes...")
            try:
                from .api.routes import router as ht_router
                api.register_router(ht_router)
                logger.info("✓ API routes registered")
            except Exception as e:
                logger.warning(f"Failed to register API routes: {e}")

            logger.info("=" * 60)
            logger.info("✓ HumanThinking Memory Manager registered")
            logger.info(f"  - UI Injection: {'✓ Yes' if qwenpaw_root else '✗ No (QwenPaw root not found)'}")
            logger.info(f"  - Startup Hook: ✓ Yes")
            logger.info(f"  - Shutdown Hook: ✓ Yes")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(
                f"Failed to register HumanThinking Memory Manager: {e}",
                exc_info=True,
            )

    def _find_qwenpaw_root(self) -> str:
        """查找 QwenPaw 根目录"""
        # 方法1：从当前模块路径推导
        try:
            import qwenpaw
            qwenpaw_file = qwenpaw.__file__
            logger.info(f"Found qwenpaw package at: {qwenpaw_file}")
            if qwenpaw_file:
                # /path/to/qwenpaw/src/qwenpaw/__init__.py -> /path/to/qwenpaw
                root = os.path.dirname(os.path.dirname(os.path.dirname(qwenpaw_file)))
                logger.info(f"Derived QwenPaw root: {root}")
                return root
        except ImportError as e:
            logger.warning(f"Cannot import qwenpaw package: {e}")

        # 方法2：检查常见路径
        common_paths = [
            os.path.expanduser("~/.qwenpaw"),
            "/root/.qwenpaw",
            "/opt/QwenPaw",
        ]

        for path in common_paths:
            if os.path.isdir(path) and os.path.isdir(os.path.join(path, "console")):
                logger.info(f"Found QwenPaw root at common path: {path}")
                return path

        logger.warning(f"QwenPaw root not found. Searched paths: {common_paths}")
        return ""

    def _inject_ui(self, qwenpaw_root: str) -> bool:
        """注入 UI 修改（优先生产环境 patcher，其次开发环境 injector）"""
        try:
            logger.info("=" * 60)
            logger.info("Starting UI injection process...")
            logger.info(f"QwenPaw root: {qwenpaw_root}")
            
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Plugin directory: {plugin_dir}")
            logger.info(f"Attempting UI injection for QwenPaw root: {qwenpaw_root}")

            # 优先尝试生产环境 patcher（修改打包后的 JS 文件）
            patcher_path = os.path.join(plugin_dir, "prod_ui_patcher.py")
            logger.info(f"Looking for production patcher at: {patcher_path}")
            logger.info(f"Patcher file exists: {os.path.exists(patcher_path)}")
            
            if os.path.exists(patcher_path):
                logger.info("Found prod_ui_patcher.py, attempting production UI patch...")
                import importlib.util
                logger.info("Loading prod_ui_patcher module...")
                spec = importlib.util.spec_from_file_location("prod_ui_patcher", patcher_path)
                patcher_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(patcher_module)
                logger.info("Prod UI patcher module loaded successfully")

                # Step 1: 安装 HumanThinkingMemoryManager 到 QwenPaw
                logger.info("Step 1: Installing HumanThinkingMemoryManager to QwenPaw...")
                install_result = patcher_module.install_human_thinking_to_qwenpaw(
                    qwenpaw_root=qwenpaw_root,
                    plugin_dir=plugin_dir  # 使用已知的插件目录路径
                )
                logger.info(f"Install result: {install_result}")
                if install_result.get("success"):
                    logger.info("  ✓ HumanThinkingMemoryManager installed successfully")
                else:
                    for err in install_result.get("errors", []):
                        logger.warning(f"  ✗ Install error: {err}")
                    logger.warning("  HumanThinkingMemoryManager not installed - 'human_thinking' backend will fail")

                # Step 2: 修复 workspace.py 中的 ConfigurationException
                logger.info("Step 2: Patching workspace.py error handling...")
                workspace_result = patcher_module.patch_workspace_import(qwenpaw_root)
                logger.info(f"Workspace patch result: {workspace_result}")
                if workspace_result.get("success"):
                    logger.info("  ✓ workspace.py patched successfully")
                else:
                    for err in workspace_result.get("errors", []):
                        logger.warning(f"  ✗ Workspace patch error: {err}")

                # Step 3: 修补后端配置（使 memory_manager_backend 接受 human_thinking）
                logger.info("Step 3: Patching backend config (Literal type)...")
                backend_result = patcher_module.patch_backend_config(qwenpaw_root)
                logger.info(f"Backend config patch result: {backend_result}")
                if backend_result.get("success"):
                    for fname in backend_result.get("patched_files", []):
                        logger.info(f"  ✓ Backend config patched: {fname}")
                else:
                    for err in backend_result.get("errors", []):
                        logger.warning(f"  ✗ Backend config patch error: {err}")

                # Step 3.5: 修补运行时内存中的 Pydantic 模型（关键！）
                # 即使修改了磁盘上的 config.py，Python 进程已经在内存中缓存了旧的类定义
                # 必须同时修补内存中的模型，否则 Pydantic 验证会拒绝 "human_thinking"
                logger.info("Step 3.5: Patching runtime Pydantic model (in-memory)...")
                runtime_result = patcher_module.patch_runtime_config_model()
                logger.info(f"Runtime model patch result: {runtime_result}")
                if runtime_result.get("success"):
                    logger.info("  ✓ Runtime AgentsRunningConfig patched to accept human_thinking")
                else:
                    for err in runtime_result.get("errors", []):
                        logger.warning(f"  ✗ Runtime model patch error: {err}")
                    logger.warning("  UI save may reject 'human_thinking' value!")

                # Step 4: 修补前端 JS（添加 HumanThinking 下拉选项）
                logger.info("Step 4: Patching frontend JS (dropdown options)...")
                result = patcher_module.patch_production_ui(qwenpaw_root)
                logger.info(f"Production patcher result: {result}")

                if result.get("success"):
                    logger.info("✓ Production UI patched successfully")
                    patched = result.get("patched_files", [])
                    logger.info(f"Patched {len(patched)} file(s):")
                    for fname in patched:
                        logger.info(f"  ✓ {fname}")
                else:
                    logger.warning(f"Production patcher failed: {result.get('error', 'unknown')}")

                # Step 5: 修补前端 JS（添加agent切换自动刷新配置功能）
                logger.info("Step 5: Patching frontend JS (agent config refresh on switch)...")
                refresh_result = patcher_module.patch_agent_config_refresh(qwenpaw_root)
                logger.info(f"Agent refresh patch result: {refresh_result}")
                
                if refresh_result.get("success"):
                    logger.info("✓ Agent config refresh patch applied successfully")
                    for fname in refresh_result.get("patched", []):
                        logger.info(f"  ✓ {fname}")
                else:
                    for err in refresh_result.get("errors", []):
                        logger.warning(f"  ✗ Agent refresh patch error: {err}")

                # Step 6: 修补 plugins.py 添加 API 路由
                logger.info("Step 6: Patching plugins.py (API routes)...")
                router_result = patcher_module.patch_plugins_router(qwenpaw_root)
                logger.info(f"Plugins router patch result: {router_result}")
                
                if router_result.get("success"):
                    logger.info("✓ Plugins router patched successfully")
                else:
                    for err in router_result.get("errors", []):
                        logger.warning(f"  ✗ Plugins router patch error: {err}")

                logger.info("=" * 60)
                return True
            else:
                logger.warning(f"Production patcher not found at: {patcher_path}")

            # 回退到开发环境 injector（修改 TypeScript 源码）
            injector_path = os.path.join(plugin_dir, "ui_injector.py")
            logger.info(f"Looking for dev injector at: {injector_path}")
            if os.path.exists(injector_path):
                logger.info("Found ui_injector.py, attempting dev UI injection...")
                import importlib.util
                spec = importlib.util.spec_from_file_location("ui_injector", injector_path)
                injector_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(injector_module)

                result = injector_module.inject_ui(qwenpaw_root)
                logger.info(f"Dev injector result: {result}")
                if result.get("success"):
                    logger.info("✓ UI injection completed successfully")
                    modifications = result.get("modifications", {})
                    for name, success in modifications.items():
                        status = "✓" if success else "✗"
                        logger.info(f"  {status} {name}")
                    return True
                else:
                    logger.warning(f"Dev injector failed: {result.get('error', 'unknown')}")
            else:
                logger.warning(f"Dev injector not found at: {injector_path}")

            logger.warning("UI injection skipped - no compatible injector found or all failed")
            return False

        except Exception as e:
            logger.error(
                f"Failed to inject UI: {e}",
                exc_info=True,
            )
            return False

    def _startup_hook(self):
        """启动钩子：初始化记忆管理器"""
        try:
            logger.info("=== HumanThinking Memory Manager Initialization ===")

            try:
                from qwenpaw.agents.tools.HumanThinkingMemoryManager.core.memory_manager import HumanThinkingMemoryManager
                logger.info("✓ HumanThinkingMemoryManager imported successfully")
            except ImportError as e:
                logger.warning(f"Could not import HumanThinkingMemoryManager (may not be installed yet): {e}")

            from .core.memory_manager import get_config
            ht_config = load_humanthinking_config()
            global_config = get_config()

            frozen_days = ht_config.get("frozen_days", global_config.frozen_days)
            archive_days = ht_config.get("archive_days", global_config.archive_days)
            delete_days = ht_config.get("delete_days", global_config.delete_days)

            sleep_config = load_sleep_config()
            enable_agent_sleep = sleep_config.get("enable_agent_sleep", True)
            sleep_idle_hours = sleep_config.get("sleep_idle_hours", 2)
            auto_consolidate = sleep_config.get("auto_consolidate", True)
            consolidate_interval_hours = sleep_config.get("consolidate_interval_hours", 6)

            from .core.sleep_manager import init_sleep_manager, SleepConfig
            sleep_cfg = SleepConfig(
                enable_agent_sleep=enable_agent_sleep,
                light_sleep_minutes=30,
                rem_minutes=60,
                deep_sleep_minutes=sleep_idle_hours * 60,
                auto_consolidate=auto_consolidate,
                consolidate_days=consolidate_interval_hours // 4 if consolidate_interval_hours >= 4 else 1,
                frozen_days=frozen_days,
                archive_days=archive_days,
                enable_insight=True,
                enable_dream_log=True
            )
            init_sleep_manager(sleep_cfg)
            logger.info("✓ SleepManager initialized with config")

            # 初始化备份管理器
            qwenpaw_root = self._find_qwenpaw_root()
            if qwenpaw_root:
                from .core.backup_manager import init_backup_manager, get_backup_manager
                backup_config = load_backup_config()
                auto_backup_hours = 0
                if backup_config.get("auto_backup_enabled", False):
                    auto_backup_hours = backup_config.get("auto_backup_interval_hours", 24)
                init_backup_manager(qwenpaw_root, auto_backup_hours)
                
                # 暴露 API 给前端
                import sys
                if 'window' in sys.modules or hasattr(__import__('sys'), 'modules'):
                    pass
                
                logger.info("✓ BackupManager initialized")

            # 注册 API 路由到 FastAPI app
            try:
                self._register_api_routes()
                logger.info("✓ API routes registered")
            except Exception as e:
                logger.warning(f"Failed to register API routes: {e}")

            logger.info("✓ HumanThinking Memory Manager initialized successfully")

        except Exception as e:
            logger.error(
                f"Failed to initialize HumanThinking Memory Manager: {e}",
                exc_info=True,
            )

    def _register_api_routes(self):
        """注册 API 路由到 FastAPI app
        
        注意：在 startup hook 中，FastAPI app 可能还没有完全初始化。
        我们使用延迟注册策略，确保在 app 完全初始化后再注册路由。
        """
        import threading
        
        def delayed_register():
            """延迟注册路由"""
            import time
            time.sleep(10)  # 等待10秒让app完全初始化
            
            try:
                # 导入 FastAPI app
                from qwenpaw.app._app import app
                from .api.routes import router as ht_router
                
                # 检查路由是否已注册
                existing_paths = [getattr(r, 'path', '') for r in app.routes]
                if '/api/plugin/humanthinking/stats' in existing_paths:
                    logger.info("✓ API routes already registered")
                    return
                
                # 注册路由
                app.include_router(ht_router)
                
                # 验证注册成功
                new_paths = [getattr(r, 'path', '') for r in app.routes]
                if '/api/plugin/humanthinking/stats' in new_paths:
                    logger.info("✓ API routes successfully registered (delayed)")
                else:
                    logger.warning("✗ API routes registration may have failed")
                    
            except Exception as e:
                logger.error(f"Failed to register API routes (delayed): {e}", exc_info=True)
        
        # 启动延迟注册线程
        threading.Thread(target=delayed_register, daemon=True).start()
        logger.info("→ API routes will be registered in 10 seconds (delayed)")

    def _shutdown_hook(self):
        """关闭钩子：清理记忆管理器"""
        try:
            logger.info("=== HumanThinking Memory Manager Cleanup ===")

            # 停止睡眠管理器
            from .core.sleep_manager import get_sleep_manager
            sleep_mgr = get_sleep_manager()
            if sleep_mgr:
                sleep_mgr.stop()
                logger.info("✓ SleepManager stopped")

            logger.info("✓ HumanThinking Memory Manager cleanup completed")

        except Exception as e:
            logger.error(
                f"Failed to cleanup HumanThinking Memory Manager: {e}",
                exc_info=True,
            )


# Export plugin instance (必需)
plugin = HumanThinkingMemoryPlugin()
