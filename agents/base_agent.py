"""
智能体基础类和工具定义

提供智能体的基础架构和工具调用能力。
"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field

try:
    from langchain.agents import create_react_agent
    from langchain.tools import Tool
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain_core.language_models.base import BaseLanguageModel
    from langchain_core.prompts import PromptTemplate
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    logger.warning("LangChain库未安装，智能体功能将受限")

from ..models import SystemSnapshot


class ToolCall(BaseModel):
    """工具调用记录"""
    tool_name: str = Field(description="工具名称")
    parameters: Dict[str, Any] = Field(description="调用参数")
    result: Any = Field(description="调用结果")
    execution_time: float = Field(description="执行时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="调用时间")
    success: bool = Field(description="是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class ReasoningStep(BaseModel):
    """推理步骤"""
    step_id: str = Field(description="步骤ID")
    step_type: str = Field(description="步骤类型")
    content: str = Field(description="步骤内容")
    confidence: float = Field(description="置信度")
    evidence: List[str] = Field(description="证据列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class AgentResult(BaseModel):
    """智能体执行结果"""
    agent_name: str = Field(description="智能体名称")
    task_id: str = Field(description="任务ID")
    success: bool = Field(description="是否成功")
    result: Dict[str, Any] = Field(description="执行结果")
    reasoning_chain: List[ReasoningStep] = Field(description="推理链")
    tool_calls: List[ToolCall] = Field(description="工具调用记录")
    confidence_score: float = Field(description="整体置信度")
    execution_time: float = Field(description="执行时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class SystemDiagnosticTool:
    """系统诊断工具集合"""
    
    @staticmethod
    def get_cpu_analysis_tool() -> Tool:
        """CPU分析工具"""
        def analyze_cpu(data: str) -> str:
            try:
                cpu_data = json.loads(data)
                usage = cpu_data.get('usage_percent', 0)
                cores = cpu_data.get('core_count', 1)
                
                analysis = []
                if usage > 90:
                    analysis.append("CPU使用率过高，可能存在性能问题")
                elif usage > 70:
                    analysis.append("CPU使用率较高，需要关注")
                else:
                    analysis.append("CPU使用率正常")
                
                if cores < 2:
                    analysis.append("CPU核心数较少，可能影响多任务性能")
                
                return f"CPU分析结果: {'; '.join(analysis)}"
                
            except Exception as e:
                return f"CPU分析失败: {e}"
        
        return Tool(
            name="analyze_cpu",
            description="分析CPU使用情况和性能状态",
            func=analyze_cpu
        )
    
    @staticmethod
    def get_memory_analysis_tool() -> Tool:
        """内存分析工具"""
        def analyze_memory(data: str) -> str:
            try:
                memory_data = json.loads(data)
                usage_percent = memory_data.get('usage_percent', 0)
                total_gb = memory_data.get('total', 0) / (1024**3)
                
                analysis = []
                if usage_percent > 90:
                    analysis.append("内存使用率严重过高，可能导致系统不稳定")
                elif usage_percent > 80:
                    analysis.append("内存使用率过高，建议关闭不必要的程序")
                elif usage_percent > 60:
                    analysis.append("内存使用率较高，需要监控")
                else:
                    analysis.append("内存使用率正常")
                
                if total_gb < 4:
                    analysis.append("物理内存较小，建议增加内存")
                elif total_gb < 8:
                    analysis.append("物理内存适中，可考虑升级")
                
                return f"内存分析结果: {'; '.join(analysis)}"
                
            except Exception as e:
                return f"内存分析失败: {e}"
        
        return Tool(
            name="analyze_memory",
            description="分析内存使用情况和容量状态",
            func=analyze_memory
        )
    
    @staticmethod
    def get_disk_analysis_tool() -> Tool:
        """磁盘分析工具"""
        def analyze_disk(data: str) -> str:
            try:
                disk_data = json.loads(data)
                if isinstance(disk_data, list):
                    disks = disk_data
                else:
                    disks = [disk_data]
                
                analysis = []
                for disk in disks:
                    usage_percent = disk.get('usage_percent', 0)
                    mountpoint = disk.get('mountpoint', 'unknown')
                    
                    if usage_percent > 95:
                        analysis.append(f"{mountpoint}: 磁盘空间严重不足")
                    elif usage_percent > 85:
                        analysis.append(f"{mountpoint}: 磁盘空间不足")
                    elif usage_percent > 70:
                        analysis.append(f"{mountpoint}: 磁盘使用率较高")
                    else:
                        analysis.append(f"{mountpoint}: 磁盘空间充足")
                
                return f"磁盘分析结果: {'; '.join(analysis)}"
                
            except Exception as e:
                return f"磁盘分析失败: {e}"
        
        return Tool(
            name="analyze_disk",
            description="分析磁盘使用情况和空间状态",
            func=analyze_disk
        )
    
    @staticmethod
    def get_network_analysis_tool() -> Tool:
        """网络分析工具"""
        def analyze_network(data: str) -> str:
            try:
                network_data = json.loads(data)
                connectivity = network_data.get('connectivity', [])
                interfaces = network_data.get('interfaces', [])
                
                analysis = []
                
                # 分析连通性
                reachable_hosts = [c for c in connectivity if c.get('is_reachable', False)]
                if len(reachable_hosts) == 0:
                    analysis.append("网络连通性异常，所有测试主机均不可达")
                elif len(reachable_hosts) < len(connectivity):
                    analysis.append("部分网络连通性异常")
                else:
                    analysis.append("网络连通性正常")
                
                # 分析延迟
                latencies = [c.get('latency', 0) for c in reachable_hosts if c.get('latency')]
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                    if avg_latency > 200:
                        analysis.append("网络延迟较高")
                    elif avg_latency > 100:
                        analysis.append("网络延迟适中")
                    else:
                        analysis.append("网络延迟良好")
                
                # 分析接口状态
                active_interfaces = [i for i in interfaces if i.get('is_up', False)]
                if len(active_interfaces) == 0:
                    analysis.append("没有活跃的网络接口")
                else:
                    analysis.append(f"有{len(active_interfaces)}个活跃网络接口")
                
                return f"网络分析结果: {'; '.join(analysis)}"
                
            except Exception as e:
                return f"网络分析失败: {e}"
        
        return Tool(
            name="analyze_network",
            description="分析网络连通性和接口状态",
            func=analyze_network
        )
    
    @staticmethod
    def get_process_analysis_tool() -> Tool:
        """进程分析工具"""
        def analyze_processes(data: str) -> str:
            try:
                process_data = json.loads(data)
                if isinstance(process_data, list):
                    processes = process_data
                else:
                    processes = [process_data]
                
                analysis = []
                
                # 找出高CPU使用率进程
                high_cpu_processes = [p for p in processes if p.get('cpu_percent', 0) > 80]
                if high_cpu_processes:
                    process_names = [p.get('name', 'unknown') for p in high_cpu_processes[:3]]
                    analysis.append(f"高CPU使用率进程: {', '.join(process_names)}")
                
                # 找出高内存使用率进程
                high_memory_processes = [p for p in processes if p.get('memory_percent', 0) > 10]
                if high_memory_processes:
                    process_names = [p.get('name', 'unknown') for p in high_memory_processes[:3]]
                    analysis.append(f"高内存使用率进程: {', '.join(process_names)}")
                
                # 统计进程状态
                running_count = len([p for p in processes if p.get('status') == 'running'])
                analysis.append(f"运行中进程: {running_count}个")
                
                if not analysis:
                    analysis.append("进程状态正常")
                
                return f"进程分析结果: {'; '.join(analysis)}"
                
            except Exception as e:
                return f"进程分析失败: {e}"
        
        return Tool(
            name="analyze_processes",
            description="分析进程状态和资源使用情况",
            func=analyze_processes
        )


class BaseAgent(ABC):
    """智能体基础类"""
    
    def __init__(self, name: str, llm: Optional[BaseLanguageModel] = None, 
                 tools: Optional[List[Tool]] = None, system_prompt: str = ""):
        """
        初始化智能体
        
        Args:
            name: 智能体名称
            llm: 语言模型
            tools: 可用工具列表
            system_prompt: 系统提示词
        """
        self.name = name
        self.llm = llm
        self.tools = tools or []
        self.system_prompt = system_prompt
        
        self._agent = None
        self._tool_calls = []
        self._reasoning_steps = []
        
        if HAS_LANGCHAIN and llm and tools:
            self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        """初始化LangChain智能体"""
        try:
            if not HAS_LANGCHAIN:
                return
                
            # 创建prompt模板
            prompt = PromptTemplate.from_template("""
{system_prompt}

你是一个专业的系统诊断智能体，具有以下能力：
- 分析系统硬件和软件状态
- 识别潜在的性能问题
- 提供具体的解决建议
- 使用可用的工具进行深入分析

请按照以下格式进行推理：

思考: [你对当前问题的分析和思考]
行动: [选择使用的工具]
行动输入: [工具的输入参数]
观察: [工具的执行结果]
... (重复思考/行动/观察过程)
最终答案: [你的最终结论和建议]

可用工具:
{tools}

工具名称: {tool_names}

人类: {input}

{agent_scratchpad}
            """)
            
            self._agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt.partial(system_prompt=self.system_prompt)
            )
            
        except Exception as e:
            logger.error(f"初始化智能体失败 {self.name}: {e}")
    
    def add_tool(self, tool: Tool) -> None:
        """添加工具"""
        self.tools.append(tool)
        if self._agent and HAS_LANGCHAIN:
            self._initialize_agent()  # 重新初始化
    
    def record_tool_call(self, tool_name: str, parameters: Dict[str, Any], 
                        result: Any, execution_time: float, success: bool = True,
                        error_message: Optional[str] = None) -> None:
        """记录工具调用"""
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            execution_time=execution_time,
            success=success,
            error_message=error_message
        )
        self._tool_calls.append(tool_call)
    
    def add_reasoning_step(self, step_type: str, content: str, 
                          confidence: float = 0.5, evidence: List[str] = None) -> None:
        """添加推理步骤"""
        step = ReasoningStep(
            step_id=f"{self.name}_{len(self._reasoning_steps) + 1}",
            step_type=step_type,
            content=content,
            confidence=confidence,
            evidence=evidence or []
        )
        self._reasoning_steps.append(step)
    
    @abstractmethod
    async def execute_task(self, task_input: Dict[str, Any]) -> AgentResult:
        """
        执行任务
        
        Args:
            task_input: 任务输入
            
        Returns:
            AgentResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def execute_with_reasoning(self, input_data: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行带有推理过程的任务
        
        Args:
            input_data: 输入数据
            
        Yields:
            Dict[str, Any]: 推理过程和结果
        """
        pass
    
    def get_capabilities(self) -> List[str]:
        """获取智能体能力列表"""
        return [tool.name for tool in self.tools]
    
    def clear_history(self) -> None:
        """清除执行历史"""
        self._tool_calls.clear()
        self._reasoning_steps.clear()