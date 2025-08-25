"""
数据收集器模块

提供系统、硬件、网络等各类数据收集功能。
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional, AsyncGenerator, Dict, Any
from loguru import logger

from .hardware_collector import HardwareCollector
from .system_collector import SystemCollector  
from .network_collector import NetworkCollector
from models import SystemSnapshot, HardwareData, SystemData, NetworkData
from core.config_models import CollectorConfiguration


class DataCollectionManager:
    """数据收集管理器"""
    
    def __init__(self, config: CollectorConfiguration):
        """
        初始化数据收集管理器
        
        Args:
            config: 收集器配置
        """
        self.config = config
        self.hardware_collector = HardwareCollector()
        self.system_collector = SystemCollector(max_processes=config.max_processes)
        self.network_collector = NetworkCollector(timeout=config.network_timeout)
        
        self._collection_running = False
        self._last_collection_time: Optional[datetime] = None
    
    async def collect_single_snapshot(self) -> SystemSnapshot:
        """
        收集单次系统快照
        
        Returns:
            SystemSnapshot: 系统快照数据
        """
        try:
            collection_id = str(uuid.uuid4())
            logger.info(f"开始收集系统快照: {collection_id}")
            
            # 并行收集各类数据
            tasks = []
            
            if self.config.enable_hardware_monitoring:
                tasks.append(self._collect_hardware_async())
            
            if self.config.enable_system_monitoring:
                tasks.append(self._collect_system_async())
            
            if self.config.enable_network_monitoring:
                tasks.append(self._collect_network_async())
            
            # 等待所有收集任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            hardware_data = None
            system_data = None
            network_data = None
            
            task_index = 0
            if self.config.enable_hardware_monitoring:
                if isinstance(results[task_index], Exception):
                    logger.error(f"硬件数据收集失败: {results[task_index]}")
                else:
                    hardware_data = results[task_index]
                task_index += 1
            
            if self.config.enable_system_monitoring:
                if isinstance(results[task_index], Exception):
                    logger.error(f"系统数据收集失败: {results[task_index]}")
                else:
                    system_data = results[task_index]
                task_index += 1
            
            if self.config.enable_network_monitoring:
                if isinstance(results[task_index], Exception):
                    logger.error(f"网络数据收集失败: {results[task_index]}")
                else:
                    network_data = results[task_index]
                task_index += 1
            
            # 创建系统快照
            snapshot = SystemSnapshot(
                hardware=hardware_data or self._get_default_hardware_data(),
                system=system_data or self._get_default_system_data(),
                network=network_data or self._get_default_network_data(),
                collection_id=collection_id,
                timestamp=datetime.now()
            )
            
            self._last_collection_time = snapshot.timestamp
            logger.info(f"系统快照收集完成: {collection_id}")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"收集系统快照失败: {e}")
            raise
    
    async def _collect_hardware_async(self) -> HardwareData:
        """异步收集硬件数据"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.hardware_collector.collect_hardware_data)
    
    async def _collect_system_async(self) -> SystemData:
        """异步收集系统数据"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.system_collector.collect_system_data)
    
    async def _collect_network_async(self) -> NetworkData:
        """异步收集网络数据"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, 
                                        self.network_collector.collect_network_data, 
                                        self.config.ping_hosts)
    
    def _get_default_hardware_data(self) -> HardwareData:
        """获取默认硬件数据"""
        from models import CPUInfo, MemoryInfo
        return HardwareData(
            cpu=CPUInfo(usage_percent=0.0, core_count=1, frequency=0.0),
            memory=MemoryInfo(total=0, available=0, used=0, usage_percent=0.0, 
                            swap_total=0, swap_used=0),
            disks=[],
            timestamp=datetime.now()
        )
    
    def _get_default_system_data(self) -> SystemData:
        """获取默认系统数据"""
        from models import SystemInfo
        return SystemData(
            system_info=SystemInfo(
                hostname="unknown", platform="unknown", system="unknown",
                release="unknown", version="unknown", machine="unknown",
                processor="unknown", boot_time=datetime.now(), uptime=0.0
            ),
            processes=[],
            timestamp=datetime.now()
        )
    
    def _get_default_network_data(self) -> NetworkData:
        """获取默认网络数据"""
        return NetworkData(
            interfaces=[],
            connectivity=[],
            timestamp=datetime.now()
        )
    
    async def continuous_collection(self) -> AsyncGenerator[SystemSnapshot, None]:
        """
        持续数据收集
        
        Yields:
            SystemSnapshot: 系统快照数据流
        """
        self._collection_running = True
        logger.info(f"开始持续数据收集，间隔: {self.config.collection_interval}秒")
        
        try:
            while self._collection_running:
                try:
                    snapshot = await self.collect_single_snapshot()
                    yield snapshot
                    
                    # 等待下次收集
                    await asyncio.sleep(self.config.collection_interval)
                    
                except Exception as e:
                    logger.error(f"持续收集过程中出错: {e}")
                    # 等待一段时间后重试
                    await asyncio.sleep(5)
                    
        except asyncio.CancelledError:
            logger.info("持续数据收集被取消")
        finally:
            self._collection_running = False
            logger.info("持续数据收集结束")
    
    def stop_collection(self) -> None:
        """停止持续收集"""
        self._collection_running = False
        logger.info("已请求停止数据收集")
    
    def is_collecting(self) -> bool:
        """检查是否正在收集"""
        return self._collection_running
    
    def get_last_collection_time(self) -> Optional[datetime]:
        """获取最后收集时间"""
        return self._last_collection_time
    
    async def get_collection_summary(self) -> Dict[str, Any]:
        """
        获取收集摘要信息
        
        Returns:
            Dict[str, Any]: 收集摘要
        """
        try:
            # 获取各子系统摘要
            hardware_summary = self.hardware_collector.get_hardware_summary()
            system_summary = self.system_collector.get_system_summary()
            network_summary = self.network_collector.get_network_summary()
            
            return {
                "collection_status": "running" if self._collection_running else "stopped",
                "last_collection_time": self._last_collection_time.isoformat() if self._last_collection_time else None,
                "collection_interval": self.config.collection_interval,
                "enabled_collectors": {
                    "hardware": self.config.enable_hardware_monitoring,
                    "system": self.config.enable_system_monitoring,
                    "network": self.config.enable_network_monitoring,
                },
                "hardware_summary": hardware_summary,
                "system_summary": system_summary,
                "network_summary": network_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取收集摘要失败: {e}")
            return {"error": str(e)}


# 导出主要类
__all__ = [
    "HardwareCollector",
    "SystemCollector", 
    "NetworkCollector",
    "DataCollectionManager",
]