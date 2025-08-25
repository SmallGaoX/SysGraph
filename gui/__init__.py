"""
SysGraph 主界面

使用PyQt6构建的用户友好的图形界面。
"""

import sys
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QProgressBar, QTextEdit, QGroupBox,
    QSystemTrayIcon, QMenu, QStatusBar, QSplitter, QFrame,
    QGridLayout, QScrollArea, QApplication, QMessageBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap, QAction
from loguru import logger

try:
    import qdarkstyle
    HAS_DARK_STYLE = True
except ImportError:
    HAS_DARK_STYLE = False

from core import ConfigurationManager
from collectors import DataCollectionManager  
from models import SystemSnapshot


class StartupDataCollectionWorker(QThread):
    """启动时数据收集工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度状态消息
    data_collected = pyqtSignal(object)  # 数据收集完成
    error_occurred = pyqtSignal(str)  # 错误消息
    
    def __init__(self, data_collection_manager: DataCollectionManager):
        super().__init__()
        self.data_collection_manager = data_collection_manager
    
    def run(self):
        """运行数据收集"""
        try:
            self.progress_updated.emit("正在初始化系统...")
            self.msleep(500)
            
            self.progress_updated.emit("正在收集系统信息...")
            self.msleep(800)
            
            self.progress_updated.emit("正在检测硬件设备...")
            self.msleep(600)
            
            self.progress_updated.emit("正在检查网络连接...")
            self.msleep(400)
            
            # 运行在事件循环中的异步操作
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            self.progress_updated.emit("正在收集数据...")
            
            try:
                # 收集系统快照
                snapshot = loop.run_until_complete(
                    self.data_collection_manager.collect_single_snapshot()
                )
                
                self.progress_updated.emit("数据收集完成")
                self.msleep(300)
                
                self.data_collected.emit(snapshot)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"启动数据收集失败: {e}")
            self.error_occurred.emit(str(e))


class SystemRefreshWorker(QThread):
    """系统信息刷新工作线程"""
    
    # 信号定义
    data_updated = pyqtSignal(object)  # 数据更新完成
    
    def __init__(self, data_collection_manager: DataCollectionManager):
        super().__init__()
        self.data_collection_manager = data_collection_manager
    
    def run(self):
        """运行数据刷新"""
        try:
            # 在线程中创建新的事件循环
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 收集系统快照
                snapshot = loop.run_until_complete(
                    self.data_collection_manager.collect_single_snapshot()
                )
                
                self.data_updated.emit(snapshot)
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"系统信息刷新失败: {e}")


class DiagnosisWorker(QThread):
    """诊断工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(str, int, str)  # 状态, 进度, 消息
    diagnosis_completed = pyqtSignal(dict)  # 诊断结果
    error_occurred = pyqtSignal(str)  # 错误消息
    
    def __init__(self, config_manager: ConfigurationManager):
        super().__init__()
        self.config_manager = config_manager
        self.is_running = False
    
    def run(self):
        """运行诊断"""
        try:
            self.is_running = True
            self.progress_updated.emit("starting", 0, "正在启动诊断...")
            
            # 模拟诊断过程
            steps = [
                ("collecting", 20, "收集系统信息..."),
                ("analyzing", 40, "分析硬件状态..."),
                ("checking", 60, "检查网络连通性..."),
                ("processing", 80, "AI智能体分析中..."),
                ("completing", 100, "生成诊断报告...")
            ]
            
            for status, progress, message in steps:
                if not self.is_running:
                    break
                self.progress_updated.emit(status, progress, message)
                self.msleep(1000)  # 模拟工作时间
            
            if self.is_running:
                # 模拟诊断结果
                result = {
                    "overall_health_score": 0.85,
                    "issues_count": 2,
                    "recommendations_count": 3,
                    "diagnosis_time": 5.2,
                    "timestamp": datetime.now().isoformat()
                }
                self.diagnosis_completed.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.is_running = False
    
    def stop(self):
        """停止诊断"""
        self.is_running = False


class SystemInfoWidget(QWidget):
    """系统信息显示组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 系统概览
        overview_group = QGroupBox("系统概览")
        overview_layout = QGridLayout()
        
        self.hostname_label = QLabel("主机名: --")
        self.platform_label = QLabel("平台: --")
        self.uptime_label = QLabel("运行时间: --")
        self.cpu_label = QLabel("CPU使用率: --%")
        self.memory_label = QLabel("内存使用率: --%")
        self.disk_label = QLabel("磁盘使用率: --%")
        
        overview_layout.addWidget(self.hostname_label, 0, 0)
        overview_layout.addWidget(self.platform_label, 0, 1)
        overview_layout.addWidget(self.uptime_label, 1, 0)
        overview_layout.addWidget(self.cpu_label, 1, 1)
        overview_layout.addWidget(self.memory_label, 2, 0)
        overview_layout.addWidget(self.disk_label, 2, 1)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # 状态指示器
        status_group = QGroupBox("系统状态")
        status_layout = QHBoxLayout()
        
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.disk_progress = QProgressBar()
        self.disk_progress.setMaximum(100)
        
        status_layout.addWidget(QLabel("CPU:"))
        status_layout.addWidget(self.cpu_progress)
        status_layout.addWidget(QLabel("内存:"))
        status_layout.addWidget(self.memory_progress)
        status_layout.addWidget(QLabel("磁盘:"))
        status_layout.addWidget(self.disk_progress)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def update_system_info(self, snapshot: Optional[SystemSnapshot] = None):
        """更新系统信息显示"""
        if snapshot:
            # 更新系统信息
            system_info = snapshot.system.system_info
            self.hostname_label.setText(f"主机名: {system_info.hostname}")
            self.platform_label.setText(f"平台: {system_info.system}")
            
            uptime_hours = system_info.uptime / 3600
            if uptime_hours < 24:
                uptime_str = f"{uptime_hours:.1f} 小时"
            else:
                uptime_days = uptime_hours / 24
                uptime_str = f"{uptime_days:.1f} 天"
            self.uptime_label.setText(f"运行时间: {uptime_str}")
            
            # 更新硬件信息
            hardware = snapshot.hardware
            cpu_usage = int(hardware.cpu.usage_percent)
            memory_usage = int(hardware.memory.usage_percent)
            
            # 计算平均磁盘使用率
            if hardware.disks:
                disk_usage = int(sum(disk.usage_percent for disk in hardware.disks) / len(hardware.disks))
            else:
                disk_usage = 0
            
            self.cpu_label.setText(f"CPU使用率: {cpu_usage}%")
            self.memory_label.setText(f"内存使用率: {memory_usage}%")
            self.disk_label.setText(f"磁盘使用率: {disk_usage}%")
            
            # 更新进度条
            self.cpu_progress.setValue(cpu_usage)
            self.memory_progress.setValue(memory_usage)
            self.disk_progress.setValue(disk_usage)
            
            # 设置进度条颜色
            self._set_progress_color(self.cpu_progress, cpu_usage)
            self._set_progress_color(self.memory_progress, memory_usage)
            self._set_progress_color(self.disk_progress, disk_usage)
    
    def _set_progress_color(self, progress_bar: QProgressBar, value: int):
        """设置进度条颜色"""
        if value > 90:
            color = "#e74c3c"  # 红色
        elif value > 70:
            color = "#f39c12"  # 橙色
        else:
            color = "#27ae60"  # 绿色
        
        progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)


class DiagnosisWidget(QWidget):
    """诊断结果显示组件"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        
        # 诊断控制
        control_group = QGroupBox("诊断控制")
        control_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始诊断")
        self.start_button.setMinimumHeight(40)
        self.stop_button = QPushButton("停止诊断")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 诊断进度
        progress_group = QGroupBox("诊断进度")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # 诊断结果
        result_group = QGroupBox("诊断结果")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(200)
        
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        self.setLayout(layout)
    
    def update_progress(self, status: str, progress: int, message: str):
        """更新诊断进度"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        
        # 根据状态设置进度条颜色
        if status == "error":
            color = "#e74c3c"
        elif status == "completing":
            color = "#27ae60"
        else:
            color = "#3498db"
        
        self.progress_bar.setStyleSheet(f"""
            QProgressBar::chunk {{
                background-color: {color};
            }}
        """)
    
    def show_diagnosis_result(self, result: Dict[str, Any]):
        """显示诊断结果"""
        health_score = result.get('overall_health_score', 0) * 100
        issues_count = result.get('issues_count', 0)
        recommendations_count = result.get('recommendations_count', 0)
        diagnosis_time = result.get('diagnosis_time', 0)
        
        result_html = f"""
        <h3>🏥 系统诊断报告</h3>
        <hr>
        <p><strong>📊 系统健康评分:</strong> <span style="color: {'#27ae60' if health_score > 80 else '#f39c12' if health_score > 60 else '#e74c3c'}; font-size: 18px;">{health_score:.1f}%</span></p>
        <p><strong>⚠️  发现问题:</strong> {issues_count} 个</p>
        <p><strong>💡 优化建议:</strong> {recommendations_count} 条</p>
        <p><strong>⏱️  诊断耗时:</strong> {diagnosis_time:.1f} 秒</p>
        <hr>
        
        <h4>🔍 主要发现:</h4>
        <ul>
        """
        
        if issues_count > 0:
            result_html += "<li>🔴 检测到CPU使用率偏高，建议关闭不必要的程序</li>"
            result_html += "<li>🟡 内存使用率较高，可考虑增加内存容量</li>"
        else:
            result_html += "<li>✅ 系统运行状态良好，未发现异常</li>"
        
        result_html += """
        </ul>
        
        <h4>📋 优化建议:</h4>
        <ul>
            <li>🧹 定期清理临时文件和缓存</li>
            <li>🔄 保持系统和软件更新</li>
            <li>📊 监控系统性能指标</li>
        </ul>
        """
        
        self.result_text.setHtml(result_html)


class SysGraphMainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self, config_manager: ConfigurationManager):
        super().__init__()
        self.config_manager = config_manager
        self.diagnosis_worker: Optional[DiagnosisWorker] = None
        self.system_timer = QTimer()
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        # 启动状态标志
        self.is_startup_loading = True
        self.startup_data_ready = False
        self.data_collection_manager: Optional[DataCollectionManager] = None
        
        # 初始化加载界面
        self.init_loading_ui()
        
        # 开始启动时数据收集
        self.start_startup_data_collection()
    
    def init_loading_ui(self):
        """初始化加载界面"""
        self.setWindowTitle("SysGraph - 智能系统诊断工具")
        self.setMinimumSize(400, 300)
        self.setMaximumSize(400, 300)  # 限制加载界面大小
        
        # 创建加载中央组件
        self.loading_widget = QWidget()
        self.setCentralWidget(self.loading_widget)
        
        # 加载布局
        loading_layout = QVBoxLayout()
        loading_layout.setSpacing(20)
        loading_layout.setContentsMargins(50, 50, 50, 50)
        
        # 标题
        title_label = QLabel("SysGraph")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        loading_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("智能系统诊断工具")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        loading_layout.addWidget(subtitle_label)
        
        loading_layout.addStretch()
        
        # 加载进度条
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 0)  # 不定长进度条
        self.loading_progress.setTextVisible(False)
        loading_layout.addWidget(self.loading_progress)
        
        # 加载状态文本
        self.loading_status = QLabel("正在初始化...")
        self.loading_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self.loading_status)
        
        loading_layout.addStretch()
        
        self.loading_widget.setLayout(loading_layout)
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen().geometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def start_startup_data_collection(self):
        """开始启动时数据收集"""
        from collectors import DataCollectionManager
        
        try:
            # 获取收集器配置
            collector_config = self.config_manager.get_section('collectors')
            if not collector_config:
                # 使用默认配置
                from core.config_models import CollectorConfiguration
                collector_config = CollectorConfiguration()
            
            # 创建数据收集管理器
            self.data_collection_manager = DataCollectionManager(collector_config)
            
            # 创建并启动数据收集线程
            self.startup_worker = StartupDataCollectionWorker(self.data_collection_manager)
            self.startup_worker.progress_updated.connect(self.update_loading_status)
            self.startup_worker.data_collected.connect(self.on_startup_data_ready)
            self.startup_worker.error_occurred.connect(self.on_startup_error)
            self.startup_worker.start()
            
        except Exception as e:
            logger.error(f"启动数据收集初始化失败: {e}")
            self.on_startup_error(str(e))
    
    def update_loading_status(self, status: str):
        """更新加载状态"""
        self.loading_status.setText(status)
        logger.info(f"加载状态: {status}")
    
    def on_startup_data_ready(self, snapshot):
        """启动数据准备完成"""
        self.startup_data_ready = True
        logger.info("启动数据收集完成")
        
        # 稍微延迟后切换到主界面
        QTimer.singleShot(500, self.switch_to_main_ui)
    
    def on_startup_error(self, error_message: str):
        """启动数据收集错误"""
        logger.error(f"启动数据收集失败: {error_message}")
        self.loading_status.setText(f"初始化失败: {error_message}")
        
        # 显示错误对话框
        QMessageBox.warning(self, "初始化错误", 
                           f"系统初始化时发生错误:\n{error_message}\n\n将使用默认数据继续运行")
        
        # 即使出错也切换到主界面
        QTimer.singleShot(1000, self.switch_to_main_ui)
    
    def switch_to_main_ui(self):
        """切换到主界面"""
        self.is_startup_loading = False
        
        # 重新初始化主界面
        self.setMaximumSize(16777215, 16777215)  # 取消尺寸限制
        self.init_ui()
        self.setup_tray_icon()
        self.setup_timers()
        
        # 立即刷新系统信息显示初始数据
        if self.startup_data_ready:
            self.refresh_system_info()
        
        logger.info("已切换到主界面")
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("SysGraph - 智能系统诊断工具")
        self.setMinimumSize(1000, 700)
        
        # 设置应用图标
        self.setWindowIcon(QIcon())  # 实际使用时需要添加图标文件
        
        # 应用主题
        if HAS_DARK_STYLE:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        
        # 创建中央窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 创建标签页组件
        self.tab_widget = QTabWidget()
        
        # 概览标签页
        overview_widget = self.create_overview_tab()
        self.tab_widget.addTab(overview_widget, "📊 系统概览")
        
        # 诊断标签页
        diagnosis_widget = QWidget()
        diagnosis_layout = QHBoxLayout()
        
        # 创建分割器用于诊断界面
        diagnosis_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧面板 - 系统信息
        self.system_info_widget = SystemInfoWidget()
        diagnosis_splitter.addWidget(self.system_info_widget)
        
        # 右侧面板 - 诊断功能
        self.diagnosis_widget = DiagnosisWidget()
        diagnosis_splitter.addWidget(self.diagnosis_widget)
        
        # 设置分割器比例
        diagnosis_splitter.setSizes([300, 700])
        
        diagnosis_layout.addWidget(diagnosis_splitter)
        diagnosis_widget.setLayout(diagnosis_layout)
        self.tab_widget.addTab(diagnosis_widget, "🔍 系统诊断")
        
        # 配置标签页
        config_widget = self.create_config_tab()
        self.tab_widget.addTab(config_widget, "⚙️ 系统配置")
        
        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
        
        # 连接信号
        self.diagnosis_widget.start_button.clicked.connect(self.start_diagnosis)
        self.diagnosis_widget.stop_button.clicked.connect(self.stop_diagnosis)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 加载配置
        self.load_window_config()
    
    def create_overview_tab(self) -> QWidget:
        """创建系统概览标签页"""
        overview_widget = QWidget()
        layout = QVBoxLayout()
        
        # 系统概览标题
        title_label = QLabel("📊 系统概览")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 系统状态卡片
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.Box)
        status_layout = QGridLayout()
        
        # 系统信息卡片
        system_card = self.create_info_card("🖥️ 系统信息", [
            "主机名: 获取中...",
            "操作系统: 获取中...",
            "运行时间: 获取中..."
        ])
        status_layout.addWidget(system_card, 0, 0)
        
        # 硬件状态卡片
        hardware_card = self.create_info_card("⚙️ 硬件状态", [
            "CPU使用率: 获取中...",
            "内存使用率: 获取中...",
            "磁盘使用率: 获取中..."
        ])
        status_layout.addWidget(hardware_card, 0, 1)
        
        # 网络状态卡片
        network_card = self.create_info_card("🌐 网络状态", [
            "网络接口: 获取中...",
            "连接状态: 获取中...",
            "网络延迟: 获取中..."
        ])
        status_layout.addWidget(network_card, 1, 0)
        
        # 诊断历史卡片
        history_card = self.create_info_card("📋 诊断历史", [
            "上次诊断: 暂无",
            "健康评分: 暂无",
            "发现问题: 暂无"
        ])
        status_layout.addWidget(history_card, 1, 1)
        
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame)
        
        layout.addStretch()
        overview_widget.setLayout(layout)
        return overview_widget
    
    def create_info_card(self, title: str, info_list: list) -> QGroupBox:
        """创建信息卡片"""
        card = QGroupBox(title)
        layout = QVBoxLayout()
        
        for info in info_list:
            label = QLabel(info)
            layout.addWidget(label)
        
        card.setLayout(layout)
        return card
    
    def create_config_tab(self) -> QWidget:
        """创建配置标签页"""
        config_widget = QWidget()
        layout = QVBoxLayout()
        
        # 配置标题
        title_label = QLabel("⚙️ 系统配置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 创建配置内容的滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # GUI配置组
        gui_group = self.create_gui_config_group()
        scroll_layout.addWidget(gui_group)
        
        # 收集器配置组
        collector_group = self.create_collector_config_group()
        scroll_layout.addWidget(collector_group)
        
        # 更新配置组
        update_group = self.create_update_config_group()
        scroll_layout.addWidget(update_group)
        
        # 配置操作按钮
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 保存配置")
        save_button.clicked.connect(self.save_config)
        button_layout.addWidget(save_button)
        
        reset_button = QPushButton("🔄 重置为默认")
        reset_button.clicked.connect(self.reset_config)
        button_layout.addWidget(reset_button)
        
        export_button = QPushButton("📤 导出配置")
        export_button.clicked.connect(self.export_config)
        button_layout.addWidget(export_button)
        
        import_button = QPushButton("📥 导入配置")
        import_button.clicked.connect(self.import_config)
        button_layout.addWidget(import_button)
        
        button_layout.addStretch()
        scroll_layout.addLayout(button_layout)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        
        layout.addWidget(scroll_area)
        config_widget.setLayout(layout)
        return config_widget
    
    def create_gui_config_group(self) -> QGroupBox:
        """创建 GUI 配置组"""
        from PyQt6.QtWidgets import QCheckBox, QSpinBox, QComboBox
        
        group = QGroupBox("🎨 界面配置")
        layout = QGridLayout()
        
        # 获取当前配置
        gui_config = self.config_manager.get_section('gui')
        
        # 主题选择
        layout.addWidget(QLabel("主题:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        if gui_config:
            self.theme_combo.setCurrentText(gui_config.theme)
        layout.addWidget(self.theme_combo, 0, 1)
        
        # 语言选择
        layout.addWidget(QLabel("语言:"), 1, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["zh_CN", "en_US"])
        if gui_config:
            self.language_combo.setCurrentText(gui_config.language)
        layout.addWidget(self.language_combo, 1, 1)
        
        # 窗口大小
        layout.addWidget(QLabel("窗口宽度:"), 2, 0)
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        if gui_config:
            self.window_width_spin.setValue(gui_config.window_width)
        layout.addWidget(self.window_width_spin, 2, 1)
        
        layout.addWidget(QLabel("窗口高度:"), 3, 0)
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        if gui_config:
            self.window_height_spin.setValue(gui_config.window_height)
        layout.addWidget(self.window_height_spin, 3, 1)
        
        # 功能选项
        self.show_tray_check = QCheckBox("显示系统托盘")
        if gui_config:
            self.show_tray_check.setChecked(gui_config.show_system_tray)
        layout.addWidget(self.show_tray_check, 4, 0, 1, 2)
        
        self.minimize_tray_check = QCheckBox("最小化到托盘")
        if gui_config:
            self.minimize_tray_check.setChecked(gui_config.minimize_to_tray)
        layout.addWidget(self.minimize_tray_check, 5, 0, 1, 2)
        
        self.enable_notifications_check = QCheckBox("启用通知")
        if gui_config:
            self.enable_notifications_check.setChecked(gui_config.enable_notifications)
        layout.addWidget(self.enable_notifications_check, 6, 0, 1, 2)
        
        # 刷新间隔
        layout.addWidget(QLabel("刷新间隔(秒):"), 7, 0)
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        if gui_config:
            self.refresh_interval_spin.setValue(gui_config.refresh_interval)
        layout.addWidget(self.refresh_interval_spin, 7, 1)
        
        group.setLayout(layout)
        return group
    
    def create_collector_config_group(self) -> QGroupBox:
        """创建收集器配置组"""
        from PyQt6.QtWidgets import QSpinBox
        
        group = QGroupBox("📋 数据收集配置")
        layout = QGridLayout()
        
        # 获取当前配置
        collector_config = self.config_manager.get_section('collectors')
        
        # 最大进程数
        layout.addWidget(QLabel("最大进程数:"), 0, 0)
        self.max_processes_spin = QSpinBox()
        self.max_processes_spin.setRange(10, 1000)
        if collector_config:
            self.max_processes_spin.setValue(collector_config.max_processes)
        layout.addWidget(self.max_processes_spin, 0, 1)
        
        # 收集间隔
        layout.addWidget(QLabel("收集间隔(秒):"), 1, 0)
        self.collection_interval_spin = QSpinBox()
        self.collection_interval_spin.setRange(1, 3600)
        if collector_config:
            self.collection_interval_spin.setValue(collector_config.collection_interval)
        layout.addWidget(self.collection_interval_spin, 1, 1)
        
        # 网络超时
        layout.addWidget(QLabel("网络超时(秒):"), 2, 0)
        self.network_timeout_spin = QSpinBox()
        self.network_timeout_spin.setRange(1, 60)
        if collector_config:
            self.network_timeout_spin.setValue(collector_config.network_timeout)
        layout.addWidget(self.network_timeout_spin, 2, 1)
        
        group.setLayout(layout)
        return group
    
    def create_update_config_group(self) -> QGroupBox:
        """创建更新配置组"""
        from PyQt6.QtWidgets import QCheckBox, QSpinBox, QLineEdit
        
        group = QGroupBox("🔄 更新配置")
        layout = QGridLayout()
        
        # 获取当前配置
        update_config = self.config_manager.get_section('update')
        
        # 自动检查更新
        self.auto_check_updates_check = QCheckBox("自动检查更新")
        if update_config:
            self.auto_check_updates_check.setChecked(update_config.auto_check_updates)
        layout.addWidget(self.auto_check_updates_check, 0, 0, 1, 2)
        
        # 仓库 URL
        layout.addWidget(QLabel("仓库 URL:"), 1, 0)
        self.repository_url_edit = QLineEdit()
        if update_config:
            self.repository_url_edit.setText(update_config.repository_url)
        layout.addWidget(self.repository_url_edit, 1, 1)
        
        # 检查间隔
        layout.addWidget(QLabel("检查间隔(秒):"), 2, 0)
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(60, 86400)
        if update_config:
            self.check_interval_spin.setValue(update_config.check_interval)
        layout.addWidget(self.check_interval_spin, 2, 1)
        
        # 更新前备份
        self.backup_before_update_check = QCheckBox("更新前备份")
        if update_config:
            self.backup_before_update_check.setChecked(update_config.backup_before_update)
        layout.addWidget(self.backup_before_update_check, 3, 0, 1, 2)
        
        group.setLayout(layout)
        return group
    
    def save_config(self):
        """保存配置"""
        try:
            # 保存 GUI 配置
            self.config_manager.set_value('gui.theme', self.theme_combo.currentText())
            self.config_manager.set_value('gui.language', self.language_combo.currentText())
            self.config_manager.set_value('gui.window_width', self.window_width_spin.value())
            self.config_manager.set_value('gui.window_height', self.window_height_spin.value())
            self.config_manager.set_value('gui.show_system_tray', self.show_tray_check.isChecked())
            self.config_manager.set_value('gui.minimize_to_tray', self.minimize_tray_check.isChecked())
            self.config_manager.set_value('gui.enable_notifications', self.enable_notifications_check.isChecked())
            self.config_manager.set_value('gui.refresh_interval', self.refresh_interval_spin.value())
            
            # 保存收集器配置
            self.config_manager.set_value('collectors.max_processes', self.max_processes_spin.value())
            self.config_manager.set_value('collectors.collection_interval', self.collection_interval_spin.value())
            self.config_manager.set_value('collectors.network_timeout', self.network_timeout_spin.value())
            
            # 保存更新配置
            self.config_manager.set_value('update.auto_check_updates', self.auto_check_updates_check.isChecked())
            self.config_manager.set_value('update.repository_url', self.repository_url_edit.text())
            self.config_manager.set_value('update.check_interval', self.check_interval_spin.value())
            self.config_manager.set_value('update.backup_before_update', self.backup_before_update_check.isChecked())
            
            # 保存到文件
            if self.config_manager.save_config():
                QMessageBox.information(self, "成功", "配置已保存！")
                logger.info("配置已保存")
            else:
                QMessageBox.warning(self, "错误", "配置保存失败！")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置时发生错误：{e}")
            logger.error(f"保存配置失败: {e}")
    
    def reset_config(self):
        """重置配置为默认值"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确认要将所有配置重置为默认值吗？\n\n此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.config_manager.reset_to_default():
                    QMessageBox.information(self, "成功", "配置已重置为默认值！\n\n请重启应用程序以生效。")
                    logger.info("配置已重置为默认值")
                else:
                    QMessageBox.warning(self, "错误", "配置重置失败！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重置配置时发生错误：{e}")
                logger.error(f"重置配置失败: {e}")
    
    def export_config(self):
        """导出配置"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", 
            "config.yaml",
            "YAML 文件 (*.yaml *.yml);;所有文件 (*)"
        )
        
        if file_path:
            try:
                if self.config_manager.export_config(file_path, 'yaml'):
                    QMessageBox.information(self, "成功", f"配置已导出到：\n{file_path}")
                    logger.info(f"配置已导出: {file_path}")
                else:
                    QMessageBox.warning(self, "错误", "配置导出失败！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出配置时发生错误：{e}")
                logger.error(f"导出配置失败: {e}")
    
    def import_config(self):
        """导入配置"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", 
            "",
            "YAML 文件 (*.yaml *.yml);;所有文件 (*)"
        )
        
        if file_path:
            reply = QMessageBox.question(
                self, "确认导入", 
                f"确认要导入配置文件：\n{file_path}\n\n这将覆盖当前配置！",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if self.config_manager.import_config(file_path):
                        QMessageBox.information(self, "成功", "配置已导入！\n\n请重启应用程序以生效。")
                        logger.info(f"配置已导入: {file_path}")
                    else:
                        QMessageBox.warning(self, "错误", "配置导入失败！")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"导入配置时发生错误：{e}")
                    logger.error(f"导入配置失败: {e}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        start_action = QAction('开始诊断(&S)', self)
        start_action.setShortcut('Ctrl+S')
        start_action.triggered.connect(self.start_diagnosis)
        file_menu.addAction(start_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&Q)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        refresh_action = QAction('刷新系统信息(&R)', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_system_info)
        view_menu.addAction(refresh_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 添加时间标签
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # 更新时间
        self.update_time()
    
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon())  # 实际使用时需要添加图标文件
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        start_diagnosis_action = QAction("开始诊断", self)
        start_diagnosis_action.triggered.connect(self.start_diagnosis)
        tray_menu.addAction(start_diagnosis_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        config = self.config_manager.get_section('gui')
        if config and config.show_system_tray:
            self.tray_icon.show()
    
    def setup_timers(self):
        """设置定时器"""
        # 系统信息更新定时器
        self.system_timer.timeout.connect(self.refresh_system_info)
        
        config = self.config_manager.get_section('gui')
        if config:
            interval = config.refresh_interval * 1000  # 转换为毫秒
            self.system_timer.start(interval)
        
        # 时间更新定时器
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)  # 每秒更新
    
    def load_window_config(self):
        """加载窗口配置"""
        config = self.config_manager.get_section('gui')
        if config:
            self.resize(config.window_width, config.window_height)
    
    def start_diagnosis(self):
        """开始诊断"""
        if self.diagnosis_worker and self.diagnosis_worker.isRunning():
            return
        
        logger.info("开始系统诊断")
        self.status_label.setText("正在进行系统诊断...")
        
        # 更新按钮状态
        self.diagnosis_widget.start_button.setEnabled(False)
        self.diagnosis_widget.stop_button.setEnabled(True)
        
        # 创建并启动工作线程
        self.diagnosis_worker = DiagnosisWorker(self.config_manager)
        self.diagnosis_worker.progress_updated.connect(self.diagnosis_widget.update_progress)
        self.diagnosis_worker.diagnosis_completed.connect(self.on_diagnosis_completed)
        self.diagnosis_worker.error_occurred.connect(self.on_diagnosis_error)
        self.diagnosis_worker.start()
    
    def stop_diagnosis(self):
        """停止诊断"""
        if self.diagnosis_worker and self.diagnosis_worker.isRunning():
            self.diagnosis_worker.stop()
            self.diagnosis_worker.wait()
        
        logger.info("诊断已停止")
        self.status_label.setText("诊断已停止")
        
        # 更新按钮状态
        self.diagnosis_widget.start_button.setEnabled(True)
        self.diagnosis_widget.stop_button.setEnabled(False)
    
    def on_diagnosis_completed(self, result: Dict[str, Any]):
        """诊断完成回调"""
        logger.info("系统诊断完成")
        self.status_label.setText("诊断完成")
        
        # 显示结果
        self.diagnosis_widget.show_diagnosis_result(result)
        
        # 更新按钮状态
        self.diagnosis_widget.start_button.setEnabled(True)
        self.diagnosis_widget.stop_button.setEnabled(False)
        
        # 显示通知
        config = self.config_manager.get_section('gui')
        if config and config.enable_notifications and self.tray_icon:
            health_score = result.get('overall_health_score', 0) * 100
            self.tray_icon.showMessage(
                "SysGraph 诊断完成",
                f"系统健康评分: {health_score:.1f}%",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
    
    def on_diagnosis_error(self, error_message: str):
        """诊断错误回调"""
        logger.error(f"诊断过程出错: {error_message}")
        self.status_label.setText(f"诊断错误: {error_message}")
        
        # 更新按钮状态
        self.diagnosis_widget.start_button.setEnabled(True)
        self.diagnosis_widget.stop_button.setEnabled(False)
        
        # 显示错误对话框
        QMessageBox.critical(self, "诊断错误", f"诊断过程中发生错误:\n{error_message}")
    
    def refresh_system_info(self):
        """刷新系统信息"""
        try:
            if self.data_collection_manager and self.startup_data_ready:
                # 使用后台线程收集数据，避免阻塞主线程
                self._start_background_refresh()
            else:
                # 初始化阶段或数据收集器不可用，使用默认数据
                self.system_info_widget.update_system_info(None)
                logger.debug("使用默认数据刷新系统信息")
                
        except Exception as e:
            logger.error(f"刷新系统信息失败: {e}")
            # 发生错误时使用默认数据
            self.system_info_widget.update_system_info(None)
    
    def _start_background_refresh(self):
        """在后台线程中刷新数据"""
        if hasattr(self, 'refresh_worker') and self.refresh_worker.isRunning():
            return  # 已经有刷新任务在运行
        
        self.refresh_worker = SystemRefreshWorker(self.data_collection_manager)
        self.refresh_worker.data_updated.connect(self._on_data_refreshed)
        self.refresh_worker.start()
    
    def _on_data_refreshed(self, snapshot):
        """数据刷新完成回调"""
        try:
            self.system_info_widget.update_system_info(snapshot)
            logger.debug("系统信息已刷新")
        except Exception as e:
            logger.error(f"更新系统信息显示失败: {e}")
    
    def update_time(self):
        """更新时间显示"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def tray_icon_activated(self, reason):
        """托盘图标激活回调"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.raise_()
                self.activateWindow()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于 SysGraph", 
                         """
                         <h3>SysGraph 智能系统诊断工具</h3>
                         <p>版本: 0.1.0</p>
                         <p>基于AI的跨平台系统监控和诊断解决方案</p>
                         <hr>
                         <p>特性:</p>
                         <ul>
                         <li>🤖 AI智能诊断</li>
                         <li>📊 实时系统监控</li>
                         <li>🔍 多智能体协同分析</li>
                         <li>💡 智能优化建议</li>
                         </ul>
                         <p><small>© 2024 SysGraph Team</small></p>
                         """)
    
    def quit_application(self):
        """退出应用程序"""
        if self.diagnosis_worker and self.diagnosis_worker.isRunning():
            self.stop_diagnosis()
        
        if self.tray_icon:
            self.tray_icon.hide()
        
        QApplication.instance().quit()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        config = self.config_manager.get_section('gui')
        if config and config.minimize_to_tray and self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.quit_application()
            event.accept()