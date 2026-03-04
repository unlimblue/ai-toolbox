# AI-Toolbox 示例

本目录包含 ai-toolbox 的综合示例代码。

## 示例列表

### 01_basic_agent.py - 基础 Agent 组装
展示如何组装一个基础 Agent，包含 Provider、Tools 和 Agent 的完整流程。

```bash
python examples/01_basic_agent.py
```

**包含内容**:
- 创建 Provider
- 注册工具
- 创建 Agent
- 运行对话

### 02_multi_tools_agent.py - 多工具组合
展示如何组合多个工具，让 Agent 完成复杂任务。

```bash
python examples/02_multi_tools_agent.py
```

**包含内容**:
- 注册多个工具
- 复杂任务处理
- 工具自动选择

### 03_custom_tools.py - 自定义工具
展示如何创建自定义工具并集成到 Agent 中。

```bash
python examples/03_custom_tools.py
```

**包含内容**:
- 创建自定义 Tool
- 温度转换工具
- 货币转换工具
- 工具参数定义

### 04_vision_analysis.py - 视觉分析
展示如何使用视觉能力进行图像分析。

```bash
python examples/04_vision_analysis.py
```

**包含内容**:
- 图像来源（文件、URL、Base64）
- 单图分析
- 多图分析

## 运行要求

1. 安装依赖:
```bash
pip install -e ".[dev]"
```

2. 配置 API Keys:
```bash
cp .env.example .env
# 编辑 .env 填入你的 API Keys
```

3. 运行示例:
```bash
python examples/01_basic_agent.py
```

## 自定义示例

你可以基于这些示例创建自己的 Agent:

```python
from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import ToolRegistry

# 创建 Provider
client = create_provider("kimi", api_key="your_key")

# 创建工具注册表
registry = ToolRegistry()
# ... 注册你的工具

# 创建 Agent
agent = Agent(client, registry)

# 运行
response = await agent.run("你的问题")
```

## 更多示例

欢迎提交 PR 添加更多示例！