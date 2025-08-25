"""
网络信息收集器

负责收集网络接口、连通性测试等网络相关信息。
"""

import psutil
import socket
import subprocess
import time
from typing import List, Optional
from datetime import datetime
from loguru import logger

try:
    import netifaces
    HAS_NETIFACES = True
except ImportError:
    HAS_NETIFACES = False
    logger.warning("netifaces 未安装，部分网络功能将受限")

try:
    import ping3
    HAS_PING3 = True
except ImportError:
    HAS_PING3 = False
    logger.warning("ping3 未安装，将使用系统ping命令")

from models import NetworkInterface, NetworkConnectivity, NetworkData


class NetworkCollector:
    """网络信息收集器"""
    
    def __init__(self, timeout: int = 10):
        """
        初始化网络收集器
        
        Args:
            timeout: 网络超时时间(秒)
        """
        self.timeout = timeout
        
    def collect_network_interfaces(self) -> List[NetworkInterface]:
        """
        收集网络接口信息
        
        Returns:
            List[NetworkInterface]: 网络接口列表
        """
        interfaces = []
        
        try:
            # 获取网络接口统计信息
            net_io_counters = psutil.net_io_counters(pernic=True)
            
            # 获取网络接口地址信息
            net_addrs = psutil.net_if_addrs()
            
            # 获取网络接口状态
            net_stats = psutil.net_if_stats()
            
            for interface_name in net_addrs.keys():
                try:
                    # 获取地址信息
                    addrs = net_addrs[interface_name]
                    ip_address = None
                    mac_address = "00:00:00:00:00:00"
                    
                    for addr in addrs:
                        if addr.family == socket.AF_INET:  # IPv4
                            ip_address = addr.address
                        elif addr.family == psutil.AF_LINK:  # MAC地址
                            mac_address = addr.address
                    
                    # 获取接口状态
                    stats = net_stats.get(interface_name)
                    is_up = stats.isup if stats else False
                    speed = stats.speed if stats else None
                    
                    # 获取流量统计
                    io_counters = net_io_counters.get(interface_name)
                    bytes_sent = io_counters.bytes_sent if io_counters else 0
                    bytes_recv = io_counters.bytes_recv if io_counters else 0
                    packets_sent = io_counters.packets_sent if io_counters else 0
                    packets_recv = io_counters.packets_recv if io_counters else 0
                    
                    interface_info = NetworkInterface(
                        name=interface_name,
                        ip_address=ip_address,
                        mac_address=mac_address,
                        is_up=is_up,
                        speed=speed,
                        bytes_sent=bytes_sent,
                        bytes_recv=bytes_recv,
                        packets_sent=packets_sent,
                        packets_recv=packets_recv
                    )
                    
                    interfaces.append(interface_info)
                    
                except Exception as e:
                    logger.warning(f"获取接口 {interface_name} 信息失败: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"收集网络接口信息失败: {e}")
        
        return interfaces
    
    def test_connectivity(self, hosts: List[str]) -> List[NetworkConnectivity]:
        """
        测试网络连通性
        
        Args:
            hosts: 要测试的主机列表
            
        Returns:
            List[NetworkConnectivity]: 连通性测试结果
        """
        connectivity_results = []
        
        for host in hosts:
            try:
                logger.debug(f"测试连通性: {host}")
                
                if HAS_PING3:
                    # 使用ping3库
                    latency = self._ping_with_ping3(host)
                else:
                    # 使用系统ping命令
                    latency = self._ping_with_system(host)
                
                is_reachable = latency is not None
                
                connectivity = NetworkConnectivity(
                    host=host,
                    is_reachable=is_reachable,
                    latency=latency,
                    packet_loss=0.0 if is_reachable else 100.0
                )
                
                connectivity_results.append(connectivity)
                
            except Exception as e:
                logger.warning(f"测试主机 {host} 连通性失败: {e}")
                connectivity_results.append(NetworkConnectivity(
                    host=host,
                    is_reachable=False,
                    latency=None,
                    packet_loss=100.0
                ))
        
        return connectivity_results
    
    def _ping_with_ping3(self, host: str) -> Optional[float]:
        """使用ping3库进行ping测试"""
        try:
            latency = ping3.ping(host, timeout=self.timeout)
            if latency is not None:
                return latency * 1000  # 转换为毫秒
            return None
        except Exception as e:
            logger.warning(f"ping3测试失败 {host}: {e}")
            return None
    
    def _ping_with_system(self, host: str) -> Optional[float]:
        """使用系统ping命令进行测试"""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(self.timeout * 1000), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(self.timeout), host]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
            
            if result.returncode == 0:
                # 解析ping输出中的延迟
                output = result.stdout
                if system == "windows":
                    # Windows: time=XXXms
                    import re
                    match = re.search(r'time[=<](\d+)ms', output)
                    if match:
                        return float(match.group(1))
                else:
                    # Linux/Mac: time=XXX ms
                    import re
                    match = re.search(r'time=(\d+\.?\d*)', output)
                    if match:
                        return float(match.group(1))
            
            return None
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.warning(f"系统ping测试失败 {host}: {e}")
            return None
        except Exception as e:
            logger.warning(f"系统ping异常 {host}: {e}")
            return None
    
    def test_dns_resolution(self, hostname: str) -> bool:
        """
        测试DNS解析
        
        Args:
            hostname: 主机名
            
        Returns:
            bool: 是否解析成功
        """
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
        except Exception as e:
            logger.warning(f"DNS解析测试异常 {hostname}: {e}")
            return False
    
    def get_default_gateway(self) -> Optional[str]:
        """
        获取默认网关
        
        Returns:
            Optional[str]: 默认网关IP地址
        """
        try:
            if HAS_NETIFACES:
                gateways = netifaces.gateways()
                default_gateway = gateways.get('default')
                if default_gateway and netifaces.AF_INET in default_gateway:
                    return default_gateway[netifaces.AF_INET][0]
            
            # 备用方法：解析路由表
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                result = subprocess.run(["route", "print", "0.0.0.0"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    import re
                    match = re.search(r'0\.0\.0\.0\s+0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
            else:
                result = subprocess.run(["ip", "route", "show", "default"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    import re
                    match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if match:
                        return match.group(1)
                        
        except Exception as e:
            logger.warning(f"获取默认网关失败: {e}")
        
        return None
    
    def collect_network_data(self, ping_hosts: List[str]) -> NetworkData:
        """
        收集完整的网络数据
        
        Args:
            ping_hosts: 要ping测试的主机列表
            
        Returns:
            NetworkData: 网络数据对象
        """
        try:
            logger.debug("开始收集网络数据")
            
            interfaces = self.collect_network_interfaces()
            connectivity = self.test_connectivity(ping_hosts)
            
            network_data = NetworkData(
                interfaces=interfaces,
                connectivity=connectivity,
                timestamp=datetime.now()
            )
            
            logger.debug(f"网络数据收集完成，包含 {len(interfaces)} 个接口，{len(connectivity)} 个连通性测试")
            return network_data
            
        except Exception as e:
            logger.error(f"收集网络数据失败: {e}")
            raise
    
    def get_network_summary(self) -> dict:
        """
        获取网络摘要信息
        
        Returns:
            dict: 网络摘要
        """
        try:
            interfaces = self.collect_network_interfaces()
            
            # 统计活跃接口
            active_interfaces = [iface for iface in interfaces if iface.is_up and iface.ip_address]
            
            # 计算总流量
            total_bytes_sent = sum(iface.bytes_sent for iface in interfaces)
            total_bytes_recv = sum(iface.bytes_recv for iface in interfaces)
            
            # 获取默认网关
            default_gateway = self.get_default_gateway()
            
            return {
                "total_interfaces": len(interfaces),
                "active_interfaces": len(active_interfaces),
                "default_gateway": default_gateway,
                "total_bytes_sent": total_bytes_sent,
                "total_bytes_recv": total_bytes_recv,
                "primary_interface": active_interfaces[0].name if active_interfaces else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取网络摘要失败: {e}")
            return {}