# -*- coding: utf-8 -*-
"""环境检测工具 - 适配不同安装环境（Docker、Windows、macOS、Linux）

支持的环境：
1. Docker: /app/working, /app/venv
2. Windows脚本安装: %USERPROFILE%\.qwenpaw, venv
3. macOS/Linux脚本安装: ~/.qwenpaw, venv
4. pip安装: site-packages
5. 源码安装: 项目目录
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


class QwenPawEnvironment:
    """QwenPaw环境信息"""
    
    def __init__(self):
        self.install_type: str = "unknown"  # docker, script, pip, source
        self.working_dir: Optional[Path] = None
        self.venv_dir: Optional[Path] = None
        self.python_executable: Optional[Path] = None
        self.site_packages_dir: Optional[Path] = None
        self.qwenpaw_package_dir: Optional[Path] = None
        self.plugins_dir: Optional[Path] = None
        self.config_file: Optional[Path] = None
        self.is_windows: bool = sys.platform.startswith("win")
        self.is_macos: bool = sys.platform == "darwin"
        self.is_linux: bool = sys.platform.startswith("linux")
        self.is_docker: bool = self._detect_docker()
        
    def _detect_docker(self) -> bool:
        """检测是否在Docker容器中运行"""
        # 检查常见的Docker环境标志
        if os.path.exists("/.dockerenv"):
            return True
        try:
            with open("/proc/1/cgroup", "r") as f:
                return "docker" in f.read()
        except:
            pass
        return os.environ.get("QWENPAW_RUNNING_IN_CONTAINER") == "1"


def detect_qwenpaw_env() -> QwenPawEnvironment:
    """自动检测QwenPaw安装环境
    
    Returns:
        QwenPawEnvironment: 包含所有路径信息的环境对象
    """
    env = QwenPawEnvironment()
    
    # 1. 检测工作目录
    env.working_dir = _detect_working_dir()
    if env.working_dir:
        env.plugins_dir = env.working_dir / "plugins"
        env.config_file = env.working_dir / "config.json"
    
    # 2. 检测Python环境和site-packages
    env.python_executable = Path(sys.executable)
    env.site_packages_dir = _detect_site_packages()
    
    # 3. 检测qwenpaw包目录
    env.qwenpaw_package_dir = _detect_qwenpaw_package(env)
    
    # 4. 检测venv目录
    env.venv_dir = _detect_venv_dir(env)
    
    # 5. 确定安装类型
    env.install_type = _determine_install_type(env)
    
    logger.info(f"Detected QwenPaw environment: {env.install_type}")
    logger.info(f"  Working dir: {env.working_dir}")
    logger.info(f"  Plugins dir: {env.plugins_dir}")
    logger.info(f"  QwenPaw package: {env.qwenpaw_package_dir}")
    logger.info(f"  venv: {env.venv_dir}")
    logger.info(f"  Docker: {env.is_docker}")
    
    return env


def _detect_working_dir() -> Optional[Path]:
    """检测QwenPaw工作目录"""
    # 优先级1: 环境变量
    for env_var in ["QWENPAW_WORKING_DIR", "COPAW_WORKING_DIR"]:
        if env_var in os.environ:
            path = Path(os.environ[env_var]).expanduser().resolve()
            if path.exists():
                return path
    
    # 优先级2: Docker默认路径
    docker_path = Path("/app/working")
    if docker_path.exists():
        return docker_path
    
    # 优先级3: 用户主目录
    home_paths = [
        Path.home() / ".qwenpaw",
        Path.home() / ".copaw",  # 遗留目录
    ]
    for path in home_paths:
        if path.exists():
            return path
    
    return None


def _detect_site_packages() -> Optional[Path]:
    """检测site-packages目录"""
    for path in sys.path:
        if "site-packages" in path or "dist-packages" in path:
            p = Path(path)
            if p.exists() and p.is_dir():
                return p
    return None


def _detect_qwenpaw_package(env: QwenPawEnvironment) -> Optional[Path]:
    """检测qwenpaw包安装位置"""
    # 方法1: 通过导入检测
    try:
        import qwenpaw
        pkg_dir = Path(qwenpaw.__file__).parent
        if pkg_dir.exists():
            return pkg_dir
    except ImportError:
        pass
    
    # 方法2: 在site-packages中查找
    if env.site_packages_dir:
        qwenpaw_dir = env.site_packages_dir / "qwenpaw"
        if qwenpaw_dir.exists():
            return qwenpaw_dir
    
    # 方法3: 在venv中查找
    if env.venv_dir:
        for python_dir in (env.venv_dir / "lib").glob("python3.*"):
            site_pkg = python_dir / "site-packages" / "qwenpaw"
            if site_pkg.exists():
                return site_pkg
    
    # 方法4: 系统级安装路径
    system_paths = [
        Path("/usr/local/lib/python3.12/site-packages/qwenpaw"),
        Path("/usr/local/lib/python3.11/site-packages/qwenpaw"),
        Path("/usr/local/lib/python3.10/site-packages/qwenpaw"),
        Path("/usr/lib/python3.12/site-packages/qwenpaw"),
        Path("/usr/lib/python3.11/site-packages/qwenpaw"),
        Path("/usr/lib/python3.10/site-packages/qwenpaw"),
    ]
    for path in system_paths:
        if path.exists():
            return path
    
    return None


def _detect_venv_dir(env: QwenPawEnvironment) -> Optional[Path]:
    """检测虚拟环境目录"""
    # 方法1: 从Python可执行文件路径推断
    exe = env.python_executable
    if exe:
        # Windows: venv/Scripts/python.exe
        # Unix: venv/bin/python
        if "Scripts" in str(exe) or "bin" in str(exe):
            venv = exe.parent.parent
            if (venv / "pyvenv.cfg").exists() or (venv / "bin").exists() or (venv / "Scripts").exists():
                return venv
    
    # 方法2: 在工作目录中查找
    if env.working_dir:
        venv = env.working_dir / "venv"
        if venv.exists():
            return venv
    
    # 方法3: 检查环境变量
    if "VIRTUAL_ENV" in os.environ:
        return Path(os.environ["VIRTUAL_ENV"])
    
    return None


def _determine_install_type(env: QwenPawEnvironment) -> str:
    """确定安装类型"""
    if env.is_docker:
        return "docker"
    
    if env.working_dir:
        working_str = str(env.working_dir)
        if ".qwenpaw" in working_str or ".copaw" in working_str:
            if env.is_windows:
                return "script_windows"
            elif env.is_macos:
                return "script_macos"
            else:
                return "script_linux"
    
    if env.site_packages_dir and env.qwenpaw_package_dir:
        if str(env.qwenpaw_package_dir).startswith(str(env.site_packages_dir)):
            return "pip"
    
    return "source"


def get_qwenpaw_console_dir(env: QwenPawEnvironment) -> Optional[Path]:
    """获取QwenPaw前端console目录"""
    if env.qwenpaw_package_dir:
        console = env.qwenpaw_package_dir / "console"
        if console.exists() and (console / "index.html").exists():
            return console
    return None


def get_cache_dirs(env: QwenPawEnvironment) -> List[Path]:
    """获取需要清除缓存的目录列表"""
    dirs = []
    
    if env.qwenpaw_package_dir:
        dirs.append(env.qwenpaw_package_dir)
    
    # 也清除工作目录中的缓存
    if env.working_dir:
        for cache_dir in env.working_dir.rglob("__pycache__"):
            dirs.append(cache_dir)
    
    return dirs


# 便捷函数
def get_current_env() -> QwenPawEnvironment:
    """获取当前环境（带缓存）"""
    if not hasattr(get_current_env, "_cache"):
        get_current_env._cache = detect_qwenpaw_env()
    return get_current_env._cache


def reset_env_cache():
    """重置环境缓存"""
    if hasattr(get_current_env, "_cache"):
        delattr(get_current_env, "_cache")
