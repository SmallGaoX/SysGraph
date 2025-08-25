"""
系统分析智能体

专门负责系统进程、服务和运行状态的分析。
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime, timedelta
from loguru import logger

from .base_agent import BaseAgent, AgentResult, SystemDiagnosticTool
from ..models import SystemSnapshot


class SystemAnalysisAgent(BaseAgent):
    """系统分析智能体"""
    
    def __init__(self, llm=None):
        """初始化系统分析智能体"""
        system_prompt = """
你是一个专业的系统诊断专家，专门分析操作系统运行状态和进程管理。

你的主要职责：
1. 分析系统运行时间和稳定性
2. 监控进程状态和资源占用
3. 识别异常进程和潜在安全风险
4. 评估系统负载和性能瓶颈
5. 提供系统优化和维护建议

分析时要考虑：
- 系统运行时间和稳定性指标
- 进程资源使用的合理性
- 异常进程的识别和处理
- 系统负载分布和均衡性
- 安全风险和性能优化

请始终保持专业和准确，提供可执行的建议。
        """
        
        tools = [
            SystemDiagnosticTool.get_process_analysis_tool(),
        ]
        
        super().__init__(
            name="system_analyst",
            llm=llm,
            tools=tools,
            system_prompt=system_prompt
        )
    
    async def execute_task(self, task_input: Dict[str, Any]) -> AgentResult:
        """
        执行系统分析任务
        
        Args:
            task_input: 包含系统快照的任务输入
            
        Returns:
            AgentResult: 分析结果
        """
        start_time = datetime.now()
        task_id = task_input.get('task_id', 'system_analysis')
        
        try:
            logger.info(f"系统分析智能体开始执行任务: {task_id}")
            
            # 清除历史记录
            self.clear_history()
            
            # 获取系统快照
            snapshot = task_input.get('system_snapshot')
            if not snapshot:
                raise ValueError("缺少系统快照数据")
            
            # 分析系统数据
            analysis_result = await self._analyze_system_data(snapshot)
            
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
            logger.error(f"系统分析任务执行失败: {e}")
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
        执行带有推理过程的系统分析
        
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
                "message": "开始系统分析推理",
                "timestamp": datetime.now().isoformat()
            }
            
            # 第一步：理解问题
            self.add_reasoning_step(
                "问题理解",
                "需要分析系统运行状态，包括进程管理、系统稳定性和性能状况",
                confidence=0.9,
                evidence=["收到完整的系统状态数据"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "问题理解",
                "content": "分析系统运行状态和进程管理",
                "confidence": 0.9
            }
            
            # 第二步：系统基础信息分析
            system_data = snapshot_data.get('system', {})
            system_info = system_data.get('system_info', {})
            
            uptime_analysis = await self._analyze_uptime_with_reasoning(system_info)
            
            yield {
                "type": "reasoning_step",
                "step": "系统运行时间分析",
                "content": uptime_analysis,
                "confidence": 0.8
            }
            
            # 第三步：进程分析
            processes = system_data.get('processes', [])
            process_analysis = await self._analyze_processes_with_reasoning(processes)
            
            yield {
                "type": "reasoning_step",
                "step": "进程状态分析",
                "content": process_analysis,
                "confidence": 0.8
            }
            
            # 第四步：系统负载分析
            load_analysis = await self._analyze_system_load_with_reasoning(processes, system_info)
            
            yield {
                "type": "reasoning_step",
                "step": "系统负载分析",
                "content": load_analysis,
                "confidence": 0.8
            }
            
            # 第五步：综合诊断
            overall_diagnosis = self._generate_system_diagnosis(uptime_analysis, process_analysis, load_analysis)
            
            self.add_reasoning_step(
                "综合诊断",
                overall_diagnosis,
                confidence=0.85,
                evidence=["运行时间分析", "进程状态分析", "系统负载分析"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "综合诊断",
                "content": overall_diagnosis,
                "confidence": 0.85
            }
            
            # 最终结果
            final_result = {
                "uptime_analysis": uptime_analysis,
                "process_analysis": process_analysis,
                "load_analysis": load_analysis,
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
    
    async def _analyze_system_data(self, snapshot: SystemSnapshot) -> Dict[str, Any]:
        """分析系统数据"""
        try:
            system_data = snapshot.system
            
            # 分析系统基础信息
            uptime_analysis = await self._analyze_uptime(system_data.system_info.dict())
            
            # 分析进程状态
            process_analysis = await self._call_process_analysis_tool([p.dict() for p in system_data.processes])
            
            # 分析系统负载
            load_analysis = self._analyze_system_load(system_data.processes, system_data.system_info)
            
            # 生成系统建议
            recommendations = self._generate_system_recommendations(
                system_data.system_info.dict(),
                [p.dict() for p in system_data.processes]
            )
            
            return {
                "uptime_analysis": uptime_analysis,
                "process_analysis": process_analysis,
                "load_analysis": load_analysis,
                "recommendations": recommendations,
                "system_score": self._calculate_system_score(system_data)
            }
            
        except Exception as e:
            logger.error(f"系统数据分析失败: {e}")
            raise
    
    async def _analyze_uptime(self, system_info: Dict[str, Any]) -> str:
        """分析系统运行时间"""
        uptime_seconds = system_info.get('uptime', 0)
        uptime_hours = uptime_seconds / 3600
        uptime_days = uptime_hours / 24
        
        if uptime_days > 30:
            return f"系统运行时间过长({uptime_days:.1f}天)，建议重启以清理内存和更新系统"
        elif uptime_days > 7:
            return f"系统运行时间较长({uptime_days:.1f}天)，运行稳定"
        elif uptime_hours > 1:
            return f"系统运行时间正常({uptime_hours:.1f}小时)，状态良好"
        else:
            return "系统刚启动，需要观察稳定性"
    
    async def _analyze_uptime_with_reasoning(self, system_info: Dict[str, Any]) -> str:
        """带推理的系统运行时间分析"""
        uptime_seconds = system_info.get('uptime', 0)
        uptime_hours = uptime_seconds / 3600
        uptime_days = uptime_hours / 24
        
        reasoning = []
        if uptime_days > 30:
            reasoning.append("运行时间过长，可能存在内存泄漏或需要更新")
        elif uptime_days > 7:
            reasoning.append("运行时间适中，系统较为稳定")
        elif uptime_hours > 1:
            reasoning.append("运行时间正常")
        else:
            reasoning.append("系统刚启动，需要监控")
        
        boot_time = system_info.get('boot_time', '')
        platform_info = system_info.get('platform', 'unknown')
        
        analysis = f"系统运行时间分析: {'; '.join(reasoning)}。运行{uptime_days:.1f}天，平台: {platform_info}"
        
        self.add_reasoning_step(
            "运行时间分析",
            analysis,
            confidence=0.9,
            evidence=[f"运行时间: {uptime_days:.1f}天", f"平台: {platform_info}"]
        )
        
        return analysis
    
    async def _call_process_analysis_tool(self, process_data: List[Dict[str, Any]]) -> str:
        """调用进程分析工具"""
        start_time = datetime.now()
        try:
            process_tool = SystemDiagnosticTool.get_process_analysis_tool()
            result = process_tool.func(json.dumps(process_data))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_processes", {"processes": process_data}, result, execution_time, True)
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_processes", {"processes": process_data}, None, execution_time, False, str(e))
            return f"进程分析失败: {e}"
    
    async def _analyze_processes_with_reasoning(self, processes: List[Dict[str, Any]]) -> str:
        """带推理的进程分析"""
        if not processes:
            return "进程分析: 未检测到进程数据"
        
        # 统计进程状态
        running_count = len([p for p in processes if p.get('status') == 'running'])
        sleeping_count = len([p for p in processes if p.get('status') == 'sleeping'])
        total_count = len(processes)
        
        # 找出资源占用高的进程
        high_cpu_processes = [p for p in processes if p.get('cpu_percent', 0) > 50]
        high_memory_processes = [p for p in processes if p.get('memory_percent', 0) > 10]
        
        reasoning = []
        reasoning.append(f"总进程数: {total_count}, 运行中: {running_count}, 休眠: {sleeping_count}")
        
        if high_cpu_processes:
            cpu_names = [p.get('name', 'unknown') for p in high_cpu_processes[:3]]
            reasoning.append(f"高CPU进程: {', '.join(cpu_names)}")
        
        if high_memory_processes:
            mem_names = [p.get('name', 'unknown') for p in high_memory_processes[:3]]
            reasoning.append(f"高内存进程: {', '.join(mem_names)}")
        
        if not high_cpu_processes and not high_memory_processes:
            reasoning.append("进程资源使用正常")
        
        analysis = f"进程状态分析: {'; '.join(reasoning)}"
        
        evidence = [
            f"总进程: {total_count}",
            f"运行中: {running_count}",
            f"高CPU进程: {len(high_cpu_processes)}个",
            f"高内存进程: {len(high_memory_processes)}个"
        ]
        
        self.add_reasoning_step(
            "进程分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    def _analyze_system_load(self, processes, system_info) -> str:
        """分析系统负载"""
        try:
            # 计算总体资源使用
            total_cpu = sum(p.cpu_percent for p in processes)
            total_memory = sum(p.memory_percent for p in processes)
            
            analysis = []
            
            if total_cpu > 80:
                analysis.append("系统CPU负载过高")
            elif total_cpu > 50:
                analysis.append("系统CPU负载适中")
            else:
                analysis.append("系统CPU负载较低")
            
            if total_memory > 80:
                analysis.append("系统内存负载过高")
            elif total_memory > 50:
                analysis.append("系统内存负载适中")
            else:
                analysis.append("系统内存负载较低")
            
            return f"系统负载分析: {'; '.join(analysis)}"
            
        except Exception as e:
            return f"系统负载分析失败: {e}"
    
    async def _analyze_system_load_with_reasoning(self, processes: List[Dict[str, Any]], system_info: Dict[str, Any]) -> str:
        """带推理的系统负载分析"""
        if not processes:
            return "系统负载分析: 无进程数据"
        
        # 计算负载指标
        cpu_processes = [p.get('cpu_percent', 0) for p in processes]
        memory_processes = [p.get('memory_percent', 0) for p in processes]
        
        total_cpu_usage = sum(cpu_processes)
        total_memory_usage = sum(memory_processes)
        avg_cpu_per_process = total_cpu_usage / len(processes) if processes else 0
        
        reasoning = []
        
        # CPU负载分析
        if total_cpu_usage > 200:  # 多核情况下
            reasoning.append("CPU负载严重过高，系统可能卡顿")
        elif total_cpu_usage > 100:
            reasoning.append("CPU负载较高，需要关注")
        else:
            reasoning.append("CPU负载正常")
        
        # 内存负载分析
        if total_memory_usage > 80:
            reasoning.append("内存负载过高，可能影响性能")
        elif total_memory_usage > 60:
            reasoning.append("内存负载适中")
        else:
            reasoning.append("内存负载较低")
        
        # 进程分布分析
        active_processes = len([p for p in processes if p.get('cpu_percent', 0) > 1])
        reasoning.append(f"活跃进程数: {active_processes}")
        
        analysis = f"系统负载分析: {'; '.join(reasoning)}。总CPU使用{total_cpu_usage:.1f}%，总内存使用{total_memory_usage:.1f}%"
        
        evidence = [
            f"总CPU使用: {total_cpu_usage:.1f}%",
            f"总内存使用: {total_memory_usage:.1f}%",
            f"活跃进程: {active_processes}个",
            f"平均CPU/进程: {avg_cpu_per_process:.1f}%"
        ]
        
        self.add_reasoning_step(
            "负载分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    def _generate_system_diagnosis(self, uptime_analysis: str, process_analysis: str, load_analysis: str) -> str:
        """生成系统综合诊断"""
        issues = []
        
        if "过长" in uptime_analysis:
            issues.append("系统运行时间过长")
        
        if "过高" in process_analysis or "过高" in load_analysis:
            issues.append("系统负载过高")
        
        if "异常" in process_analysis:
            issues.append("进程状态异常")
        
        if issues:
            diagnosis = f"检测到系统问题: {', '.join(issues)}。建议进行系统优化和维护。"
        else:
            diagnosis = "系统运行状态良好，进程管理正常。"
        
        return diagnosis
    
    def _generate_system_recommendations(self, system_info: Dict, processes: List[Dict]) -> List[str]:
        """生成系统建议"""
        recommendations = []
        
        # 运行时间建议
        uptime = system_info.get('uptime', 0) / 86400  # 转换为天
        if uptime > 30:
            recommendations.append("系统运行时间过长，建议重启以清理缓存")
        
        # 进程建议
        high_cpu_processes = [p for p in processes if p.get('cpu_percent', 0) > 80]
        if high_cpu_processes:
            recommendations.append("关闭高CPU使用率的不必要进程")
        
        high_memory_processes = [p for p in processes if p.get('memory_percent', 0) > 20]
        if high_memory_processes:
            recommendations.append("检查高内存使用率的进程是否正常")
        
        # 总进程数建议
        if len(processes) > 200:
            recommendations.append("进程数量较多，建议清理不必要的后台程序")
        
        if not recommendations:
            recommendations.append("系统状态良好，继续保持")
        
        return recommendations
    
    def _calculate_system_score(self, system_data) -> float:
        """计算系统健康评分"""
        scores = []
        
        # 运行时间评分
        uptime_days = system_data.system_info.uptime / 86400
        if uptime_days < 7:
            scores.append(1.0)
        elif uptime_days < 30:
            scores.append(0.8)
        else:
            scores.append(0.6)
        
        # 进程评分
        processes = system_data.processes
        if processes:
            high_cpu_count = len([p for p in processes if p.cpu_percent > 80])
            high_memory_count = len([p for p in processes if p.memory_percent > 20])
            
            if high_cpu_count == 0 and high_memory_count == 0:
                scores.append(1.0)
            elif high_cpu_count <= 2 and high_memory_count <= 3:
                scores.append(0.7)
            else:
                scores.append(0.4)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_confidence_score(self) -> float:
        """计算置信度评分"""
        if not self._reasoning_steps:
            return 0.5
        
        confidences = [step.confidence for step in self._reasoning_steps]
        return sum(confidences) / len(confidences)