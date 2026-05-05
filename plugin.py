# -*- coding: utf-8 -*-
"""HumanThinking Plugin for QwenPaw v1.1.5.post1+"""

from qwenpaw.plugins.api import PluginApi
import logging
import os
import sys
import json
from pathlib import Path
from typing import Optional

from .utils.paths import resolve_qwenpaw_dir as _resolve_qwenpaw_dir, resolve_agent_workspace_dir as _resolve_agent_workspace_dir, validate_agent_id
from .utils.version import CURRENT_VERSION

logger = logging.getLogger("qwenpaw.humanthinking")

CONFIG_KEY = 'humanthinking_config'
BACKUP_CONFIG_KEY = 'humanthinking_backup_config'
SLEEP_CONFIG_KEY = 'humanthinking_sleep_config'


_config_profiles_cache = None

def _config_profiles():
    global _config_profiles_cache
    if _config_profiles_cache is not None:
        return _config_profiles_cache
    try:
        from qwenpaw.config.utils import load_config
        _config_profiles_cache = load_config().agents.profiles
        return _config_profiles_cache
    except Exception:
        return {}


def _resolve_all_agent_workspace_dirs() -> list[Path]:
    profiles = _config_profiles()
    if profiles:
        return [Path(ref.workspace_dir).expanduser().resolve() for ref in profiles.values()]
    workspaces_dir = _resolve_qwenpaw_dir() / "workspaces"
    if workspaces_dir.exists():
        return [d for d in workspaces_dir.iterdir() if d.is_dir()]
    return []


def _load_json_config(config_path: Path, default: dict = None) -> dict:
    """通用配置加载函数"""
    try:
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load config from {config_path}: {e}")
    return default or {}


class HumanThinkingMemoryPlugin:
    """HumanThinking Memory Manager Plugin."""

    def register(self, api: PluginApi):
        logger.info("=" * 60)
        logger.info("Registering HumanThinking Memory Manager v1.0.0-beta0.1...")
        logger.info(f"Plugin module: {__name__}")
        logger.info(f"Plugin file: {__file__}")

        try:
            logger.info("Searching for QwenPaw root...")
            qwenpaw_root = self._find_qwenpaw_root()

            if qwenpaw_root:
                logger.info(f"QwenPaw root found: {qwenpaw_root}")
                logger.info("Attempting UI injection...")
                ui_injected = self._inject_ui(qwenpaw_root)
                logger.info(f"UI injection result: {'SUCCESS' if ui_injected else 'FAILED'}")
            else:
                logger.warning("QwenPaw root not found, skipping UI injection")
                logger.warning("This means HumanThinking option will NOT appear in the dropdown")

            logger.info("Registering startup hook 'human_thinking_init'...")
            api.register_startup_hook(
                hook_name="human_thinking_init",
                callback=self._startup_hook,
                priority=10,
            )
            logger.info("Startup hook registered")

            logger.info("Registering shutdown hook 'human_thinking_cleanup'...")
            api.register_shutdown_hook(
                hook_name="human_thinking_cleanup",
                callback=self._shutdown_hook,
                priority=10,
            )
            logger.info("Shutdown hook registered")

            try:
                logger.info("Registering API routes...")
                if 'qwenpaw.app._app' in sys.modules:
                    app_module = sys.modules['qwenpaw.app._app']
                    app = getattr(app_module, 'app', None)
                else:
                    from qwenpaw.app._app import app

                from .api.routes import router as ht_router

                existing_paths = [getattr(r, 'path', '') for r in app.routes]
                has_health = any('humanthinking/health' in p for p in existing_paths)

                if not has_health:
                    @app.get("/api/plugins/humanthinking/health")
                    async def health_check():
                        return {
                            "status": "healthy",
                            "plugin": "humanthinking",
                            "version": CURRENT_VERSION,
                            "timestamp": __import__('time').time()
                        }
                    logger.info("Health endpoint registered in register()")
                else:
                    logger.info("Health endpoint already in FastAPI app")

                logger.info("Config/Stats routes handled by api/routes.py via include_router")

                verify_paths = [getattr(r, 'path', '') for r in app.routes]
                verify_health = [p for p in verify_paths if 'humanthinking/health' in p]
                logger.info(f"Register() verify health routes: {verify_health}")
                logger.info(f"Register() app id: {id(app)}, routes count: {len(app.routes)}")
            except Exception as e:
                logger.warning(f"Failed to register API routes in register(): {e}")

            logger.info("=" * 60)
            logger.info("HumanThinking Memory Manager registered")
            logger.info(f"  - UI Injection: {'Yes' if qwenpaw_root else 'No (QwenPaw root not found)'}")
            logger.info("  - Startup Hook: Yes")
            logger.info("  - Shutdown Hook: Yes")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Failed to register HumanThinking Memory Manager: {e}", exc_info=True)

    def _find_qwenpaw_root(self) -> str:
        try:
            import qwenpaw
            qwenpaw_file = qwenpaw.__file__
            logger.info(f"Found qwenpaw package at: {qwenpaw_file}")
            if qwenpaw_file:
                path = os.path.abspath(qwenpaw_file)
                while path != '/' and path != '':
                    path = os.path.dirname(path)
                    if os.path.basename(path) == '.qwenpaw':
                        logger.info(f"Found QwenPaw root: {path}")
                        return path
                path = os.path.abspath(qwenpaw_file)
                for _ in range(6):
                    path = os.path.dirname(path)
                    if os.path.isdir(os.path.join(path, 'console')):
                        logger.info(f"Found QwenPaw root (with console): {path}")
                        return path
        except ImportError as e:
            logger.warning(f"Cannot import qwenpaw package: {e}")

        common_paths = [
            os.path.expanduser("~/.qwenpaw"),
            str(_resolve_qwenpaw_dir()),
            "/opt/QwenPaw",
        ]

        for path in common_paths:
            if os.path.isdir(path) and os.path.isdir(os.path.join(path, "console")):
                logger.info(f"Found QwenPaw root at common path: {path}")
                return path

        logger.warning(f"QwenPaw root not found. Searched paths: {common_paths}")
        return ""

    def _inject_ui(self, qwenpaw_root: str) -> bool:
        try:
            logger.info("=" * 60)
            logger.info("Starting UI injection process...")
            logger.info(f"QwenPaw root: {qwenpaw_root}")

            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            logger.info(f"Plugin directory: {plugin_dir}")

            patcher_path = os.path.join(plugin_dir, "prod_ui_patcher.py")
            logger.info(f"Looking for production patcher at: {patcher_path}")

            if os.path.exists(patcher_path):
                logger.info("Found prod_ui_patcher.py, attempting production UI patch...")
                import importlib.util
                spec = importlib.util.spec_from_file_location("prod_ui_patcher", patcher_path)
                patcher_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(patcher_module)
                logger.info("Prod UI patcher module loaded successfully")

                logger.info("Step 1: Installing HumanThinkingMemoryManager to QwenPaw...")
                install_result = patcher_module.install_human_thinking_to_qwenpaw(
                    qwenpaw_root=qwenpaw_root,
                    plugin_dir=plugin_dir
                )
                logger.info(f"Install result: {install_result}")
                if install_result.get("success"):
                    logger.info("HumanThinkingMemoryManager installed successfully")
                else:
                    for err in install_result.get("errors", []):
                        logger.warning(f"Install error: {err}")
                    logger.warning("HumanThinkingMemoryManager not installed - backend will fail")

                logger.info("Step 2: Patching workspace.py error handling...")
                workspace_result = patcher_module.patch_workspace_import(qwenpaw_root)
                logger.info(f"Workspace patch result: {workspace_result}")

                logger.info("Step 3: Patching backend config (Literal type)...")
                backend_result = patcher_module.patch_backend_config(qwenpaw_root)
                logger.info(f"Backend config patch result: {backend_result}")

                logger.info("Step 3.5: Patching runtime Pydantic model (in-memory)...")
                runtime_result = patcher_module.patch_runtime_config_model()
                logger.info(f"Runtime model patch result: {runtime_result}")

                logger.info("Step 3.6: Ensuring memory_registry registration...")
                registry_result = patcher_module.ensure_memory_registry_registration()
                logger.info(f"Registry guard result: {registry_result}")
                if not registry_result.get("registered"):
                    logger.error(f"CRITICAL: human_thinking NOT registered in memory_registry!")
                else:
                    logger.info(f"Memory registry backends: {registry_result.get('backends')}")

                logger.info("Step 4: Patching frontend JS (dropdown options)...")
                result = patcher_module.patch_production_ui(qwenpaw_root)
                logger.info(f"Production patcher result: {result}")

                logger.info("Step 5: Patching frontend JS (agent config refresh on switch)...")
                refresh_result = patcher_module.patch_agent_config_refresh(qwenpaw_root)
                logger.info(f"Agent refresh patch result: {refresh_result}")

                logger.info("Step 6: Patching plugins.py (API routes)...")
                router_result = patcher_module.patch_plugins_router(qwenpaw_root)
                logger.info(f"Plugins router patch result: {router_result}")

                logger.info("Step 7: Injecting persistent config (config.json -> human_thinking)...")
                persist_result = patcher_module.inject_persistent_config()
                logger.info(f"Persistent config injection: {persist_result}")

                logger.info("Step 8: Injecting registry preload (sitecustomize.py)...")
                preload_result = patcher_module.inject_registry_preload()
                logger.info(f"Registry preload injection: {preload_result}")

                logger.info("Step 9: Injecting post_reply dispatch into runner.py...")
                post_reply_result = patcher_module.inject_runner_post_reply_dispatch()
                logger.info(f"Post-reply dispatch injection: {post_reply_result}")

                logger.info("=" * 60)
                return True
            else:
                logger.warning(f"Production patcher not found at: {patcher_path}")

            injector_path = os.path.join(plugin_dir, "ui_injector.py")
            if os.path.exists(injector_path):
                logger.info("Found ui_injector.py, attempting dev UI injection...")
                import importlib.util
                spec = importlib.util.spec_from_file_location("ui_injector", injector_path)
                injector_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(injector_module)
                result = injector_module.inject_ui(qwenpaw_root)
                if result.get("success"):
                    return True
            else:
                logger.warning(f"Dev injector not found at: {injector_path}")

            logger.warning("UI injection skipped - no compatible injector found or all failed")
            return False

        except Exception as e:
            logger.error(f"Failed to inject UI: {e}", exc_info=True)
            return False

    def _startup_hook(self):
        try:
            logger.info("=== Copying AGENT.md to workspace ===")
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            agent_md_source = os.path.join(plugin_dir, "AGENT.md")

            workspaces_dirs = _resolve_all_agent_workspace_dirs()
            for agent_dir in workspaces_dirs:
                if agent_dir.is_dir():
                    agent_md_target = agent_dir / "AGENTS.md"
                    need_copy = False
                    if not agent_md_target.exists():
                        need_copy = True
                    else:
                        existing_content = agent_md_target.read_text(encoding='utf-8')
                        if "HumanThinking" not in existing_content:
                            need_copy = True

                    if need_copy and os.path.exists(agent_md_source):
                        with open(agent_md_source, 'r', encoding='utf-8') as f:
                            content = f.read()

                        if agent_md_target.exists():
                            existing = agent_md_target.read_text(encoding='utf-8')
                            if "<!-- HumanThinking:start -->" not in existing:
                                content = existing + "\n\n<!-- HumanThinking:start -->\n\n" + content + "\n\n<!-- HumanThinking:end -->\n"
                                agent_md_target.write_text(content, encoding='utf-8')
                                logger.info(f"Appended HumanThinking to {agent_dir.name}/AGENTS.md")
                        else:
                            agent_md_target.write_text(content, encoding='utf-8')
                            logger.info(f"Created {agent_dir.name}/AGENTS.md")

            logger.info("AGENT.md copy completed")
        except Exception as e:
            logger.warning(f"Failed to copy AGENT.md: {e}")

        try:
            logger.info("=== Registering API Routes ===")

            if 'qwenpaw.app._app' in sys.modules:
                app_module = sys.modules['qwenpaw.app._app']
                app = getattr(app_module, 'app', None)
            else:
                from qwenpaw.app._app import app

            from .api.routes import router as ht_router

            existing_paths = [getattr(r, 'path', '') for r in app.routes]
            has_health = any('humanthinking/health' in p for p in existing_paths)

            if not has_health:
                @app.get("/api/plugins/humanthinking/health")
                async def health_check():
                    return {
                        "status": "healthy",
                        "plugin": "humanthinking",
                        "version": CURRENT_VERSION,
                        "timestamp": __import__('time').time()
                    }
                logger.info("Health endpoint registered directly to FastAPI app")

            has_uninstall = any('humanthinking/uninstall' in p for p in existing_paths)
            if not has_uninstall:
                try:
                    app.include_router(ht_router, prefix="/api/plugins/humanthinking")
                    logger.info("All API routes registered via include_router")
                except Exception as e:
                    logger.warning(f"Failed to include router: {e}")
            else:
                logger.info("Uninstall route already exists, forcing router inclusion anyway")
                try:
                    app.include_router(ht_router, prefix="/api/plugins/humanthinking")
                    logger.info("All API routes registered via include_router (forced)")
                except Exception as e:
                    logger.warning(f"Failed to include router (forced): {e}")

            new_paths = [getattr(r, 'path', '') for r in app.routes]
            sleep_routes = [p for p in new_paths if 'sleep' in p]
            logger.info(f"Sleep routes registered: {len(sleep_routes)}")
            for p in sleep_routes:
                logger.info(f"  - {p}")

            logger.info(f"App object id: {id(app)}, routes count: {len(app.routes)}")

            try:
                spa_idx = None
                for i, r in enumerate(app.routes):
                    if getattr(r, 'path', '') == '/{full_path:path}':
                        spa_idx = i
                        break
                if spa_idx is not None:
                    ht_routes = []
                    i = 0
                    while i < len(app.routes):
                        path = getattr(app.routes[i], 'path', '')
                        if ('humanthinking' in path or 'human_thinking' in path) and i >= spa_idx:
                            ht_routes.append(app.routes.pop(i))
                        else:
                            i += 1
                    for route in reversed(ht_routes):
                        app.routes.insert(spa_idx, route)
                    logger.info(f"[RouteReorder] Moved {len(ht_routes)} HT routes before SPA catch-all")
            except Exception as e:
                logger.warning(f"[RouteReorder] Failed: {e}")
        except Exception as e:
            logger.error(f"Failed to register API routes: {e}", exc_info=True)

        try:
            logger.info("=== HumanThinking Memory Manager Initialization ===")

            try:
                from qwenpaw.agents.tools.HumanThinking.core.memory_manager import HumanThinkingMemoryManager
                logger.info("HumanThinkingMemoryManager imported successfully")
            except ImportError as e:
                logger.warning(f"Could not import HumanThinkingMemoryManager: {e}")
                HumanThinkingMemoryManager = None

            ht_config = _load_json_config(
                _resolve_qwenpaw_dir() / "config" / f"{CONFIG_KEY}.json"
            )
            import json as _json
            global_config_path = _resolve_qwenpaw_dir() / "config" / f"{CONFIG_KEY}.json"
            try:
                with open(global_config_path, 'r', encoding='utf-8') as _f:
                    global_config_data = _json.load(_f)
            except Exception:
                global_config_data = {}
            frozen_days = ht_config.get("frozen_days", global_config_data.get("frozen_days", 30))
            archive_days = ht_config.get("archive_days", global_config_data.get("archive_days", 90))
            delete_days = ht_config.get("delete_days", global_config_data.get("delete_days", 365))

            if HumanThinkingMemoryManager is not None:
                try:
                    qwenpaw_dir = _resolve_qwenpaw_dir()
                    working_dir = str(_resolve_agent_workspace_dir("default"))
                    logger.info(f"Resolved working directory: {working_dir} (from {qwenpaw_dir})")

                    Path(working_dir).mkdir(parents=True, exist_ok=True)

                    memory_manager = HumanThinkingMemoryManager(
                        working_dir=working_dir,
                        agent_id="default",
                        user_id=None
                    )

                    try:
                        import asyncio as _asyncio
                        loop = _asyncio.get_event_loop()
                        if loop.is_running():
                            _asyncio.create_task(memory_manager.start())
                        else:
                            loop.run_until_complete(memory_manager.start())
                    except RuntimeError:
                        import asyncio as _asyncio
                        loop = _asyncio.new_event_loop()
                        _asyncio.set_event_loop(loop)
                        loop.run_until_complete(memory_manager.start())

                    logger.info(f"HumanThinkingMemoryManager instance created and started")
                    logger.info(f"  - Working directory: {working_dir}")
                    logger.info(f"  - Database path: {memory_manager.db_path}")
                except Exception as e:
                    logger.warning(f"Failed to create HumanThinkingMemoryManager instance: {e}")

            sleep_config = _load_json_config(
                _resolve_qwenpaw_dir() / "config" / "sleep_config.json",
                default={
                    "enable_agent_sleep": True,
                    "sleep_idle_hours": 2,
                    "light_sleep_minutes": 30,
                    "rem_minutes": 60,
                    "auto_consolidate": True,
                    "consolidate_interval_hours": 6,
                }
            )
            enable_agent_sleep = sleep_config.get("enable_agent_sleep", True)
            sleep_idle_hours = sleep_config.get("sleep_idle_hours", 2)
            light_sleep_minutes = sleep_config.get("light_sleep_minutes", 30)
            rem_minutes = sleep_config.get("rem_minutes", 60)
            auto_consolidate = sleep_config.get("auto_consolidate", True)
            consolidate_interval_hours = sleep_config.get("consolidate_interval_hours", 6)

            from qwenpaw.agents.tools.HumanThinking.core.sleep_manager import init_sleep_manager, SleepConfig
            sleep_cfg = SleepConfig(
                enable_agent_sleep=enable_agent_sleep,
                light_sleep_minutes=light_sleep_minutes,
                rem_minutes=rem_minutes,
                deep_sleep_minutes=sleep_idle_hours * 60,
                auto_consolidate=auto_consolidate,
                consolidate_days=consolidate_interval_hours // 4 if consolidate_interval_hours >= 4 else 1,
                frozen_days=frozen_days,
                archive_days=archive_days,
                enable_insight=True,
                enable_dream_log=True
            )
            sleep_mgr = init_sleep_manager(sleep_cfg)
            logger.info("SleepManager initialized with config (event-driven mode, no timer thread)")

            qwenpaw_root = str(_resolve_qwenpaw_dir())
            if qwenpaw_root:
                from qwenpaw.agents.tools.HumanThinking.core.backup_manager import init_backup_manager
                backup_config = _load_json_config(
                    _resolve_qwenpaw_dir() / "config" / f"{BACKUP_CONFIG_KEY}.json",
                    default={"auto_backup_enabled": False, "auto_backup_interval_hours": 24}
                )
                auto_backup_hours = 0
                if backup_config.get("auto_backup_enabled", False):
                    auto_backup_hours = backup_config.get("auto_backup_interval_hours", 24)
                init_backup_manager(qwenpaw_root, auto_backup_hours)
                logger.info("BackupManager initialized")

            logger.info("HumanThinking Memory Manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize HumanThinking Memory Manager: {e}", exc_info=True)

    def _shutdown_hook(self):
        try:
            logger.info("=== HumanThinking Memory Manager Cleanup ===")
            try:
                from qwenpaw.agents.tools.HumanThinking.core.backup_manager import get_backup_manager
                bm = get_backup_manager()
                if bm:
                    bm.shutdown()
                    logger.info("BackupManager shutdown completed")
            except Exception as e:
                logger.warning(f"Failed to shutdown BackupManager: {e}")
            try:
                from qwenpaw.agents.tools.HumanThinking.api.routes import _db_cache
                import asyncio as _asyncio
                for db_path, db in list(_db_cache.items()):
                    try:
                        _asyncio.get_event_loop().run_until_complete(db.close())
                        logger.info(f"Closed cached DB: {db_path}")
                    except Exception:
                        pass
                _db_cache.clear()
                logger.info("Routes DB cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear routes DB cache: {e}")
            try:
                from qwenpaw.agents.tools.HumanThinking.core.sleep_manager import get_sleep_manager
                sm = get_sleep_manager()
                if sm and hasattr(sm, '_db_cache'):
                    import asyncio as _asyncio
                    for db_path, db in list(sm._db_cache.items()):
                        try:
                            _asyncio.get_event_loop().run_until_complete(db.close())
                        except Exception:
                            pass
                    sm._db_cache.clear()
                    logger.info("SleepManager DB cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear SleepManager DB cache: {e}")
            logger.info("HumanThinking Memory Manager cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup HumanThinking Memory Manager: {e}", exc_info=True)


plugin = HumanThinkingMemoryPlugin()
