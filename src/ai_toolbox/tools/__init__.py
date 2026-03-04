"""Tools 模块.

提供工具系统的基础组件：
- Tool: 工具定义
- ToolRegistry: 工具注册表
- ToolExecutor: 工具执行器
- 内置工具集

示例:
    >>> from ai_toolbox.tools import ToolRegistry, calculator_tool
    >>> registry = ToolRegistry()
    >>> registry.register(calculator_tool)
    >>> print(registry.list_names())
    ['calculator']
"""

from .base import Tool, ToolCall, ToolResult, ToolParameter, ToolError
from .registry import ToolRegistry
from .executor import ToolExecutor
from .builtin import (
    calculator_tool,
    get_current_time_tool,
    random_number_tool,
    random_choice_tool,
    count_words_tool,
    format_json_tool,
    read_file_tool,
    list_directory_tool,
)

__all__ = [
    # 基础类
    "Tool",
    "ToolCall",
    "ToolResult",
    "ToolParameter",
    "ToolError",
    # 注册和执行
    "ToolRegistry",
    "ToolExecutor",
    # 内置工具
    "calculator_tool",
    "get_current_time_tool",
    "random_number_tool",
    "random_choice_tool",
    "count_words_tool",
    "format_json_tool",
    "read_file_tool",
    "list_directory_tool",
]