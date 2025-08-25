"""
配置管理器

负责配置的加载、保存、验证和动态更新。
"""

import json
import yaml
import toml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from loguru import logger

from .config_models import ApplicationConfiguration, DEFAULT_CONFIG


class ConfigurationManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self._config: ApplicationConfiguration = DEFAULT_CONFIG.copy()
        self._config_file: Optional[Path] = None
        self._watchers: Dict[str, list] = {}  # 配置变更监听器
        
        # 设置配置文件路径
        if config_file:
            self._config_file = Path(config_file)
        else:
            self._config_file = self._get_default_config_path()
        
        # 创建必要目录
        self._config.create_directories()
        
        # 加载配置
        self.load_config()
    
    def _get_default_config_path(self) -> Path:
        """获取默认配置文件路径"""
        config_dir = Path.home() / ".sysgraph"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.yaml"
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not self._config_file.exists():
                logger.info(f"配置文件不存在，创建默认配置: {self._config_file}")
                self.save_config()
                return True
            
            # 根据文件扩展名选择解析器
            file_extension = self._config_file.suffix.lower()
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                if file_extension == '.yaml' or file_extension == '.yml':
                    config_data = yaml.safe_load(f)
                elif file_extension == '.json':
                    config_data = json.load(f)
                elif file_extension == '.toml':
                    config_data = toml.load(f)
                else:
                    logger.error(f"不支持的配置文件格式: {file_extension}")
                    return False
            
            # 验证和更新配置
            self._config = ApplicationConfiguration(**config_data)
            logger.info(f"配置文件加载成功: {self._config_file}")
            
            # 触发配置加载事件
            self._notify_watchers('config_loaded', self._config)
            
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            self._config = DEFAULT_CONFIG.copy()
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 转换为字典
            config_dict = self._config.dict()
            
            # 根据文件扩展名选择格式
            file_extension = self._config_file.suffix.lower()
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                if file_extension == '.yaml' or file_extension == '.yml':
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                elif file_extension == '.json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                elif file_extension == '.toml':
                    toml.dump(config_dict, f)
                else:
                    logger.error(f"不支持的配置文件格式: {file_extension}")
                    return False
            
            logger.info(f"配置文件保存成功: {self._config_file}")
            
            # 触发配置保存事件
            self._notify_watchers('config_saved', self._config)
            
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_config(self) -> ApplicationConfiguration:
        """获取完整配置"""
        return self._config
    
    def get_section(self, section: str) -> Optional[Any]:
        """
        获取配置段
        
        Args:
            section: 配置段名称 (如 'model', 'agents', 'gui')
            
        Returns:
            配置段对象或None
        """
        return getattr(self._config, section, None)
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，用点分隔 (如 'model.temperature', 'gui.theme')
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                value = getattr(value, key)
            
            return value
            
        except (AttributeError, KeyError):
            logger.warning(f"配置键不存在: {key_path}")
            return default
    
    def set_value(self, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径
            value: 新值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key_path.split('.')
            if len(keys) < 2:
                logger.error(f"无效的配置键路径: {key_path}")
                return False
            
            # 获取目标对象
            target = self._config
            for key in keys[:-1]:
                target = getattr(target, key)
            
            # 设置值
            old_value = getattr(target, keys[-1])
            setattr(target, keys[-1], value)
            
            logger.info(f"配置更新: {key_path} = {value} (旧值: {old_value})")
            
            # 触发配置变更事件
            self._notify_watchers('config_changed', {
                'key': key_path,
                'old_value': old_value,
                'new_value': value
            })
            
            return True
            
        except (AttributeError, KeyError) as e:
            logger.error(f"设置配置值失败: {e}")
            return False
    
    def update_section(self, section: str, config_dict: Dict[str, Any]) -> bool:
        """
        更新配置段
        
        Args:
            section: 配置段名称
            config_dict: 配置字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            section_config = getattr(self._config, section)
            
            # 备份旧配置
            old_config = section_config.dict()
            
            # 更新配置
            for key, value in config_dict.items():
                if hasattr(section_config, key):
                    setattr(section_config, key, value)
                else:
                    logger.warning(f"未知配置项: {section}.{key}")
            
            logger.info(f"配置段更新: {section}")
            
            # 触发配置变更事件
            self._notify_watchers('section_changed', {
                'section': section,
                'old_config': old_config,
                'new_config': section_config.dict()
            })
            
            return True
            
        except (AttributeError, KeyError) as e:
            logger.error(f"更新配置段失败: {e}")
            return False
    
    def reset_to_default(self, section: Optional[str] = None) -> bool:
        """
        重置配置为默认值
        
        Args:
            section: 要重置的配置段，为None时重置全部
            
        Returns:
            bool: 重置是否成功
        """
        try:
            if section:
                # 重置指定段
                default_section = getattr(DEFAULT_CONFIG, section)
                setattr(self._config, section, default_section.copy())
                logger.info(f"配置段已重置为默认值: {section}")
            else:
                # 重置全部配置
                self._config = DEFAULT_CONFIG.copy()
                logger.info("所有配置已重置为默认值")
            
            # 触发重置事件
            self._notify_watchers('config_reset', section)
            
            return True
            
        except Exception as e:
            logger.error(f"重置配置失败: {e}")
            return False
    
    def validate_config(self) -> tuple[bool, list]:
        """
        验证配置
        
        Returns:
            tuple: (是否有效, 错误列表)
        """
        errors = []
        
        try:
            # 使用Pydantic验证
            ApplicationConfiguration(**self._config.dict())
            
            # 自定义验证逻辑
            if self._config.model.temperature < 0 or self._config.model.temperature > 2:
                errors.append("模型温度值超出有效范围 (0-2)")
            
            if self._config.agents.consensus_threshold < 0.5 or self._config.agents.consensus_threshold > 1.0:
                errors.append("共识阈值超出有效范围 (0.5-1.0)")
            
            if self._config.collectors.collection_interval < 1:
                errors.append("收集间隔不能小于1秒")
            
            # 检查目录权限
            for directory in [self._config.data_directory, self._config.cache_directory, self._config.log_directory]:
                path = Path(directory)
                if path.exists() and not path.is_dir():
                    errors.append(f"路径不是目录: {directory}")
                elif path.exists() and not os.access(path, os.W_OK):
                    errors.append(f"目录无写权限: {directory}")
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"配置验证异常: {e}")
            return False, errors
    
    def add_watcher(self, event_type: str, callback: callable) -> None:
        """
        添加配置变更监听器
        
        Args:
            event_type: 事件类型 ('config_loaded', 'config_saved', 'config_changed', etc.)
            callback: 回调函数
        """
        if event_type not in self._watchers:
            self._watchers[event_type] = []
        self._watchers[event_type].append(callback)
    
    def remove_watcher(self, event_type: str, callback: callable) -> None:
        """移除配置变更监听器"""
        if event_type in self._watchers and callback in self._watchers[event_type]:
            self._watchers[event_type].remove(callback)
    
    def _notify_watchers(self, event_type: str, data: Any = None) -> None:
        """通知监听器"""
        if event_type in self._watchers:
            for callback in self._watchers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"配置监听器回调失败: {e}")
    
    def export_config(self, export_path: Union[str, Path], format: str = 'yaml') -> bool:
        """
        导出配置到文件
        
        Args:
            export_path: 导出路径
            format: 导出格式 ('yaml', 'json', 'toml')
            
        Returns:
            bool: 导出是否成功
        """
        try:
            export_path = Path(export_path)
            config_dict = self._config.dict()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                if format == 'yaml':
                    yaml.dump(config_dict, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
                elif format == 'json':
                    json.dump(config_dict, f, indent=2, ensure_ascii=False)
                elif format == 'toml':
                    toml.dump(config_dict, f)
                else:
                    logger.error(f"不支持的导出格式: {format}")
                    return False
            
            logger.info(f"配置导出成功: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: Union[str, Path]) -> bool:
        """
        从文件导入配置
        
        Args:
            import_path: 导入路径
            
        Returns:
            bool: 导入是否成功
        """
        try:
            import_path = Path(import_path)
            if not import_path.exists():
                logger.error(f"导入文件不存在: {import_path}")
                return False
            
            # 备份当前配置
            backup_config = self._config.copy()
            
            # 临时更改配置文件路径进行加载
            original_config_file = self._config_file
            self._config_file = import_path
            
            if self.load_config():
                # 恢复原始配置文件路径
                self._config_file = original_config_file
                logger.info(f"配置导入成功: {import_path}")
                return True
            else:
                # 恢复备份配置
                self._config = backup_config
                self._config_file = original_config_file
                return False
                
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False