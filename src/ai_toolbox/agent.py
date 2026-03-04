"""Agent 实现 - 工具编排和对话管理."""

import json
import uuid
from typing import Any

from ai_toolbox.core import get_logger
from ai_toolbox.providers import ChatMessage
from ai_toolbox.providers.base import BaseProvider
from ai_toolbox.tools import Tool, ToolCall, ToolResult, ToolRegistry, ToolExecutor

logger = get_logger(__name__)


class Agent:
    """AI Agent，支持工具调用.
    
    Agent 将 Provider（AI 模型）与 Tools（工具）结合，
    让 AI 能够自主决定何时调用工具。
    
    示例:
        >>> from ai_toolbox import Agent, create_provider
        >>> from ai_toolbox.tools import ToolRegistry, calculator_tool
        >>> 
        >>> # 创建 Agent
        >>> provider = create_provider("openrouter", api_key)
        >>> registry = ToolRegistry()
        >>> registry.register(calculator_tool)
        >>> agent = Agent(provider, registry)
        >>> 
        >>> # 运行
        >>> response = await agent.run("计算 123 * 456")
        >>> print(response)
        '56088'
    """
    
    def __init__(
        self,
        provider: BaseProvider,
        tools: ToolRegistry | None = None,
        max_iterations: int = 5,
        system_prompt: str | None = None
    ):
        """初始化 Agent.
        
        Args:
            provider: AI 模型提供商
            tools: 工具注册表（可选）
            max_iterations: 最大工具调用轮数
            system_prompt: 系统提示词
        """
        self.provider = provider
        self.tools = tools or ToolRegistry()
        self.executor = ToolExecutor(self.tools)
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        logger.info(f"Agent initialized with {len(self.tools)} tools")
    
    def _default_system_prompt(self) -> str:
        """默认系统提示词."""
        tool_list = ", ".join(self.tools.list_names()) if len(self.tools) > 0 else "无"
        
        return f"""你是一个有用的 AI 助手。

你可以使用以下工具来帮助用户：
{tool_list}

当你需要使用工具时，请输出以下格式的 JSON：
{{
    "tool": "工具名称",
    "arguments": {{
        "参数名": "参数值"
    }}
}}

如果你不需要使用工具，直接回答用户的问题即可。"""
    
    async def run(self, user_input: str, context: list[ChatMessage] | None = None) -> str:
        """运行 Agent.
        
        Args:
            user_input: 用户输入
            context: 对话上下文（可选）
        
        Returns:
            AI 的最终回复
        """
        # 构建消息列表
        messages: list[ChatMessage] = []
        
        if context:
            messages.extend(context)
        
        # 添加系统提示
        messages.insert(0, ChatMessage(role="system", content=self.system_prompt))
        
        # 添加用户输入
        messages.append(ChatMessage(role="user", content=user_input))
        
        # 工具调用循环
        for iteration in range(self.max_iterations):
            logger.debug(f"Iteration {iteration + 1}/{self.max_iterations}")
            
            # 获取 AI 响应
            response = await self.provider.chat(messages)
            content = response.content
            
            # 检查是否是工具调用
            tool_call = self._parse_tool_call(content)
            
            if tool_call is None:
                # 不是工具调用，直接返回结果
                return content
            
            # 执行工具
            logger.info(f"Executing tool: {tool_call.name}")
            result = await self.executor.execute(tool_call)
            
            # 添加工具调用和结果到消息
            messages.append(ChatMessage(
                role="assistant",
                content=f"我将使用工具: {tool_call.name}"
            ))
            messages.append(ChatMessage(
                role="user",
                content=f"工具 '{tool_call.name}' 的返回结果:\n{result.content}"
            ))
        
        # 达到最大迭代次数
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return "抱歉，处理这个问题需要太多步骤。请简化您的问题。"
    
    def _parse_tool_call(self, content: str) -> ToolCall | None:
        """解析工具调用.
        
        尝试从 AI 响应中解析工具调用。
        支持 JSON 格式。
        
        Args:
            content: AI 响应内容
        
        Returns:
            ToolCall 或 None
        """
        # 尝试解析 JSON
        try:
            # 尝试提取 JSON 块
            json_match = None
            
            # 查找 ```json ... ``` 代码块
            import re
            code_block_match = re.search(r'```json\s*\n?(.*?)\n?```', content, re.DOTALL)
            if code_block_match:
                json_match = code_block_match.group(1)
            
            # 或者直接查找 {...}
            if json_match is None:
                json_match_match = re.search(r'\{[\s\S]*\}', content)
                if json_match_match:
                    json_match = json_match_match.group(0)
            
            if json_match is None:
                return None
            
            data = json.loads(json_match.strip())
            
            # 检查是否是工具调用格式
            if "tool" in data or "name" in data:
                tool_name = data.get("tool") or data.get("name")
                arguments = data.get("arguments") or data.get("args") or {}
                
                # 验证工具是否存在
                if not self.tools.has(tool_name):
                    logger.warning(f"Tool '{tool_name}' not found")
                    return None
                
                return ToolCall(
                    id=str(uuid.uuid4()),
                    name=tool_name,
                    arguments=arguments
                )
            
            return None
            
        except json.JSONDecodeError:
            return None
        except Exception as e:
            logger.error(f"Error parsing tool call: {e}")
            return None
    
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """简单的对话（不使用工具）.
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            **kwargs: 其他参数
        
        Returns:
            AI 回复
        """
        response = await self.provider.chat(
            messages,
            temperature=temperature,
            **kwargs
        )
        return response.content
    
    def add_tool(self, tool: Tool) -> "Agent":
        """添加工具.
        
        Args:
            tool: 要添加的工具
        
        Returns:
            self，支持链式调用
        """
        self.tools.register(tool)
        return self
    
    def remove_tool(self, name: str) -> "Agent":
        """移除工具.
        
        Args:
            name: 工具名称
        
        Returns:
            self
        """
        self.tools.unregister(name)
        return self