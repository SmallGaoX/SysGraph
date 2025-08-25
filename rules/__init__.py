"""
规则引擎

提供内置规则和远程规则的管理、加载和执行功能。
"""

import json
import yaml
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field

from ..models import SystemSnapshot, DiagnosisIssue
from ..core.config_models import RuleEngineConfiguration


class Rule(BaseModel):
    """规则定义"""
    rule_id: str = Field(description="规则ID")
    name: str = Field(description="规则名称")
    category: str = Field(description="规则类别")
    description: str = Field(description="规则描述")
    severity: str = Field(description="严重程度")
    conditions: List[Dict[str, Any]] = Field(description="条件列表")
    actions: List[Dict[str, Any]] = Field(description="动作列表")
    enabled: bool = Field(default=True, description="是否启用")
    confidence: float = Field(default=0.8, description="规则置信度")
    version: str = Field(default="1.0.0", description="规则版本")
    author: str = Field(default="system", description="规则作者")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class RuleExecutionResult(BaseModel):
    """规则执行结果"""
    rule_id: str = Field(description="规则ID")
    matched: bool = Field(description="是否匹配")
    confidence: float = Field(description="执行置信度")
    evidence: List[str] = Field(description="匹配证据")
    actions_taken: List[str] = Field(description="执行的动作")
    issues_found: List[DiagnosisIssue] = Field(description="发现的问题")
    execution_time: float = Field(description="执行时间")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间")


class BuiltinRules:
    """内置规则库"""
    
    @staticmethod
    def get_hardware_rules() -> List[Rule]:
        """获取硬件相关规则"""
        return [
            Rule(
                rule_id="hw_cpu_high_usage",
                name="CPU使用率过高",
                category="hardware",
                description="检测CPU使用率超过90%的情况",
                severity="high",
                conditions=[
                    {"field": "hardware.cpu.usage_percent", "operator": ">", "value": 90}
                ],
                actions=[
                    {"type": "create_issue", "severity": "high", "message": "CPU使用率过高，可能影响系统性能"}
                ]
            ),
            Rule(
                rule_id="hw_memory_high_usage",
                name="内存使用率过高",
                category="hardware",
                description="检测内存使用率超过90%的情况",
                severity="high",
                conditions=[
                    {"field": "hardware.memory.usage_percent", "operator": ">", "value": 90}
                ],
                actions=[
                    {"type": "create_issue", "severity": "high", "message": "内存使用率过高，系统可能变慢"}
                ]
            ),
            Rule(
                rule_id="hw_disk_full",
                name="磁盘空间不足",
                category="hardware",
                description="检测磁盘使用率超过95%的情况",
                severity="critical",
                conditions=[
                    {"field": "hardware.disks[*].usage_percent", "operator": ">", "value": 95}
                ],
                actions=[
                    {"type": "create_issue", "severity": "critical", "message": "磁盘空间严重不足，需要立即清理"}
                ]
            ),
            Rule(
                rule_id="hw_cpu_temperature_high",
                name="CPU温度过高",
                category="hardware", 
                description="检测CPU温度超过80度的情况",
                severity="high",
                conditions=[
                    {"field": "hardware.cpu.temperature", "operator": ">", "value": 80}
                ],
                actions=[
                    {"type": "create_issue", "severity": "high", "message": "CPU温度过高，需要检查散热系统"}
                ]
            )
        ]
    
    @staticmethod
    def get_system_rules() -> List[Rule]:
        """获取系统相关规则"""
        return [
            Rule(
                rule_id="sys_uptime_too_long",
                name="系统运行时间过长",
                category="system",
                description="检测系统运行时间超过30天的情况",
                severity="medium",
                conditions=[
                    {"field": "system.system_info.uptime", "operator": ">", "value": 2592000}  # 30天秒数
                ],
                actions=[
                    {"type": "create_issue", "severity": "medium", "message": "系统运行时间过长，建议重启以清理内存"}
                ]
            ),
            Rule(
                rule_id="sys_too_many_processes",
                name="进程数量过多",
                category="system",
                description="检测活跃进程数量超过200的情况",
                severity="medium",
                conditions=[
                    {"field": "system.processes", "operator": "count", "value": 200}
                ],
                actions=[
                    {"type": "create_issue", "severity": "medium", "message": "系统进程数量过多，建议清理不必要的程序"}
                ]
            ),
            Rule(
                rule_id="sys_high_cpu_process",
                name="高CPU使用率进程",
                category="system",
                description="检测单个进程CPU使用率超过80%的情况",
                severity="medium",
                conditions=[
                    {"field": "system.processes[*].cpu_percent", "operator": ">", "value": 80}
                ],
                actions=[
                    {"type": "create_issue", "severity": "medium", "message": "检测到高CPU使用率进程"}
                ]
            )
        ]
    
    @staticmethod
    def get_network_rules() -> List[Rule]:
        """获取网络相关规则"""
        return [
            Rule(
                rule_id="net_no_connectivity",
                name="网络连通性异常",
                category="network",
                description="检测所有连通性测试失败的情况",
                severity="critical",
                conditions=[
                    {"field": "network.connectivity", "operator": "all_false", "field_check": "is_reachable"}
                ],
                actions=[
                    {"type": "create_issue", "severity": "critical", "message": "网络连通性异常，所有测试主机均不可达"}
                ]
            ),
            Rule(
                rule_id="net_high_latency",
                name="网络延迟过高",
                category="network", 
                description="检测平均网络延迟超过200ms的情况",
                severity="medium",
                conditions=[
                    {"field": "network.connectivity[*].latency", "operator": "avg>", "value": 200}
                ],
                actions=[
                    {"type": "create_issue", "severity": "medium", "message": "网络延迟过高，可能影响网络性能"}
                ]
            ),
            Rule(
                rule_id="net_no_active_interface",
                name="无活跃网络接口",
                category="network",
                description="检测没有活跃网络接口的情况", 
                severity="critical",
                conditions=[
                    {"field": "network.interfaces", "operator": "none_true", "field_check": "is_up"}
                ],
                actions=[
                    {"type": "create_issue", "severity": "critical", "message": "没有活跃的网络接口，网络功能不可用"}
                ]
            )
        ]
    
    @staticmethod
    def get_all_builtin_rules() -> List[Rule]:
        """获取所有内置规则"""
        rules = []
        rules.extend(BuiltinRules.get_hardware_rules())
        rules.extend(BuiltinRules.get_system_rules())
        rules.extend(BuiltinRules.get_network_rules())
        return rules


class RuleEngine:
    """规则引擎"""
    
    def __init__(self, config: RuleEngineConfiguration):
        """
        初始化规则引擎
        
        Args:
            config: 规则引擎配置
        """
        self.config = config
        self.builtin_rules: List[Rule] = []
        self.remote_rules: List[Rule] = []
        self.rule_cache_dir = Path.home() / ".sysgraph" / "rules"
        self.rule_cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._last_remote_update: Optional[datetime] = None
        
        # 加载内置规则
        if config.enable_builtin_rules:
            self._load_builtin_rules()
        
        # 加载远程规则
        if config.enable_remote_rules:
            asyncio.create_task(self._load_remote_rules())
    
    def _load_builtin_rules(self) -> None:
        """加载内置规则"""
        try:
            self.builtin_rules = BuiltinRules.get_all_builtin_rules()
            logger.info(f"加载了 {len(self.builtin_rules)} 个内置规则")
        except Exception as e:
            logger.error(f"加载内置规则失败: {e}")
    
    async def _load_remote_rules(self) -> None:
        """加载远程规则"""
        try:
            # 检查是否需要更新
            if self._should_update_remote_rules():
                await self._fetch_remote_rules()
            
            # 从缓存加载规则
            await self._load_cached_remote_rules()
            
        except Exception as e:
            logger.error(f"加载远程规则失败: {e}")
    
    def _should_update_remote_rules(self) -> bool:
        """检查是否应该更新远程规则"""
        if self._last_remote_update is None:
            return True
        
        time_since_update = datetime.now() - self._last_remote_update
        return time_since_update.total_seconds() > self.config.rules_update_interval
    
    async def _fetch_remote_rules(self) -> None:
        """从远程仓库获取规则"""
        try:
            logger.info(f"从远程仓库获取规则: {self.config.remote_rules_url}")
            
            # 使用git克隆或拉取规则仓库
            repo_dir = self.rule_cache_dir / "remote_repo"
            
            if repo_dir.exists():
                # 更新现有仓库
                cmd = ["git", "-C", str(repo_dir), "pull"]
            else:
                # 克隆新仓库
                cmd = ["git", "clone", self.config.remote_rules_url, str(repo_dir)]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info("远程规则获取成功")
                self._last_remote_update = datetime.now()
            else:
                logger.error(f"远程规则获取失败: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"获取远程规则异常: {e}")
    
    async def _load_cached_remote_rules(self) -> None:
        """从缓存加载远程规则"""
        try:
            repo_dir = self.rule_cache_dir / "remote_repo"
            if not repo_dir.exists():
                return
            
            # 查找规则文件
            rule_files = []
            for pattern in ["*.json", "*.yaml", "*.yml"]:
                rule_files.extend(repo_dir.rglob(pattern))
            
            remote_rules = []
            for rule_file in rule_files:
                try:
                    with open(rule_file, 'r', encoding='utf-8') as f:
                        if rule_file.suffix.lower() == '.json':
                            data = json.load(f)
                        else:
                            data = yaml.safe_load(f)
                    
                    # 解析规则数据
                    if isinstance(data, list):
                        for rule_data in data:
                            rule = Rule(**rule_data)
                            remote_rules.append(rule)
                    elif isinstance(data, dict) and 'rules' in data:
                        for rule_data in data['rules']:
                            rule = Rule(**rule_data)
                            remote_rules.append(rule)
                    
                except Exception as e:
                    logger.warning(f"解析规则文件失败 {rule_file}: {e}")
            
            self.remote_rules = remote_rules
            logger.info(f"加载了 {len(remote_rules)} 个远程规则")
            
        except Exception as e:
            logger.error(f"加载缓存远程规则失败: {e}")
    
    def get_all_rules(self) -> List[Rule]:
        """获取所有规则"""
        all_rules = []
        
        if self.config.enable_builtin_rules:
            all_rules.extend(self.builtin_rules)
        
        if self.config.enable_remote_rules:
            all_rules.extend(self.remote_rules)
        
        # 过滤启用的规则
        return [rule for rule in all_rules if rule.enabled]
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """根据类别获取规则"""
        return [rule for rule in self.get_all_rules() if rule.category == category]
    
    async def execute_rules(self, snapshot: SystemSnapshot) -> List[RuleExecutionResult]:
        """
        执行规则检查
        
        Args:
            snapshot: 系统快照
            
        Returns:
            List[RuleExecutionResult]: 规则执行结果列表
        """
        try:
            logger.info("开始执行规则检查")
            
            rules = self.get_all_rules()
            execution_results = []
            
            for rule in rules:
                start_time = datetime.now()
                try:
                    result = await self._execute_single_rule(rule, snapshot)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    result.execution_time = execution_time
                    execution_results.append(result)
                    
                except Exception as e:
                    logger.error(f"规则执行失败 {rule.rule_id}: {e}")
                    execution_results.append(RuleExecutionResult(
                        rule_id=rule.rule_id,
                        matched=False,
                        confidence=0.0,
                        evidence=[],
                        actions_taken=[],
                        issues_found=[],
                        execution_time=(datetime.now() - start_time).total_seconds()
                    ))
            
            logger.info(f"规则检查完成，执行了 {len(execution_results)} 个规则")
            return execution_results
            
        except Exception as e:
            logger.error(f"规则执行异常: {e}")
            return []
    
    async def _execute_single_rule(self, rule: Rule, snapshot: SystemSnapshot) -> RuleExecutionResult:
        """执行单个规则"""
        try:
            # 检查条件
            matched, evidence = self._check_conditions(rule.conditions, snapshot)
            
            # 如果条件匹配，执行动作
            actions_taken = []
            issues_found = []
            
            if matched:
                for action in rule.actions:
                    action_result = await self._execute_action(action, rule, snapshot, evidence)
                    actions_taken.append(action_result.get('description', ''))
                    
                    if action_result.get('issue'):
                        issues_found.append(action_result['issue'])
            
            # 计算置信度
            confidence = rule.confidence if matched else 0.0
            if matched and rule.confidence > self.config.rule_confidence_threshold:
                confidence = min(1.0, confidence * 1.1)  # 提高可信规则的置信度
            
            return RuleExecutionResult(
                rule_id=rule.rule_id,
                matched=matched,
                confidence=confidence,
                evidence=evidence,
                actions_taken=actions_taken,
                issues_found=issues_found,
                execution_time=0.0  # 将在调用方设置
            )
            
        except Exception as e:
            logger.error(f"执行规则失败 {rule.rule_id}: {e}")
            raise
    
    def _check_conditions(self, conditions: List[Dict[str, Any]], snapshot: SystemSnapshot) -> tuple[bool, List[str]]:
        """检查条件是否满足"""
        evidence = []
        all_matched = True
        
        snapshot_dict = snapshot.dict()
        
        for condition in conditions:
            field = condition.get('field', '')
            operator = condition.get('operator', '==')
            value = condition.get('value')
            field_check = condition.get('field_check')
            
            try:
                field_value = self._get_field_value(snapshot_dict, field)
                matched = self._evaluate_condition(field_value, operator, value, field_check)
                
                if matched:
                    evidence.append(f"{field} {operator} {value}: 匹配")
                else:
                    all_matched = False
                    evidence.append(f"{field} {operator} {value}: 不匹配 (实际值: {field_value})")
                    
            except Exception as e:
                all_matched = False
                evidence.append(f"{field}: 条件检查失败 - {e}")
        
        return all_matched, evidence
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """从数据中获取字段值"""
        try:
            # 处理数组索引和通配符
            if '[*]' in field_path:
                # 处理数组通配符
                base_path, array_field = field_path.split('[*]', 1)
                base_value = self._get_nested_value(data, base_path)
                
                if isinstance(base_value, list):
                    if array_field.startswith('.'):
                        array_field = array_field[1:]  # 移除开头的点
                    
                    if array_field:
                        return [self._get_nested_value(item, array_field) for item in base_value if isinstance(item, dict)]
                    else:
                        return base_value
                else:
                    return []
            else:
                return self._get_nested_value(data, field_path)
                
        except Exception as e:
            logger.warning(f"获取字段值失败 {field_path}: {e}")
            return None
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """获取嵌套字段值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _evaluate_condition(self, field_value: Any, operator: str, target_value: Any, field_check: Optional[str] = None) -> bool:
        """评估条件"""
        try:
            if operator == '>':
                return float(field_value) > float(target_value)
            elif operator == '<':
                return float(field_value) < float(target_value)
            elif operator == '>=':
                return float(field_value) >= float(target_value)
            elif operator == '<=':
                return float(field_value) <= float(target_value)
            elif operator == '==':
                return field_value == target_value
            elif operator == '!=':
                return field_value != target_value
            elif operator == 'contains':
                return target_value in str(field_value)
            elif operator == 'count':
                if isinstance(field_value, list):
                    return len(field_value) > target_value
                else:
                    return False
            elif operator == 'all_false' and field_check:
                if isinstance(field_value, list):
                    return all(not item.get(field_check, True) for item in field_value)
                else:
                    return False
            elif operator == 'none_true' and field_check:
                if isinstance(field_value, list):
                    return not any(item.get(field_check, False) for item in field_value)
                else:
                    return False
            elif operator == 'avg>' and isinstance(field_value, list):
                numeric_values = [v for v in field_value if isinstance(v, (int, float)) and v is not None]
                if numeric_values:
                    avg_value = sum(numeric_values) / len(numeric_values)
                    return avg_value > target_value
                else:
                    return False
            else:
                logger.warning(f"未知操作符: {operator}")
                return False
                
        except Exception as e:
            logger.warning(f"条件评估失败: {e}")
            return False
    
    async def _execute_action(self, action: Dict[str, Any], rule: Rule, snapshot: SystemSnapshot, evidence: List[str]) -> Dict[str, Any]:
        """执行动作"""
        action_type = action.get('type', '')
        
        if action_type == 'create_issue':
            issue = DiagnosisIssue(
                issue_id=f"{rule.rule_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                category=rule.category,
                severity=action.get('severity', rule.severity),
                title=rule.name,
                description=action.get('message', rule.description),
                recommendation=action.get('recommendation', f"请检查{rule.category}相关配置"),
                confidence=rule.confidence,
                evidence=evidence
            )
            
            return {
                'description': f"创建问题: {rule.name}",
                'issue': issue
            }
        
        elif action_type == 'log':
            level = action.get('level', 'info')
            message = action.get('message', f"规则 {rule.name} 被触发")
            
            if level == 'error':
                logger.error(message)
            elif level == 'warning':
                logger.warning(message) 
            else:
                logger.info(message)
            
            return {
                'description': f"记录日志: {message}"
            }
        
        else:
            return {
                'description': f"未知动作类型: {action_type}"
            }
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则统计信息"""
        all_rules = self.get_all_rules()
        
        by_category = {}
        by_severity = {}
        
        for rule in all_rules:
            # 按类别统计
            if rule.category not in by_category:
                by_category[rule.category] = 0
            by_category[rule.category] += 1
            
            # 按严重程度统计
            if rule.severity not in by_severity:
                by_severity[rule.severity] = 0
            by_severity[rule.severity] += 1
        
        return {
            "total_rules": len(all_rules),
            "builtin_rules": len(self.builtin_rules),
            "remote_rules": len(self.remote_rules),
            "by_category": by_category,
            "by_severity": by_severity,
            "last_remote_update": self._last_remote_update.isoformat() if self._last_remote_update else None,
            "config": self.config.dict()
        }