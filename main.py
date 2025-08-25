#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SysGraph 主应用程序入口

提供GUI和CLI两种启动方式。
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QDir
from loguru import logger

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from gui import SysGraphMainWindow
from core import DiagnosisManager, ConfigurationManager
from utils import setup_logging, check_system_requirements


def setup_application() -> QApplication:
    """设置Qt应用程序"""
    app = QApplication(sys.argv)
    app.setApplicationName("SysGraph")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("SysGraph Team")
    app.setOrganizationDomain("sysgraph.io")
    
    # 设置应用程序图标和样式
    app.setQuitOnLastWindowClosed(True)
    
    return app


def run_gui_mode() -> int:
    """运行GUI模式"""
    try:
        # 检查系统要求
        if not check_system_requirements():
            logger.error("系统要求检查失败")
            return 1
            
        app = setup_application()
        
        # 初始化配置管理器
        config_manager = ConfigurationManager()
        
        # 创建主窗口
        main_window = SysGraphMainWindow(config_manager)
        main_window.show()
        
        logger.info("SysGraph GUI已启动")
        return app.exec()
        
    except Exception as e:
        logger.error(f"启动GUI模式失败: {e}")
        return 1


async def run_cli_mode(args: argparse.Namespace) -> int:
    """运行CLI模式"""
    try:
        logger.info("SysGraph CLI模式启动")
        
        # 初始化诊断管理器
        diagnosis_manager = DiagnosisManager()
        
        if args.command == "diagnose":
            logger.info("开始系统诊断...")
            
            # 执行诊断
            async for result in diagnosis_manager.run_diagnosis():
                if result["type"] == "diagnosis_complete":
                    print(f"诊断完成: {result['summary']}")
                    if result["issues"]:
                        print("发现问题:")
                        for issue in result["issues"]:
                            print(f"  - {issue['description']} (严重程度: {issue['severity']})")
                    else:
                        print("未发现系统问题")
                elif result["type"] == "diagnosis_error":
                    logger.error(f"诊断错误: {result['error']}")
                    return 1
                    
        elif args.command == "check-update":
            logger.info("检查更新...")
            # TODO: 实现更新检查逻辑
            
        return 0
        
    except Exception as e:
        logger.error(f"CLI模式执行失败: {e}")
        return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="SysGraph - 智能系统诊断工具",
        epilog="使用示例: sysgraph --gui 或 sysgraph diagnose"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="SysGraph 0.1.0"
    )
    
    parser.add_argument(
        "--gui", 
        action="store_true", 
        help="启动GUI模式（默认）"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="设置日志级别"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 诊断命令
    diagnose_parser = subparsers.add_parser("diagnose", help="运行系统诊断")
    diagnose_parser.add_argument("--output", "-o", help="诊断结果输出文件")
    diagnose_parser.add_argument("--format", choices=["json", "text"], default="text", help="输出格式")
    
    # 更新检查命令
    update_parser = subparsers.add_parser("check-update", help="检查软件更新")
    update_parser.add_argument("--auto-update", action="store_true", help="自动更新")
    
    return parser


def main() -> int:
    """主函数"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(level=args.log_level, debug=args.debug)
    
    logger.info("SysGraph 启动中...")
    
    # 根据参数决定运行模式
    if args.command:
        # CLI模式
        return asyncio.run(run_cli_mode(args))
    else:
        # GUI模式（默认）
        return run_gui_mode()


if __name__ == "__main__":
    sys.exit(main())