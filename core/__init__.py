"""
SysGraph 核心模块

包含配置管理、诊断管理、智能体管理等核心功能。
"""

from .config_models import (
    ApplicationConfiguration,
    ModelConfiguration,
    AgentConfiguration,
    CollectorConfiguration,
    GUIConfiguration,
    UpdateConfiguration,
    LoggingConfiguration,
    RuleEngineConfiguration,
    SecurityConfiguration,
    DEFAULT_CONFIG,
)

from .config_manager import ConfigurationManager

# 占位符 - 后续任务中实现
class DiagnosisManager:
    """诊断管理器 - 占位符"""
    pass

class AgentManager:
    """智能体管理器 - 占位符"""
    pass

class ModelManager:
    """模型管理器 - 占位符"""
    pass

class SystemDataCollector:
    """系统数据收集器 - 占位符"""
    pass

__all__ = [
    # 配置相关
    "ApplicationConfiguration",
    "ModelConfiguration", 
    "AgentConfiguration",
    "CollectorConfiguration",
    "GUIConfiguration",
    "UpdateConfiguration",
    "LoggingConfiguration",
    "RuleEngineConfiguration",
    "SecurityConfiguration",
    "DEFAULT_CONFIG",
    "ConfigurationManager",
    
    # 核心管理器
    "DiagnosisManager",
    "AgentManager",
    "ModelManager", 
    "SystemDataCollector",
]