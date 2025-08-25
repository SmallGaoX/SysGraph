"""
硬件信息收集器

负责收集CPU、内存、磁盘等硬件信息。
"""

import psutil
import platform
from datetime import datetime
from typing import List, Optional
from loguru import logger

from models import CPUInfo, MemoryInfo, DiskInfo, HardwareData


class HardwareCollector:
    """硬件信息收集器"""
    
    def __init__(self):
        """初始化硬件收集器"""
        self._last_cpu_times = None
        
    def collect_cpu_info(self) -> CPUInfo:
        """
        收集CPU信息
        
        Returns:
            CPUInfo: CPU信息对象
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # CPU核心数
            core_count = psutil.cpu_count(logical=True)
            
            # CPU频率
            cpu_freq = psutil.cpu_freq()
            frequency = cpu_freq.current if cpu_freq else 0.0
            
            # 负载平均值（仅Linux/Mac）
            load_average = None
            try:
                if hasattr(psutil, 'getloadavg'):
                    load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                pass
            
            # CPU温度（如果可用）
            temperature = None
            try:
                sensors = psutil.sensors_temperatures()
                if sensors:
                    # 尝试获取主要CPU温度
                    for name, entries in sensors.items():
                        if 'cpu' in name.lower() or 'core' in name.lower():
                            if entries:
                                temperature = entries[0].current
                                break
            except (AttributeError, OSError):
                pass
            
            return CPUInfo(
                usage_percent=cpu_percent,
                core_count=core_count,
                frequency=frequency,
                temperature=temperature,
                load_average=load_average
            )
            
        except Exception as e:
            logger.error(f"收集CPU信息失败: {e}")
            # 返回默认值
            return CPUInfo(
                usage_percent=0.0,
                core_count=1,
                frequency=0.0
            )
    
    def collect_memory_info(self) -> MemoryInfo:
        """
        收集内存信息
        
        Returns:
            MemoryInfo: 内存信息对象
        """
        try:
            # 虚拟内存
            memory = psutil.virtual_memory()
            
            # 交换分区
            swap = psutil.swap_memory()
            
            return MemoryInfo(
                total=memory.total,
                available=memory.available,
                used=memory.used,
                usage_percent=memory.percent,
                swap_total=swap.total,
                swap_used=swap.used
            )
            
        except Exception as e:
            logger.error(f"收集内存信息失败: {e}")
            # 返回默认值
            return MemoryInfo(
                total=0,
                available=0,
                used=0,
                usage_percent=0.0,
                swap_total=0,
                swap_used=0
            )
    
    def collect_disk_info(self) -> List[DiskInfo]:
        """
        收集磁盘信息
        
        Returns:
            List[DiskInfo]: 磁盘信息列表
        """
        disks = []
        
        try:
            # 获取所有磁盘分区
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    # 获取分区使用情况
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    disk_info = DiskInfo(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        filesystem=partition.fstype,
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                        usage_percent=(usage.used / usage.total) * 100 if usage.total > 0 else 0.0
                    )
                    
                    disks.append(disk_info)
                    
                except (PermissionError, OSError) as e:
                    logger.warning(f"无法访问分区 {partition.device}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"收集磁盘信息失败: {e}")
        
        return disks
    
    def collect_hardware_data(self) -> HardwareData:
        """
        收集完整的硬件数据
        
        Returns:
            HardwareData: 硬件数据对象
        """
        try:
            logger.debug("开始收集硬件数据")
            
            cpu_info = self.collect_cpu_info()
            memory_info = self.collect_memory_info()
            disk_info = self.collect_disk_info()
            
            hardware_data = HardwareData(
                cpu=cpu_info,
                memory=memory_info,
                disks=disk_info,
                timestamp=datetime.now()
            )
            
            logger.debug("硬件数据收集完成")
            return hardware_data
            
        except Exception as e:
            logger.error(f"收集硬件数据失败: {e}")
            raise
    
    def get_hardware_summary(self) -> dict:
        """
        获取硬件摘要信息
        
        Returns:
            dict: 硬件摘要
        """
        try:
            hardware_data = self.collect_hardware_data()
            
            total_disk_space = sum(disk.total for disk in hardware_data.disks)
            used_disk_space = sum(disk.used for disk in hardware_data.disks)
            disk_usage_percent = (used_disk_space / total_disk_space) * 100 if total_disk_space > 0 else 0
            
            return {
                "cpu_usage": hardware_data.cpu.usage_percent,
                "cpu_cores": hardware_data.cpu.core_count,
                "memory_usage": hardware_data.memory.usage_percent,
                "memory_total_gb": hardware_data.memory.total / (1024**3),
                "disk_usage": disk_usage_percent,
                "disk_total_gb": total_disk_space / (1024**3),
                "timestamp": hardware_data.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取硬件摘要失败: {e}")
            return {}