"""
配置管理数据模型

定义所有配置项的数据结构和默认值。
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from pathlib import Path
import os


class ModelConfiguration(BaseModel):
    """AI模型配置"""
    model_name: str = Field(default="Qwen/Qwen3-0.6B", description="模型名称")
    model_path: Optional[str] = Field(default=None, description="本地模型路径")
    device: str = Field(default="auto", description="运行设备 (cpu/cuda/auto)")
    max_tokens: int = Field(default=2048, description="最大token数")
    temperature: float = Field(default=0.7, description="生成温度")
    top_p: float = Field(default=0.9, description="Top-p采样")
    auto_download: bool = Field(default=True, description="自动下载模型")
    download_mirror: str = Field(default="huggingface", description="下载镜像")
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v
        
    @validator("top_p")
    def validate_top_p(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")
        return v


class AgentConfiguration(BaseModel):
    """智能体配置"""
    enabled_agents: List[str] = Field(
        default=["hardware", "system", "network", "coordinator"],
        description="启用的智能体列表"
    )
    consensus_threshold: float = Field(default=0.7, description="共识阈值")
    max_reasoning_steps: int = Field(default=10, description="最大推理步数")
    reasoning_timeout: int = Field(default=300, description="推理超时时间(秒)")
    enable_chain_of_thought: bool = Field(default=True, description="启用思考链")
    enable_cross_validation: bool = Field(default=True, description="启用交叉验证")
    fallback_to_rules: bool = Field(default=True, description="回退到规则引擎")


class CollectorConfiguration(BaseModel):
    """数据收集器配置"""
    collection_interval: int = Field(default=5, description="收集间隔(秒)")
    enable_hardware_monitoring: bool = Field(default=True, description="启用硬件监控")
    enable_system_monitoring: bool = Field(default=True, description="启用系统监控")
    enable_network_monitoring: bool = Field(default=True, description="启用网络监控")
    enable_process_monitoring: bool = Field(default=True, description="启用进程监控")
    
    # 网络配置
    network_timeout: int = Field(default=10, description="网络超时时间(秒)")
    ping_hosts: List[str] = Field(
        default=["8.8.8.8", "1.1.1.1", "114.114.114.114"],
        description="ping测试主机列表"
    )
    speedtest_enabled: bool = Field(default=False, description="启用网速测试")
    
    # 系统配置
    max_processes: int = Field(default=100, description="最大进程监控数")
    disk_usage_threshold: float = Field(default=0.9, description="磁盘使用率阈值")
    memory_usage_threshold: float = Field(default=0.9, description="内存使用率阈值")
    cpu_usage_threshold: float = Field(default=0.9, description="CPU使用率阈值")


class GUIConfiguration(BaseModel):
    """GUI界面配置"""
    theme: str = Field(default="dark", description="界面主题")
    language: str = Field(default="zh_CN", description="界面语言")
    window_width: int = Field(default=1200, description="窗口宽度")
    window_height: int = Field(default=800, description="窗口高度")
    auto_start_diagnosis: bool = Field(default=False, description="自动开始诊断")
    show_system_tray: bool = Field(default=True, description="显示系统托盘")
    minimize_to_tray: bool = Field(default=True, description="最小化到托盘")
    enable_notifications: bool = Field(default=True, description="启用通知")
    refresh_interval: int = Field(default=5, description="界面刷新间隔(秒)")


class UpdateConfiguration(BaseModel):
    """更新配置"""
    auto_check_updates: bool = Field(default=True, description="自动检查更新")
    update_channel: str = Field(default="stable", description="更新通道")
    repository_url: str = Field(
        default="https://gitea.example.com/sysgraph/sysgraph",
        description="仓库URL"
    )
    repository_type: str = Field(default="gitea", description="仓库类型")
    check_interval: int = Field(default=3600, description="检查间隔(秒)")
    backup_before_update: bool = Field(default=True, description="更新前备份")
    restart_after_update: bool = Field(default=True, description="更新后重启")


class LoggingConfiguration(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    file_enabled: bool = Field(default=True, description="启用文件日志")
    console_enabled: bool = Field(default=True, description="启用控制台日志")
    max_file_size: str = Field(default="10MB", description="最大日志文件大小")
    retention_days: int = Field(default=7, description="日志保留天数")
    format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        description="日志格式"
    )


class RuleEngineConfiguration(BaseModel):
    """规则引擎配置"""
    enable_builtin_rules: bool = Field(default=True, description="启用内置规则")
    enable_remote_rules: bool = Field(default=True, description="启用远程规则")
    remote_rules_url: str = Field(
        default="https://gitea.example.com/sysgraph/rules",
        description="远程规则仓库URL"
    )
    rules_update_interval: int = Field(default=86400, description="规则更新间隔(秒)")
    rule_confidence_threshold: float = Field(default=0.8, description="规则置信度阈值")


class SecurityConfiguration(BaseModel):
    """安全配置"""
    enable_sandbox: bool = Field(default=True, description="启用沙箱模式")
    allow_system_commands: bool = Field(default=False, description="允许系统命令")
    allowed_commands: List[str] = Field(default=[], description="允许的命令列表")
    network_restrictions: bool = Field(default=True, description="网络限制")
    file_access_restrictions: bool = Field(default=True, description="文件访问限制")


class ApplicationConfiguration(BaseModel):
    """应用程序总配置"""
    # 基本信息
    app_name: str = Field(default="SysGraph", description="应用程序名称")
    app_version: str = Field(default="0.1.0", description="应用程序版本")
    
    # 各模块配置
    model: ModelConfiguration = Field(default_factory=ModelConfiguration)
    agents: AgentConfiguration = Field(default_factory=AgentConfiguration)
    collectors: CollectorConfiguration = Field(default_factory=CollectorConfiguration)
    gui: GUIConfiguration = Field(default_factory=GUIConfiguration)
    updates: UpdateConfiguration = Field(default_factory=UpdateConfiguration)
    logging: LoggingConfiguration = Field(default_factory=LoggingConfiguration)
    rules: RuleEngineConfiguration = Field(default_factory=RuleEngineConfiguration)
    security: SecurityConfiguration = Field(default_factory=SecurityConfiguration)
    
    # 运行时配置
    data_directory: str = Field(default="", description="数据目录")
    cache_directory: str = Field(default="", description="缓存目录")
    log_directory: str = Field(default="", description="日志目录")
    
    def __init__(self, **data):
        super().__init__(**data)
        # 设置默认目录
        if not self.data_directory:
            self.data_directory = str(Path.home() / ".sysgraph" / "data")
        if not self.cache_directory:
            self.cache_directory = str(Path.home() / ".sysgraph" / "cache")
        if not self.log_directory:
            self.log_directory = str(Path.home() / ".sysgraph" / "logs")
    
    def create_directories(self) -> None:
        """创建必要的目录"""
        for directory in [self.data_directory, self.cache_directory, self.log_directory]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get_model_cache_path(self) -> Path:
        """获取模型缓存路径"""
        return Path(self.cache_directory) / "models"
    
    def get_rules_cache_path(self) -> Path:
        """获取规则缓存路径"""
        return Path(self.cache_directory) / "rules"


# 默认配置实例
DEFAULT_CONFIG = ApplicationConfiguration()