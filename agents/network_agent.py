"""
网络分析智能体

专门负责网络连通性、接口状态和网络性能的分析。
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent, AgentResult, SystemDiagnosticTool
from ..models import SystemSnapshot


class NetworkAnalysisAgent(BaseAgent):
    """网络分析智能体"""
    
    def __init__(self, llm=None):
        """初始化网络分析智能体"""
        system_prompt = """
你是一个专业的网络诊断专家，专门分析网络连通性、性能和安全状态。

你的主要职责：
1. 分析网络接口状态和配置
2. 测试网络连通性和延迟
3. 监控网络流量和性能指标
4. 识别网络安全风险和异常
5. 提供网络优化和故障排除建议

分析时要考虑：
- 网络接口的可用性和配置
- 连通性测试结果和延迟指标
- 网络流量模式和异常
- 潜在的安全威胁
- 性能优化机会

请始终保持专业和准确，提供可执行的建议。
        """
        
        tools = [
            SystemDiagnosticTool.get_network_analysis_tool(),
        ]
        
        super().__init__(
            name="network_analyst",
            llm=llm,
            tools=tools,
            system_prompt=system_prompt
        )
    
    async def execute_task(self, task_input: Dict[str, Any]) -> AgentResult:
        """
        执行网络分析任务
        
        Args:
            task_input: 包含系统快照的任务输入
            
        Returns:
            AgentResult: 分析结果
        """
        start_time = datetime.now()
        task_id = task_input.get('task_id', 'network_analysis')
        
        try:
            logger.info(f"网络分析智能体开始执行任务: {task_id}")
            
            # 清除历史记录
            self.clear_history()
            
            # 获取系统快照
            snapshot = task_input.get('system_snapshot')
            if not snapshot:
                raise ValueError("缺少系统快照数据")
            
            # 分析网络数据
            analysis_result = await self._analyze_network_data(snapshot)
            
            # 计算整体置信度
            confidence_score = self._calculate_confidence_score()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                task_id=task_id,
                success=True,
                result=analysis_result,
                reasoning_chain=self._reasoning_steps.copy(),
                tool_calls=self._tool_calls.copy(),
                confidence_score=confidence_score,
                execution_time=execution_time
            )
            
        except Exception as e:
            logger.error(f"网络分析任务执行失败: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResult(
                agent_name=self.name,
                task_id=task_id,
                success=False,
                result={},
                reasoning_chain=self._reasoning_steps.copy(),
                tool_calls=self._tool_calls.copy(),
                confidence_score=0.0,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def execute_with_reasoning(self, input_data: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行带有推理过程的网络分析
        
        Args:
            input_data: 系统快照JSON数据
            
        Yields:
            Dict[str, Any]: 推理过程和结果
        """
        try:
            # 解析输入数据
            snapshot_data = json.loads(input_data)
            
            yield {
                "type": "reasoning_start",
                "agent_name": self.name,
                "message": "开始网络分析推理",
                "timestamp": datetime.now().isoformat()
            }
            
            # 第一步：理解问题
            self.add_reasoning_step(
                "问题理解",
                "需要分析网络连通性、接口状态和网络性能",
                confidence=0.9,
                evidence=["收到完整的网络状态数据"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "问题理解",
                "content": "分析网络连通性和性能状态",
                "confidence": 0.9
            }
            
            # 第二步：网络接口分析
            network_data = snapshot_data.get('network', {})
            interfaces = network_data.get('interfaces', [])
            
            interface_analysis = await self._analyze_interfaces_with_reasoning(interfaces)
            
            yield {
                "type": "reasoning_step",
                "step": "网络接口分析",
                "content": interface_analysis,
                "confidence": 0.8
            }
            
            # 第三步：连通性测试分析
            connectivity = network_data.get('connectivity', [])
            connectivity_analysis = await self._analyze_connectivity_with_reasoning(connectivity)
            
            yield {
                "type": "reasoning_step",
                "step": "连通性测试分析",
                "content": connectivity_analysis,
                "confidence": 0.8
            }
            
            # 第四步：网络性能分析
            performance_analysis = await self._analyze_network_performance_with_reasoning(interfaces, connectivity)
            
            yield {
                "type": "reasoning_step",
                "step": "网络性能分析",
                "content": performance_analysis,
                "confidence": 0.8
            }
            
            # 第五步：综合诊断
            overall_diagnosis = self._generate_network_diagnosis(interface_analysis, connectivity_analysis, performance_analysis)
            
            self.add_reasoning_step(
                "综合诊断",
                overall_diagnosis,
                confidence=0.85,
                evidence=["接口分析结果", "连通性测试结果", "性能分析结果"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "综合诊断",
                "content": overall_diagnosis,
                "confidence": 0.85
            }
            
            # 最终结果
            final_result = {
                "interface_analysis": interface_analysis,
                "connectivity_analysis": connectivity_analysis,
                "performance_analysis": performance_analysis,
                "overall_diagnosis": overall_diagnosis,
                "confidence_score": 0.85
            }
            
            yield {
                "type": "reasoning_complete",
                "result": final_result,
                "confidence": 0.85,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                "type": "reasoning_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_network_data(self, snapshot: SystemSnapshot) -> Dict[str, Any]:
        """分析网络数据"""
        try:
            network_data = snapshot.network
            
            # 分析网络接口
            interface_analysis = await self._analyze_interfaces(network_data.interfaces)
            
            # 分析连通性
            connectivity_analysis = await self._call_network_analysis_tool(network_data.dict())
            
            # 分析网络性能
            performance_analysis = self._analyze_network_performance(network_data.interfaces, network_data.connectivity)
            
            # 生成网络建议
            recommendations = self._generate_network_recommendations(
                [iface.dict() for iface in network_data.interfaces],
                [conn.dict() for conn in network_data.connectivity]
            )
            
            return {
                "interface_analysis": interface_analysis,
                "connectivity_analysis": connectivity_analysis,
                "performance_analysis": performance_analysis,
                "recommendations": recommendations,
                "network_score": self._calculate_network_score(network_data)
            }
            
        except Exception as e:
            logger.error(f"网络数据分析失败: {e}")
            raise
    
    async def _analyze_interfaces(self, interfaces) -> str:
        """分析网络接口"""
        if not interfaces:
            return "网络接口分析: 未检测到网络接口"
        
        active_interfaces = [iface for iface in interfaces if iface.is_up]
        configured_interfaces = [iface for iface in interfaces if iface.ip_address]
        
        analysis = []
        analysis.append(f"总接口数: {len(interfaces)}")
        analysis.append(f"活跃接口: {len(active_interfaces)}")
        analysis.append(f"已配置IP: {len(configured_interfaces)}")
        
        if len(active_interfaces) == 0:
            analysis.append("警告: 没有活跃的网络接口")
        elif len(configured_interfaces) == 0:
            analysis.append("警告: 没有配置IP地址的接口")
        
        return f"网络接口分析: {'; '.join(analysis)}"
    
    async def _analyze_interfaces_with_reasoning(self, interfaces: List[Dict[str, Any]]) -> str:
        """带推理的网络接口分析"""
        if not interfaces:
            return "网络接口分析: 未检测到网络接口数据"
        
        # 统计接口状态
        total_interfaces = len(interfaces)
        active_interfaces = [iface for iface in interfaces if iface.get('is_up', False)]
        configured_interfaces = [iface for iface in interfaces if iface.get('ip_address')]
        wireless_interfaces = [iface for iface in interfaces if 'wifi' in iface.get('name', '').lower() or 'wireless' in iface.get('name', '').lower()]
        
        reasoning = []
        reasoning.append(f"检测到{total_interfaces}个网络接口")
        
        if len(active_interfaces) == 0:
            reasoning.append("严重问题: 没有活跃的网络接口")
        elif len(active_interfaces) == total_interfaces:
            reasoning.append("所有接口均处于活跃状态")
        else:
            reasoning.append(f"{len(active_interfaces)}个接口活跃，{total_interfaces - len(active_interfaces)}个接口未启用")
        
        if len(configured_interfaces) == 0:
            reasoning.append("警告: 没有配置IP地址的接口")
        else:
            reasoning.append(f"{len(configured_interfaces)}个接口已配置IP")
        
        if wireless_interfaces:
            reasoning.append(f"检测到{len(wireless_interfaces)}个无线接口")
        
        # 流量分析
        high_traffic_interfaces = [iface for iface in interfaces if iface.get('bytes_sent', 0) + iface.get('bytes_recv', 0) > 1024*1024*1024]  # 1GB
        if high_traffic_interfaces:
            reasoning.append(f"{len(high_traffic_interfaces)}个接口有高流量")
        
        analysis = f"网络接口分析: {'; '.join(reasoning)}"
        
        evidence = [
            f"总接口: {total_interfaces}",
            f"活跃接口: {len(active_interfaces)}",
            f"已配置IP: {len(configured_interfaces)}",
            f"无线接口: {len(wireless_interfaces)}"
        ]
        
        self.add_reasoning_step(
            "接口分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    async def _call_network_analysis_tool(self, network_data: Dict[str, Any]) -> str:
        """调用网络分析工具"""
        start_time = datetime.now()
        try:
            network_tool = SystemDiagnosticTool.get_network_analysis_tool()
            result = network_tool.func(json.dumps(network_data))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_network", network_data, result, execution_time, True)
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_network", network_data, None, execution_time, False, str(e))
            return f"网络分析失败: {e}"
    
    async def _analyze_connectivity_with_reasoning(self, connectivity: List[Dict[str, Any]]) -> str:
        """带推理的连通性分析"""
        if not connectivity:
            return "连通性分析: 未进行连通性测试"
        
        # 统计连通性结果
        total_tests = len(connectivity)
        successful_tests = [test for test in connectivity if test.get('is_reachable', False)]
        failed_tests = [test for test in connectivity if not test.get('is_reachable', False)]
        
        reasoning = []
        reasoning.append(f"进行了{total_tests}项连通性测试")
        
        if len(successful_tests) == 0:
            reasoning.append("严重问题: 所有连通性测试失败，网络可能断开")
        elif len(failed_tests) == 0:
            reasoning.append("所有连通性测试成功，网络状态良好")
        else:
            reasoning.append(f"{len(successful_tests)}项成功，{len(failed_tests)}项失败")
        
        # 延迟分析
        latencies = [test.get('latency', 0) for test in successful_tests if test.get('latency')]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            if avg_latency > 200:
                reasoning.append(f"网络延迟较高(平均{avg_latency:.1f}ms)")
            elif avg_latency > 100:
                reasoning.append(f"网络延迟适中(平均{avg_latency:.1f}ms)")
            else:
                reasoning.append(f"网络延迟良好(平均{avg_latency:.1f}ms)")
            
            if max_latency > 500:
                reasoning.append(f"检测到异常高延迟({max_latency:.1f}ms)")
        
        # 失败的主机分析
        if failed_tests:
            failed_hosts = [test.get('host', 'unknown') for test in failed_tests]
            reasoning.append(f"无法连接的主机: {', '.join(failed_hosts[:3])}")
        
        analysis = f"连通性分析: {'; '.join(reasoning)}"
        
        evidence = [
            f"测试总数: {total_tests}",
            f"成功: {len(successful_tests)}",
            f"失败: {len(failed_tests)}",
            f"平均延迟: {sum(latencies)/len(latencies):.1f}ms" if latencies else "无延迟数据"
        ]
        
        self.add_reasoning_step(
            "连通性分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    def _analyze_network_performance(self, interfaces, connectivity) -> str:
        """分析网络性能"""
        try:
            performance_issues = []
            
            # 分析接口性能
            for iface in interfaces:
                if iface.is_up and iface.speed:
                    if iface.speed < 100:  # 小于100Mbps
                        performance_issues.append(f"{iface.name}接口速度较低({iface.speed}Mbps)")
            
            # 分析延迟
            latencies = [conn.latency for conn in connectivity if conn.is_reachable and conn.latency]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                if avg_latency > 200:
                    performance_issues.append(f"网络延迟过高(平均{avg_latency:.1f}ms)")
            
            if performance_issues:
                return f"网络性能分析: 发现问题 - {'; '.join(performance_issues)}"
            else:
                return "网络性能分析: 性能状态良好"
                
        except Exception as e:
            return f"网络性能分析失败: {e}"
    
    async def _analyze_network_performance_with_reasoning(self, interfaces: List[Dict[str, Any]], connectivity: List[Dict[str, Any]]) -> str:
        """带推理的网络性能分析"""
        reasoning = []
        performance_score = 1.0
        
        # 接口速度分析
        speed_issues = []
        for iface in interfaces:
            if iface.get('is_up', False) and iface.get('speed'):
                speed = iface.get('speed', 0)
                name = iface.get('name', 'unknown')
                
                if speed < 100:
                    speed_issues.append(f"{name}({speed}Mbps)")
                    performance_score *= 0.7
                elif speed < 1000:
                    performance_score *= 0.9
        
        if speed_issues:
            reasoning.append(f"低速接口: {', '.join(speed_issues)}")
        else:
            reasoning.append("接口速度正常")
        
        # 延迟性能分析
        latencies = [test.get('latency', 0) for test in connectivity if test.get('is_reachable', False) and test.get('latency')]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            max_latency = max(latencies)
            
            if avg_latency > 200:
                reasoning.append(f"延迟过高(平均{avg_latency:.1f}ms)")
                performance_score *= 0.6
            elif avg_latency > 100:
                reasoning.append(f"延迟适中(平均{avg_latency:.1f}ms)")
                performance_score *= 0.8
            else:
                reasoning.append(f"延迟良好(平均{avg_latency:.1f}ms)")
            
            if max_latency > 500:
                reasoning.append(f"检测到极高延迟({max_latency:.1f}ms)")
                performance_score *= 0.5
        else:
            reasoning.append("无延迟数据")
        
        # 数据包丢失分析
        packet_loss_tests = [test for test in connectivity if test.get('packet_loss', 0) > 0]
        if packet_loss_tests:
            avg_loss = sum(test.get('packet_loss', 0) for test in packet_loss_tests) / len(packet_loss_tests)
            reasoning.append(f"检测到数据包丢失(平均{avg_loss:.1f}%)")
            performance_score *= (1 - avg_loss / 100)
        
        # 流量分析
        high_traffic_interfaces = []
        for iface in interfaces:
            bytes_total = iface.get('bytes_sent', 0) + iface.get('bytes_recv', 0)
            if bytes_total > 1024*1024*1024:  # 1GB
                high_traffic_interfaces.append(iface.get('name', 'unknown'))
        
        if high_traffic_interfaces:
            reasoning.append(f"高流量接口: {', '.join(high_traffic_interfaces)}")
        
        # 综合性能评估
        if performance_score > 0.8:
            reasoning.append("网络性能良好")
        elif performance_score > 0.6:
            reasoning.append("网络性能一般")
        else:
            reasoning.append("网络性能较差")
        
        analysis = f"网络性能分析: {'; '.join(reasoning)}，性能评分: {performance_score:.2f}"
        
        evidence = [
            f"接口数: {len(interfaces)}",
            f"平均延迟: {sum(latencies)/len(latencies):.1f}ms" if latencies else "无延迟数据",
            f"性能评分: {performance_score:.2f}",
            f"高流量接口: {len(high_traffic_interfaces)}个"
        ]
        
        self.add_reasoning_step(
            "性能分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    def _generate_network_diagnosis(self, interface_analysis: str, connectivity_analysis: str, performance_analysis: str) -> str:
        """生成网络综合诊断"""
        issues = []
        
        if "没有活跃" in interface_analysis or "严重问题" in interface_analysis:
            issues.append("网络接口配置问题")
        
        if "失败" in connectivity_analysis or "断开" in connectivity_analysis:
            issues.append("网络连通性问题")
        
        if "过高" in performance_analysis or "较差" in performance_analysis:
            issues.append("网络性能问题")
        
        if issues:
            diagnosis = f"检测到网络问题: {', '.join(issues)}。建议检查网络配置和连接状态。"
        else:
            diagnosis = "网络状态良好，连通性和性能正常。"
        
        return diagnosis
    
    def _generate_network_recommendations(self, interfaces: List[Dict], connectivity: List[Dict]) -> List[str]:
        """生成网络建议"""
        recommendations = []
        
        # 接口建议
        active_interfaces = [iface for iface in interfaces if iface.get('is_up', False)]
        if len(active_interfaces) == 0:
            recommendations.append("检查网络线缆连接和网络驱动")
        
        configured_interfaces = [iface for iface in interfaces if iface.get('ip_address')]
        if len(configured_interfaces) == 0:
            recommendations.append("配置网络接口IP地址")
        
        # 连通性建议
        failed_tests = [test for test in connectivity if not test.get('is_reachable', False)]
        if failed_tests:
            recommendations.append("检查DNS设置和防火墙配置")
        
        # 性能建议
        latencies = [test.get('latency', 0) for test in connectivity if test.get('is_reachable', False) and test.get('latency')]
        if latencies and sum(latencies)/len(latencies) > 200:
            recommendations.append("优化网络路由或联系网络服务提供商")
        
        # 速度建议
        slow_interfaces = [iface for iface in interfaces if iface.get('is_up', False) and iface.get('speed', 0) < 100]
        if slow_interfaces:
            recommendations.append("考虑升级网络设备以提高带宽")
        
        if not recommendations:
            recommendations.append("网络配置良好，继续监控")
        
        return recommendations
    
    def _calculate_network_score(self, network_data) -> float:
        """计算网络健康评分"""
        scores = []
        
        # 接口评分
        interfaces = network_data.interfaces
        if interfaces:
            active_count = len([iface for iface in interfaces if iface.is_up])
            if active_count > 0:
                scores.append(min(1.0, active_count / len(interfaces)))
            else:
                scores.append(0.0)
        
        # 连通性评分
        connectivity = network_data.connectivity
        if connectivity:
            success_count = len([test for test in connectivity if test.is_reachable])
            scores.append(success_count / len(connectivity))
        
        # 延迟评分
        latencies = [test.latency for test in connectivity if test.is_reachable and test.latency]
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            if avg_latency < 50:
                scores.append(1.0)
            elif avg_latency < 100:
                scores.append(0.8)
            elif avg_latency < 200:
                scores.append(0.6)
            else:
                scores.append(0.3)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_confidence_score(self) -> float:
        """计算置信度评分"""
        if not self._reasoning_steps:
            return 0.5
        
        confidences = [step.confidence for step in self._reasoning_steps]
        return sum(confidences) / len(confidences)