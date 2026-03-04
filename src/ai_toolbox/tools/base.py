"""工具系统基础定义."""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from abc import ABC, abstractmethod
import inspect


@dataclass(frozen=True)
class ToolParameter:
    """工具参数定义."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str = ""
    required: bool = True
    default: Any = None
    enum: list[Any] = field(default_factory=list)


@dataclass(frozen=True)
class Tool:
    """工具定义.
    
    示例:
        >>> def calculator(expression: str) -> str:
        ...     return str(eval(expression))
        ...
        >>> tool = Tool.from_function(
        ...     calculator,
        ...     description="计算数学表达式",
        ...     parameters=[
        ...         ToolParameter("expression", "string", "数学表达式，如 2+2")
        ...     ]
        ... )
    """
    name: str
    description: str
    parameters: list[ToolParameter]
    function: Callable[..., Any]
    
    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any],
        name: str | None = None,
        description: str = "",
        parameters: list[ToolParameter] | None = None
    ) -> "Tool":
        """从函数创建 Tool.
        
        Args:
            func: 函数对象
            name: 工具名称（默认使用函数名）
            description: 工具描述
            parameters: 参数列表（默认从函数签名推断）
        
        Returns:
            Tool 实例
        """
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"工具: {tool_name}"
        
        if parameters is None:
            # 从函数签名推断参数
            sig = inspect.signature(func)
            parameters = []
            for param_name, param in sig.parameters.items():
                param_type = "string"  # 默认类型
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation in (int, float):
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list:
                        param_type = "array"
                    elif param.annotation == dict:
                        param_type = "object"
                
                parameters.append(ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"参数: {param_name}",
                    required=param.default == inspect.Parameter.empty,
                    default=param.default if param.default != inspect.Parameter.empty else None
                ))
        
        return cls(
            name=tool_name,
            description=tool_description,
            parameters=parameters,
            function=func
        )
    
    def to_openai_format(self) -> dict[str, Any]:
        """转换为 OpenAI 工具格式."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: dict[str, Any] = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def to_anthropic_format(self) -> dict[str, Any]:
        """转换为 Anthropic 工具格式."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop: dict[str, Any] = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


@dataclass(frozen=True)
class ToolCall:
    """工具调用请求."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    """工具执行结果."""
    tool_call_id: str
    content: str
    is_error: bool = False


class ToolError(Exception):
    """工具执行错误."""
    pass