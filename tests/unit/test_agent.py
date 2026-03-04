"""Agent 单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_toolbox.agent import Agent
from ai_toolbox.providers import ChatMessage, ChatResponse
from ai_toolbox.tools import Tool, ToolParameter, ToolRegistry, ToolCall


class TestAgent:
    """Agent 单元测试."""

    @pytest.fixture
    def mock_provider(self):
        """创建模拟 Provider."""
        provider = MagicMock()
        provider.chat = AsyncMock(return_value=ChatResponse(
            content="Hello!",
            model="test-model"
        ))
        return provider

    @pytest.fixture
    def sample_tool(self):
        """创建示例工具."""
        return Tool(
            name="greet",
            description="问候",
            parameters=[ToolParameter("name", "string", "名字")],
            function=lambda name: f"Hello, {name}!"
        )

    @pytest.fixture
    def agent(self, mock_provider, sample_tool):
        """创建 Agent."""
        registry = ToolRegistry()
        registry.register(sample_tool)
        return Agent(mock_provider, registry)

    @pytest.mark.asyncio
    async def test_run_simple_response(self, agent, mock_provider):
        """测试简单响应（无工具调用）."""
        response = await agent.run("Hi")
        
        assert response == "Hello!"
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_tool_call(self, agent, mock_provider):
        """测试工具调用."""
        # 第一次返回工具调用，第二次返回最终结果
        mock_provider.chat.side_effect = [
            ChatResponse(
                content='```json\n{"tool": "greet", "arguments": {"name": "World"}}\n```',
                model="test"
            ),
            ChatResponse(content="Done!", model="test")
        ]
        
        response = await agent.run("Say hello")
        
        assert response == "Done!"
        assert mock_provider.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_run_max_iterations(self, agent, mock_provider):
        """测试最大迭代次数."""
        # 每次都返回工具调用
        mock_provider.chat.return_value = ChatResponse(
            content='```json\n{"tool": "greet", "arguments": {"name": "World"}}\n```',
            model="test"
        )
        
        agent.max_iterations = 2
        response = await agent.run("Test")
        
        assert "太多步骤" in response
        assert mock_provider.chat.call_count == 2

    def test_parse_tool_call_valid(self, agent):
        """测试解析有效工具调用."""
        content = '```json\n{"tool": "greet", "arguments": {"name": "Test"}}\n```'
        
        result = agent._parse_tool_call(content)
        
        assert result is not None
        assert result.name == "greet"
        assert result.arguments == {"name": "Test"}

    def test_parse_tool_call_inline_json(self, agent):
        """测试解析内联 JSON."""
        content = '{"tool": "greet", "arguments": {"name": "Test"}}'
        
        result = agent._parse_tool_call(content)
        
        assert result is not None
        assert result.name == "greet"

    def test_parse_tool_call_no_tool(self, agent):
        """测试无工具调用."""
        content = "Just a normal response"
        
        result = agent._parse_tool_call(content)
        
        assert result is None

    def test_parse_tool_call_invalid_tool(self, agent):
        """测试无效工具."""
        content = '{"tool": "nonexistent", "arguments": {}}'
        
        result = agent._parse_tool_call(content)
        
        assert result is None

    def test_parse_tool_call_invalid_json(self, agent):
        """测试无效 JSON."""
        content = "{invalid json}"
        
        result = agent._parse_tool_call(content)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_chat_simple(self, agent, mock_provider):
        """测试简单聊天."""
        messages = [ChatMessage(role="user", content="Hi")]
        
        response = await agent.chat(messages)
        
        assert response == "Hello!"

    def test_add_tool(self, agent):
        """测试添加工具."""
        new_tool = Tool(
            name="new_tool",
            description="新工具",
            parameters=[],
            function=lambda: "ok"
        )
        
        agent.add_tool(new_tool)
        
        assert "new_tool" in agent.tools

    def test_remove_tool(self, agent, sample_tool):
        """测试移除工具."""
        agent.remove_tool("greet")
        
        assert "greet" not in agent.tools

    def test_default_system_prompt(self, mock_provider):
        """测试默认系统提示词."""
        agent = Agent(mock_provider)
        
        assert "AI 助手" in agent.system_prompt
        assert "工具" in agent.system_prompt