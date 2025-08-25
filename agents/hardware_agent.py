"""
硬件分析智能体

专门负责硬件相关的分析和诊断。
"""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent, AgentResult, SystemDiagnosticTool
from ..models import SystemSnapshot


class HardwareAnalysisAgent(BaseAgent):
    """硬件分析智能体"""
    
    def __init__(self, llm=None):
        """初始化硬件分析智能体"""
        system_prompt = """
你是一个专业的硬件诊断专家，专门分析计算机硬件性能和状态。

你的主要职责：
1. 分析CPU使用率、温度和性能状态
2. 评估内存使用情况和容量是否充足
3. 检查磁盘空间和I/O性能
4. 识别硬件性能瓶颈和潜在问题
5. 提供具体的硬件优化建议

分析时要考虑：
- 使用率阈值和性能指标
- 硬件配置的合理性
- 潜在的升级需求
- 性能优化建议

请始终保持专业和准确，提供可执行的建议。
        """
        
        tools = [
            SystemDiagnosticTool.get_cpu_analysis_tool(),
            SystemDiagnosticTool.get_memory_analysis_tool(),
            SystemDiagnosticTool.get_disk_analysis_tool(),
        ]
        
        super().__init__(
            name="hardware_analyst",
            llm=llm,
            tools=tools,
            system_prompt=system_prompt
        )
    
    async def execute_task(self, task_input: Dict[str, Any]) -> AgentResult:
        """
        执行硬件分析任务
        
        Args:
            task_input: 包含系统快照的任务输入
            
        Returns:
            AgentResult: 分析结果
        """
        start_time = datetime.now()
        task_id = task_input.get('task_id', 'hardware_analysis')
        
        try:
            logger.info(f"硬件分析智能体开始执行任务: {task_id}")
            
            # 清除历史记录
            self.clear_history()
            
            # 获取系统快照
            snapshot = task_input.get('system_snapshot')
            if not snapshot:
                raise ValueError("缺少系统快照数据")
            
            # 分析硬件数据
            analysis_result = await self._analyze_hardware_data(snapshot)
            
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
            logger.error(f"硬件分析任务执行失败: {e}")
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
        执行带有推理过程的硬件分析
        
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
                "message": "开始硬件分析推理",
                "timestamp": datetime.now().isoformat()
            }
            
            # 第一步：理解问题
            self.add_reasoning_step(
                "问题理解",
                "需要分析系统硬件状态，包括CPU、内存和磁盘的使用情况",
                confidence=0.9,
                evidence=["收到完整的系统硬件数据"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "问题理解",
                "content": "分析硬件性能和状态",
                "confidence": 0.9
            }
            
            # 第二步：数据分析
            hardware_data = snapshot_data.get('hardware', {})
            
            # 分析CPU
            cpu_data = hardware_data.get('cpu', {})
            cpu_analysis = await self._analyze_cpu_with_reasoning(cpu_data)
            
            yield {
                "type": "reasoning_step", 
                "step": "CPU分析",
                "content": cpu_analysis,
                "confidence": 0.8
            }
            
            # 分析内存
            memory_data = hardware_data.get('memory', {})
            memory_analysis = await self._analyze_memory_with_reasoning(memory_data)
            
            yield {
                "type": "reasoning_step",
                "step": "内存分析", 
                "content": memory_analysis,
                "confidence": 0.8
            }
            
            # 分析磁盘
            disk_data = hardware_data.get('disks', [])
            disk_analysis = await self._analyze_disk_with_reasoning(disk_data)
            
            yield {
                "type": "reasoning_step",
                "step": "磁盘分析",
                "content": disk_analysis,
                "confidence": 0.8
            }
            
            # 第三步：综合诊断
            overall_diagnosis = self._generate_overall_diagnosis(cpu_analysis, memory_analysis, disk_analysis)
            
            self.add_reasoning_step(
                "综合诊断",
                overall_diagnosis,
                confidence=0.85,
                evidence=["CPU分析结果", "内存分析结果", "磁盘分析结果"]
            )
            
            yield {
                "type": "reasoning_step",
                "step": "综合诊断",
                "content": overall_diagnosis,
                "confidence": 0.85
            }
            
            # 最终结果
            final_result = {
                "cpu_analysis": cpu_analysis,
                "memory_analysis": memory_analysis,
                "disk_analysis": disk_analysis,
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
    
    async def _analyze_hardware_data(self, snapshot: SystemSnapshot) -> Dict[str, Any]:
        """分析硬件数据"""
        try:
            hardware_data = snapshot.hardware
            
            # 分析CPU
            cpu_analysis = await self._call_cpu_analysis_tool(hardware_data.cpu.dict())
            
            # 分析内存
            memory_analysis = await self._call_memory_analysis_tool(hardware_data.memory.dict())
            
            # 分析磁盘
            disk_analysis = await self._call_disk_analysis_tool([disk.dict() for disk in hardware_data.disks])
            
            # 生成综合建议
            recommendations = self._generate_hardware_recommendations(
                hardware_data.cpu.dict(),
                hardware_data.memory.dict(),
                [disk.dict() for disk in hardware_data.disks]
            )
            
            return {
                "cpu_analysis": cpu_analysis,
                "memory_analysis": memory_analysis,
                "disk_analysis": disk_analysis,
                "recommendations": recommendations,
                "hardware_score": self._calculate_hardware_score(hardware_data)
            }
            
        except Exception as e:
            logger.error(f"硬件数据分析失败: {e}")
            raise
    
    async def _call_cpu_analysis_tool(self, cpu_data: Dict[str, Any]) -> str:
        """调用CPU分析工具"""
        start_time = datetime.now()
        try:
            cpu_tool = SystemDiagnosticTool.get_cpu_analysis_tool()
            result = cpu_tool.func(json.dumps(cpu_data))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_cpu", cpu_data, result, execution_time, True)
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_cpu", cpu_data, None, execution_time, False, str(e))
            return f"CPU分析失败: {e}"
    
    async def _call_memory_analysis_tool(self, memory_data: Dict[str, Any]) -> str:
        """调用内存分析工具"""
        start_time = datetime.now()
        try:
            memory_tool = SystemDiagnosticTool.get_memory_analysis_tool()
            result = memory_tool.func(json.dumps(memory_data))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_memory", memory_data, result, execution_time, True)
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_memory", memory_data, None, execution_time, False, str(e))
            return f"内存分析失败: {e}"
    
    async def _call_disk_analysis_tool(self, disk_data: List[Dict[str, Any]]) -> str:
        """调用磁盘分析工具"""
        start_time = datetime.now()
        try:
            disk_tool = SystemDiagnosticTool.get_disk_analysis_tool()
            result = disk_tool.func(json.dumps(disk_data))
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_disk", {"disks": disk_data}, result, execution_time, True)
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.record_tool_call("analyze_disk", {"disks": disk_data}, None, execution_time, False, str(e))
            return f"磁盘分析失败: {e}"
    
    async def _analyze_cpu_with_reasoning(self, cpu_data: Dict[str, Any]) -> str:
        """带推理的CPU分析"""
        usage = cpu_data.get('usage_percent', 0)
        cores = cpu_data.get('core_count', 1)
        frequency = cpu_data.get('frequency', 0)
        
        reasoning = []
        if usage > 90:
            reasoning.append("CPU使用率超过90%，系统负载过高")
        elif usage > 70:
            reasoning.append("CPU使用率较高，需要监控")
        else:
            reasoning.append("CPU使用率正常")
        
        if cores < 4:
            reasoning.append("CPU核心数较少，可能影响多任务性能")
        
        if frequency > 0:
            if frequency < 2000:
                reasoning.append("CPU频率较低，性能可能受限")
        
        analysis = f"CPU分析: {'; '.join(reasoning)}。使用率{usage}%，{cores}核心，频率{frequency}MHz"
        
        self.add_reasoning_step(
            "CPU分析",
            analysis,
            confidence=0.8,
            evidence=[f"CPU使用率: {usage}%", f"核心数: {cores}", f"频率: {frequency}MHz"]
        )
        
        return analysis
    
    async def _analyze_memory_with_reasoning(self, memory_data: Dict[str, Any]) -> str:
        """带推理的内存分析"""
        usage_percent = memory_data.get('usage_percent', 0)
        total_gb = memory_data.get('total', 0) / (1024**3)
        
        reasoning = []
        if usage_percent > 90:
            reasoning.append("内存使用率过高，可能导致系统不稳定")
        elif usage_percent > 80:
            reasoning.append("内存使用率较高，建议清理内存")
        else:
            reasoning.append("内存使用率正常")
        
        if total_gb < 4:
            reasoning.append("物理内存较小，建议升级")
        elif total_gb < 8:
            reasoning.append("物理内存适中")
        else:
            reasoning.append("物理内存充足")
        
        analysis = f"内存分析: {'; '.join(reasoning)}。使用率{usage_percent}%，总容量{total_gb:.1f}GB"
        
        self.add_reasoning_step(
            "内存分析",
            analysis,
            confidence=0.8,
            evidence=[f"内存使用率: {usage_percent}%", f"总容量: {total_gb:.1f}GB"]
        )
        
        return analysis
    
    async def _analyze_disk_with_reasoning(self, disk_data: List[Dict[str, Any]]) -> str:
        """带推理的磁盘分析"""
        if not disk_data:
            return "磁盘分析: 未检测到磁盘数据"
        
        reasoning = []
        critical_disks = []
        
        for disk in disk_data:
            usage_percent = disk.get('usage_percent', 0)
            mountpoint = disk.get('mountpoint', 'unknown')
            
            if usage_percent > 95:
                critical_disks.append(mountpoint)
                reasoning.append(f"{mountpoint}磁盘空间严重不足({usage_percent}%)")
            elif usage_percent > 85:
                reasoning.append(f"{mountpoint}磁盘空间不足({usage_percent}%)")
        
        if not reasoning:
            reasoning.append("所有磁盘空间充足")
        
        analysis = f"磁盘分析: {'; '.join(reasoning)}"
        
        evidence = [f"{disk.get('mountpoint', 'unknown')}: {disk.get('usage_percent', 0)}%" for disk in disk_data]
        
        self.add_reasoning_step(
            "磁盘分析",
            analysis,
            confidence=0.8,
            evidence=evidence
        )
        
        return analysis
    
    def _generate_overall_diagnosis(self, cpu_analysis: str, memory_analysis: str, disk_analysis: str) -> str:
        """生成综合诊断"""
        issues = []
        
        if "过高" in cpu_analysis or "负载" in cpu_analysis:
            issues.append("CPU性能问题")
        
        if "过高" in memory_analysis or "不稳定" in memory_analysis:
            issues.append("内存不足问题")
        
        if "不足" in disk_analysis:
            issues.append("磁盘空间问题")
        
        if issues:
            diagnosis = f"检测到硬件问题: {', '.join(issues)}。建议优先解决这些问题以提升系统性能。"
        else:
            diagnosis = "硬件状态良好，系统运行正常。"
        
        return diagnosis
    
    def _generate_hardware_recommendations(self, cpu_data: Dict, memory_data: Dict, disk_data: List[Dict]) -> List[str]:
        """生成硬件建议"""
        recommendations = []
        
        # CPU建议
        if cpu_data.get('usage_percent', 0) > 80:
            recommendations.append("关闭不必要的后台程序以降低CPU使用率")
        
        # 内存建议
        if memory_data.get('usage_percent', 0) > 80:
            recommendations.append("增加物理内存或关闭内存占用高的程序")
        
        # 磁盘建议
        for disk in disk_data:
            if disk.get('usage_percent', 0) > 85:
                mountpoint = disk.get('mountpoint', 'unknown')
                recommendations.append(f"清理{mountpoint}磁盘空间或扩容")
        
        if not recommendations:
            recommendations.append("硬件配置良好，无需特别优化")
        
        return recommendations
    
    def _calculate_hardware_score(self, hardware_data) -> float:
        """计算硬件健康评分"""
        scores = []
        
        # CPU评分
        cpu_usage = hardware_data.cpu.usage_percent
        if cpu_usage < 50:
            scores.append(1.0)
        elif cpu_usage < 80:
            scores.append(0.7)
        else:
            scores.append(0.3)
        
        # 内存评分
        memory_usage = hardware_data.memory.usage_percent
        if memory_usage < 60:
            scores.append(1.0)
        elif memory_usage < 80:
            scores.append(0.7)
        else:
            scores.append(0.3)
        
        # 磁盘评分
        if hardware_data.disks:
            disk_scores = []
            for disk in hardware_data.disks:
                if disk.usage_percent < 70:
                    disk_scores.append(1.0)
                elif disk.usage_percent < 85:
                    disk_scores.append(0.7)
                else:
                    disk_scores.append(0.3)
            scores.append(sum(disk_scores) / len(disk_scores))
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _calculate_confidence_score(self) -> float:
        """计算置信度评分"""
        if not self._reasoning_steps:
            return 0.5
        
        confidences = [step.confidence for step in self._reasoning_steps]
        return sum(confidences) / len(confidences)