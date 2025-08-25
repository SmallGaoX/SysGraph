"""
数据模型定义

定义系统数据的结构化表示。
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field


class CPUInfo(BaseModel):
    """CPU信息"""
    usage_percent: float = Field(description="CPU使用率")
    core_count: int = Field(description="CPU核心数")
    frequency: float = Field(description="CPU频率(MHz)")
    temperature: Optional[float] = Field(default=None, description="CPU温度(°C)")
    load_average: Optional[List[float]] = Field(default=None, description="负载平均值")


class MemoryInfo(BaseModel):
    """内存信息"""
    total: int = Field(description="总内存(字节)")
    available: int = Field(description="可用内存(字节)")
    used: int = Field(description="已用内存(字节)")
    usage_percent: float = Field(description="内存使用率")
    swap_total: int = Field(description="交换分区总大小")
    swap_used: int = Field(description="交换分区已用")


class DiskInfo(BaseModel):
    """磁盘信息"""
    device: str = Field(description="设备名称")
    mountpoint: str = Field(description="挂载点")
    filesystem: str = Field(description="文件系统类型")
    total: int = Field(description="总空间(字节)")
    used: int = Field(description="已用空间(字节)")
    free: int = Field(description="可用空间(字节)")
    usage_percent: float = Field(description="磁盘使用率")


class NetworkInterface(BaseModel):
    """网络接口信息"""
    name: str = Field(description="接口名称")
    ip_address: Optional[str] = Field(default=None, description="IP地址")
    mac_address: str = Field(description="MAC地址")
    is_up: bool = Field(description="接口是否启用")
    speed: Optional[int] = Field(default=None, description="接口速度(Mbps)")
    bytes_sent: int = Field(description="发送字节数")
    bytes_recv: int = Field(description="接收字节数")
    packets_sent: int = Field(description="发送数据包数")
    packets_recv: int = Field(description="接收数据包数")


class NetworkConnectivity(BaseModel):
    """网络连通性"""
    host: str = Field(description="主机地址")
    is_reachable: bool = Field(description="是否可达")
    latency: Optional[float] = Field(default=None, description="延迟(ms)")
    packet_loss: Optional[float] = Field(default=None, description="丢包率")


class ProcessInfo(BaseModel):
    """进程信息"""
    pid: int = Field(description="进程ID")
    name: str = Field(description="进程名称")
    cpu_percent: float = Field(description="CPU使用率")
    memory_percent: float = Field(description="内存使用率")
    memory_rss: int = Field(description="物理内存(字节)")
    status: str = Field(description="进程状态")
    create_time: datetime = Field(description="创建时间")
    command_line: Optional[str] = Field(default=None, description="命令行")


class SystemInfo(BaseModel):
    """系统基本信息"""
    hostname: str = Field(description="主机名")
    platform: str = Field(description="平台")
    system: str = Field(description="操作系统")
    release: str = Field(description="系统版本")
    version: str = Field(description="详细版本")
    machine: str = Field(description="机器类型")
    processor: str = Field(description="处理器")
    boot_time: datetime = Field(description="启动时间")
    uptime: float = Field(description="运行时长(秒)")


class HardwareData(BaseModel):
    """硬件数据"""
    cpu: CPUInfo = Field(description="CPU信息")
    memory: MemoryInfo = Field(description="内存信息")
    disks: List[DiskInfo] = Field(description="磁盘信息列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")


class SystemData(BaseModel):
    """系统数据"""
    system_info: SystemInfo = Field(description="系统基本信息")
    processes: List[ProcessInfo] = Field(description="进程列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")


class NetworkData(BaseModel):
    """网络数据"""
    interfaces: List[NetworkInterface] = Field(description="网络接口列表")
    connectivity: List[NetworkConnectivity] = Field(description="连通性测试结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")


class SystemSnapshot(BaseModel):
    """系统快照 - 完整的系统状态数据"""
    hardware: HardwareData = Field(description="硬件数据")
    system: SystemData = Field(description="系统数据")
    network: NetworkData = Field(description="网络数据")
    collection_id: str = Field(description="采集ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")


class DiagnosisIssue(BaseModel):
    """诊断问题"""
    issue_id: str = Field(description="问题ID")
    category: str = Field(description="问题类别")
    severity: str = Field(description="严重程度")
    title: str = Field(description="问题标题")
    description: str = Field(description="问题描述")
    recommendation: str = Field(description="建议解决方案")
    confidence: float = Field(description="置信度")
    evidence: List[str] = Field(description="证据列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="诊断时间")


class DiagnosisResult(BaseModel):
    """诊断结果"""
    diagnosis_id: str = Field(description="诊断ID")
    system_snapshot: SystemSnapshot = Field(description="系统快照")
    issues: List[DiagnosisIssue] = Field(description="发现的问题")
    overall_health_score: float = Field(description="总体健康评分")
    agent_results: Dict[str, Any] = Field(description="智能体结果")
    reasoning_chain: List[Dict[str, Any]] = Field(description="推理链")
    diagnosis_time: float = Field(description="诊断耗时(秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="诊断时间")


# 导出所有模型
__all__ = [
    "CPUInfo",
    "MemoryInfo", 
    "DiskInfo",
    "NetworkInterface",
    "NetworkConnectivity",
    "ProcessInfo",
    "SystemInfo",
    "HardwareData",
    "SystemData",
    "NetworkData",
    "SystemSnapshot",
    "DiagnosisIssue",
    "DiagnosisResult",
]