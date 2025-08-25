"""
SysGraph 工具函数模块

提供日志设置、系统要求检查等通用功能。
"""

import sys
import platform
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logging(level: str = "INFO", debug: bool = False) -> None:
    """
    设置日志系统
    
    Args:
        level: 日志级别
        debug: 是否启用调试模式
    """
    # 移除默认处理器
    logger.remove()
    
    # 设置日志级别
    log_level = "DEBUG" if debug else level
    
    # 控制台输出
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        colorize=True
    )
    
    # 文件输出
    log_dir = Path.home() / ".sysgraph" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        log_dir / "sysgraph.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    if debug:
        logger.debug("调试模式已启用")


def check_system_requirements() -> bool:
    """
    检查系统要求
    
    Returns:
        bool: 是否满足系统要求
    """
    try:
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 9):
            logger.error(f"Python版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}, 需要 >= 3.9")
            return False
        
        # 检查操作系统
        system = platform.system()
        if system not in ["Windows", "Darwin", "Linux"]:
            logger.error(f"不支持的操作系统: {system}")
            return False
        
        # 检查必要的依赖
        required_packages = [
            "PyQt6",
            "psutil", 
            "requests",
            "pydantic",
            "loguru"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"缺少必要依赖: {', '.join(missing_packages)}")
            return False
        
        logger.info("系统要求检查通过")
        return True
        
    except Exception as e:
        logger.error(f"系统要求检查失败: {e}")
        return False


def get_system_info() -> dict:
    """
    获取系统信息
    
    Returns:
        dict: 系统信息字典
    """
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "python_executable": sys.executable,
    }


def ensure_directory(path: Path) -> bool:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 是否成功
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {path}: {e}")
        return False


def format_bytes(bytes_value: int) -> str:
    """
    格式化字节数
    
    Args:
        bytes_value: 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f}{unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f}PB"


def format_duration(seconds: float) -> str:
    """
    格式化持续时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}小时"
    else:
        days = seconds / 86400
        return f"{days:.1f}天"