"""工具执行器."""

import asyncio
from typing import Any

from .base import Tool, ToolCall, ToolResult, ToolError
from .registry import ToolRegistry


class ToolExecutor:
    """工具执行器.
    
    负责执行工具调用并返回结果。
    
    示例:
        >>> executor = ToolExecutor(registry)
        >>> tool_call = ToolCall(id="1", name="calculator", arguments={"expression": "2+2"})
        >>> result = await executor.execute(tool_call)
        >>> print(result.content)  # "4"
    """
    
    def __init__(self, registry: ToolRegistry):
        """初始化执行器.
        
        Args:
            registry: 工具注册表
        """
        self.registry = registry
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用.
        
        Args:
            tool_call: 工具调用请求
        
        Returns:
            工具执行结果
        """
        tool = self.registry.get(tool_call.name)
        
        if tool is None:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"工具 '{tool_call.name}' 不存在",
                is_error=True
            )
        
        try:
            # 检查参数
            for param in tool.parameters:
                if param.required and param.name not in tool_call.arguments:
                    return ToolResult(
                        tool_call_id=tool_call.id,
                        content=f"缺少必需参数: {param.name}",
                        is_error=True
                    )
            
            # 调用函数
            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**tool_call.arguments)
            else:
                result = tool.function(**tool_call.arguments)
            
            return ToolResult(
                tool_call_id=tool_call.id,
                content=str(result)
            )
            
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"执行错误: {str(e)}",
                is_error=True
            )
    
    async def execute_batch(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """批量执行工具调用.
        
        Args:
            tool_calls: 工具调用请求列表
        
        Returns:
            工具执行结果列表
        """
        results = await asyncio.gather(
            *[self.execute(tc) for tc in tool_calls]
        )
        return list(results)