"""
系统信息收集器

负责收集系统基本信息、进程信息等。
"""

import psutil
import platform
import socket
from datetime import datetime
from typing import List, Optional
from loguru import logger

from models import SystemInfo, ProcessInfo, SystemData


class SystemCollector:
    """系统信息收集器"""
    
    def __init__(self, max_processes: int = 100):
        """
        初始化系统收集器
        
        Args:
            max_processes: 最大进程监控数量
        """
        self.max_processes = max_processes
        
    def collect_system_info(self) -> SystemInfo:
        """
        收集系统基本信息
        
        Returns:
            SystemInfo: 系统信息对象
        """
        try:
            # 获取启动时间
            boot_timestamp = psutil.boot_time()
            boot_time = datetime.fromtimestamp(boot_timestamp)
            
            # 计算运行时长
            uptime = (datetime.now() - boot_time).total_seconds()
            
            # 获取主机名
            hostname = socket.gethostname()
            
            return SystemInfo(
                hostname=hostname,
                platform=platform.platform(),
                system=platform.system(),
                release=platform.release(),
                version=platform.version(),
                machine=platform.machine(),
                processor=platform.processor(),
                boot_time=boot_time,
                uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"收集系统信息失败: {e}")
            # 返回默认值
            return SystemInfo(
                hostname="unknown",
                platform="unknown",
                system="unknown",
                release="unknown",
                version="unknown",
                machine="unknown",
                processor="unknown",
                boot_time=datetime.now(),
                uptime=0.0
            )
    
    def collect_processes_info(self) -> List[ProcessInfo]:
        """
        收集进程信息
        
        Returns:
            List[ProcessInfo]: 进程信息列表
        """
        processes = []
        
        try:
            # 获取所有进程
            all_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'memory_info', 'status', 'create_time', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # 计算CPU使用率，处理None值
                    cpu_percent = proc_info.get('cpu_percent')
                    if cpu_percent is None:
                        cpu_percent = 0.0
                    
                    # 获取内存信息，处理None值
                    memory_info = proc_info.get('memory_info')
                    memory_rss = memory_info.rss if memory_info else 0
                    memory_percent = proc_info.get('memory_percent')
                    if memory_percent is None:
                        memory_percent = 0.0
                    
                    # 创建时间
                    create_timestamp = proc_info.get('create_time', 0)
                    create_time = datetime.fromtimestamp(create_timestamp)
                    
                    # 命令行
                    cmdline = proc_info.get('cmdline')
                    command_line = ' '.join(cmdline) if cmdline else None
                    
                    process_info = ProcessInfo(
                        pid=proc_info['pid'],
                        name=proc_info['name'] or 'unknown',
                        cpu_percent=cpu_percent,
                        memory_percent=memory_percent,
                        memory_rss=memory_rss,
                        status=proc_info.get('status', 'unknown'),
                        create_time=create_time,
                        command_line=command_line
                    )
                    
                    all_processes.append((process_info, cpu_percent, memory_percent))
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception as e:
                    logger.warning(f"获取进程信息失败: {e}")
                    continue
            
            # 按CPU使用率排序，取前N个
            all_processes.sort(key=lambda x: x[1] + x[2], reverse=True)
            processes = [proc[0] for proc in all_processes[:self.max_processes]]
            
        except Exception as e:
            logger.error(f"收集进程信息失败: {e}")
        
        return processes
    
    def collect_system_data(self) -> SystemData:
        """
        收集完整的系统数据
        
        Returns:
            SystemData: 系统数据对象
        """
        try:
            logger.debug("开始收集系统数据")
            
            system_info = self.collect_system_info()
            processes = self.collect_processes_info()
            
            system_data = SystemData(
                system_info=system_info,
                processes=processes,
                timestamp=datetime.now()
            )
            
            logger.debug(f"系统数据收集完成，包含 {len(processes)} 个进程")
            return system_data
            
        except Exception as e:
            logger.error(f"收集系统数据失败: {e}")
            raise
    
    def get_top_processes_by_cpu(self, count: int = 10) -> List[ProcessInfo]:
        """
        获取CPU使用率最高的进程
        
        Args:
            count: 返回的进程数量
            
        Returns:
            List[ProcessInfo]: 进程列表
        """
        try:
            processes = self.collect_processes_info()
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
            return processes[:count]
        except Exception as e:
            logger.error(f"获取CPU高使用率进程失败: {e}")
            return []
    
    def get_top_processes_by_memory(self, count: int = 10) -> List[ProcessInfo]:
        """
        获取内存使用率最高的进程
        
        Args:
            count: 返回的进程数量
            
        Returns:
            List[ProcessInfo]: 进程列表
        """
        try:
            processes = self.collect_processes_info()
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
            return processes[:count]
        except Exception as e:
            logger.error(f"获取内存高使用率进程失败: {e}")
            return []
    
    def get_system_summary(self) -> dict:
        """
        获取系统摘要信息
        
        Returns:
            dict: 系统摘要
        """
        try:
            system_data = self.collect_system_data()
            
            # 计算进程统计
            total_processes = len(system_data.processes)
            running_processes = len([p for p in system_data.processes if p.status == 'running'])
            
            # CPU和内存使用率最高的进程
            top_cpu_process = max(system_data.processes, key=lambda x: x.cpu_percent, default=None)
            top_memory_process = max(system_data.processes, key=lambda x: x.memory_percent, default=None)
            
            return {
                "hostname": system_data.system_info.hostname,
                "platform": system_data.system_info.platform,
                "uptime_hours": system_data.system_info.uptime / 3600,
                "total_processes": total_processes,
                "running_processes": running_processes,
                "top_cpu_process": {
                    "name": top_cpu_process.name,
                    "cpu_percent": top_cpu_process.cpu_percent
                } if top_cpu_process else None,
                "top_memory_process": {
                    "name": top_memory_process.name,
                    "memory_percent": top_memory_process.memory_percent
                } if top_memory_process else None,
                "timestamp": system_data.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统摘要失败: {e}")
            return {}