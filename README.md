# SysGraph - 智能系统诊断工具

🤖 基于AI的跨平台系统监控和诊断解决方案

## 🌟 项目特性

- **🧠 AI智能诊断**: 集成Qwen3-0.6B模型，提供智能的系统分析和诊断
- **🔄 多智能体协同**: 使用LangGraph架构，多个专业智能体协同工作
- **📊 实时监控**: 持续收集系统硬件、软件和网络状态信息
- **🎯 精准分析**: 硬件、系统、网络三大专业智能体分别负责不同领域
- **🛡️ 规则引擎**: 内置专家规则 + 远程Git仓库规则，双重保障
- **💻 跨平台支持**: 支持Windows、macOS、Linux
- **🎨 友好界面**: PyQt6构建的现代化GUI，支持深色主题
- **🔄 自动更新**: 支持Gitea的版本检查和自动更新

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户界面层                                │
│  ┌─────────────────┐    ┌─────────────────────────────────┐  │
│  │   PyQt6 GUI     │    │      命令行接口                  │  │
│  └─────────────────┘    └─────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     应用服务层                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   诊断管理器     │ │   智能体管理器   │ │   模型管理器     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     智能体层                                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   硬件分析      │ │   系统分析      │ │   网络分析      │ │
│  │   智能体        │ │   智能体        │ │   智能体        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     数据收集层                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   硬件信息      │ │   系统信息      │ │   网络信息      │ │
│  │   收集器        │ │   收集器        │ │   收集器        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     AI引擎层                                  │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Qwen3-0.6B     │ │   LangGraph     │ │   工具调用      │ │
│  │   模型          │ │   引擎          │ │   系统          │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- uv (推荐的包管理器)
- Git

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/sysgraph/sysgraph.git
cd sysgraph/SysGraph
```

2. **安装依赖**
```bash
uv sync
```

3. **运行应用**
```bash
# GUI模式 (默认)
uv run sysgraph

# 命令行模式
uv run sysgraph diagnose

# 查看帮助
uv run sysgraph --help
```

## 📦 项目结构

```
sysgraph/
├── sysgraph/                 # 主要源代码
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── core/                # 核心模块
│   │   ├── config_manager.py
│   │   └── config_models.py
│   ├── agents/              # 智能体模块
│   │   ├── base_agent.py
│   │   ├── hardware_agent.py
│   │   ├── system_agent.py
│   │   └── network_agent.py
│   ├── collectors/          # 数据收集器
│   │   ├── hardware_collector.py
│   │   ├── system_collector.py
│   │   └── network_collector.py
│   ├── models/              # 数据模型和AI模型管理
│   │   ├── __init__.py
│   │   └── model_manager.py
│   ├── rules/               # 规则引擎
│   │   └── __init__.py
│   ├── gui/                 # GUI界面
│   │   └── __init__.py
│   └── utils/               # 工具函数
│       └── __init__.py
├── tests/                   # 测试文件
├── docs/                    # 文档
├── assets/                  # 资源文件
├── config/                  # 配置文件
├── pyproject.toml          # 项目配置
└── README.md
```

## 🔧 配置说明

配置文件位于 `~/.sysgraph/config.yaml`，主要配置项：

```yaml
# AI模型配置
model:
  model_name: "Qwen/Qwen3-0.6B"
  device: "auto"
  temperature: 0.7
  auto_download: true

# 智能体配置
agents:
  consensus_threshold: 0.7
  enable_chain_of_thought: true
  enable_cross_validation: true

# 数据收集配置
collectors:
  collection_interval: 5
  enable_hardware_monitoring: true
  enable_system_monitoring: true
  enable_network_monitoring: true

# GUI配置
gui:
  theme: "dark"
  language: "zh_CN"
  window_width: 1200
  window_height: 800

# 更新配置
updates:
  auto_check_updates: true
  repository_url: "https://gitea.example.com/sysgraph/sysgraph"
```

## 🤖 AI诊断流程

### 严谨性设计

1. **多智能体共识机制**: 三个专业智能体独立分析，通过投票机制达成共识
2. **置信度量化**: 每个诊断结果都有明确的置信度评分
3. **思考链推理**: 支持思考链输出，展示AI的推理过程
4. **规则引擎兜底**: AI无法确定时自动切换到专家规则
5. **交叉验证**: 智能体结果相互验证，提高准确性

### 诊断维度

#### 🖥️ 硬件分析智能体
- CPU使用率、温度、核心数分析
- 内存使用情况和容量评估
- 磁盘空间和I/O性能检查
- 硬件性能瓶颈识别

#### 🔧 系统分析智能体
- 系统运行时间和稳定性
- 进程状态和资源占用
- 系统负载和性能指标
- 异常进程识别

#### 🌐 网络分析智能体
- 网络接口状态检查
- 连通性测试和延迟分析
- 网络流量和性能监控
- 网络配置和安全检查

## 🛠️ 开发指南

### 添加新的智能体

1. 继承 `BaseAgent` 类
2. 实现 `execute_task` 和 `execute_with_reasoning` 方法
3. 定义专业工具和系统提示词
4. 在智能体管理器中注册

### 添加新的规则

1. 在 `BuiltinRules` 类中添加规则定义
2. 或创建YAML/JSON格式的远程规则文件
3. 推送到Git仓库，系统将自动更新

### 自定义数据收集器

1. 继承相应的收集器基类
2. 实现数据收集逻辑
3. 返回标准化的数据模型

## 📊 使用示例

### GUI模式
启动后即可通过图形界面进行系统诊断：

1. 查看实时系统状态
2. 点击"开始诊断"按钮
3. 观察AI分析过程
4. 查看诊断结果和建议

### 命令行模式
```bash
# 运行完整诊断
uv run sysgraph diagnose

# 输出到文件
uv run sysgraph diagnose --output report.json --format json

# 检查更新
uv run sysgraph check-update --auto-update
```

## 🔄 更新机制

支持从Gitea仓库自动检查和下载更新：

1. 定期检查远程仓库的新版本
2. 下载更新包并验证完整性
3. 备份当前版本
4. 应用更新并重启应用

## 🧪 测试

```bash
# 运行所有测试
uv run pytest

# 运行特定模块测试
uv run pytest tests/test_agents.py

# 运行GUI测试
uv run pytest tests/test_gui.py --gui
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 📞 支持

- 📧 Email: team@sysgraph.io
- 🐛 Issues: [GitHub Issues](https://github.com/sysgraph/sysgraph/issues)
- 📖 文档: [在线文档](https://sysgraph.readthedocs.io/)

## 🙏 致谢

- [Qwen](https://github.com/QwenLM/Qwen) - 提供优秀的开源语言模型
- [LangChain](https://github.com/langchain-ai/langchain) - 强大的AI应用开发框架
- [PyQt6](https://riverbankcomputing.com/software/pyqt/) - 现代化的GUI框架
- [psutil](https://github.com/giampaolo/psutil) - 系统信息获取库