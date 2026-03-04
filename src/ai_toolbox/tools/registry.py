"""工具注册表."""

from typing import Any

from .base import Tool


class ToolRegistry:
    """工具注册表.
    
    用于注册和管理工具，支持动态添加和查询。
    
    示例:
        >>> registry = ToolRegistry()
        >>> registry.register(calculator_tool)
        >>> tool = registry.get("calculator")
        >>> tools = registry.list_tools()  # OpenAI 格式
    """
    
    def __init__(self) -> None:
        """初始化注册表."""
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> "ToolRegistry":
        """注册工具.
        
        Args:
            tool: 要注册的工具
        
        Returns:
            self，支持链式调用
            
        示例:
            >>> registry.register(tool1).register(tool2)
        """
        self._tools[tool.name] = tool
        return self
    
    def unregister(self, name: str) -> "ToolRegistry":
        """注销工具.
        
        Args:
            name: 工具名称
        
        Returns:
            self
        """
        if name in self._tools:
            del self._tools[name]
        return self
    
    def get(self, name: str) -> Tool | None:
        """获取工具.
        
        Args:
            name: 工具名称
        
        Returns:
            Tool 实例或 None
        """
        return self._tools.get(name)
    
    def has(self, name: str) -> bool:
        """检查工具是否存在.
        
        Args:
            name: 工具名称
        
        Returns:
            是否存在
        """
        return name in self._tools
    
    def list_tools(self) -> list[dict[str, Any]]:
        """列出所有工具（OpenAI 格式）.
        
        Returns:
            工具定义列表
        """
        return [tool.to_openai_format() for tool in self._tools.values()]
    
    def list_tools_anthropic(self) -> list[dict[str, Any]]:
        """列出所有工具（Anthropic 格式）.
        
        Returns:
            工具定义列表
        """
        return [tool.to_anthropic_format() for tool in self._tools.values()]
    
    def list_names(self) -> list[str]:
        """列出所有工具名称.
        
        Returns:
            工具名称列表
        """
        return list(self._tools.keys())
    
    def clear(self) -> "ToolRegistry":
        """清空注册表.
        
        Returns:
            self
        """
        self._tools.clear()
        return self
    
    def __len__(self) -> int:
        """返回工具数量."""
        return len(self._tools)
    
    def __contains__(self, name: str) -> bool:
        """检查工具是否存在."""
        return name in self._tools
    
    def __iter__(self):
        """迭代工具."""
        return iter(self._tools.values())