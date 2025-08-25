"""
SysGraph - 智能系统诊断工具

基于AI的跨平台系统监控和诊断解决方案，支持多智能体协同分析。
"""

__version__ = "0.1.0"
__author__ = "SysGraph Team"
__email__ = "team@sysgraph.io"
__description__ = "智能系统诊断工具 - 基于AI的跨平台系统监控和诊断解决方案"

# 导出主要类和函数
from .core import (
    DiagnosisManager,
    AgentManager,
    ModelManager,
    SystemDataCollector,
)

from .gui import SysGraphMainWindow
from .models import SystemData, DiagnosisResult

__all__ = [
    "DiagnosisManager",
    "AgentManager", 
    "ModelManager",
    "SystemDataCollector",
    "SysGraphMainWindow",
    "SystemData",
    "DiagnosisResult",
]