"""Tools 模块单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_toolbox.tools import (
    Tool, ToolCall, ToolResult, ToolParameter, ToolRegistry, ToolExecutor,
    calculator_tool, get_current_time_tool, random_number_tool,
)
from ai_toolbox.tools.builtin import calculator, get_current_time, random_number


class TestToolParameter:
    """测试 ToolParameter."""

    def test_create(self):
        """测试创建参数."""
        param = ToolParameter(
            name="expression",
            type="string",
            description="数学表达式",
            required=True
        )
        assert param.name == "expression"
        assert param.type == "string"
        assert param.description == "数学表达式"
        assert param.required is True


class TestTool:
    """测试 Tool 类."""

    def test_from_function(self):
        """测试从函数创建 Tool."""
        def my_func(a: str, b: int = 10) -> str:
            """测试函数."""
            return f"{a} {b}"
        
        tool = Tool.from_function(my_func)
        
        assert tool.name == "my_func"
        assert tool.description == "测试函数."
        assert len(tool.parameters) == 2
        assert tool.parameters[0].name == "a"
        assert tool.parameters[1].name == "b"
        assert tool.parameters[1].default == 10

    def test_to_openai_format(self):
        """测试 OpenAI 格式转换."""
        tool = Tool(
            name="test",
            description="测试工具",
            parameters=[
                ToolParameter("x", "string", "参数x", required=True),
                ToolParameter("y", "number", "参数y", required=False, default=0)
            ],
            function=lambda x, y=0: x
        )
        
        fmt = tool.to_openai_format()
        
        assert fmt["type"] == "function"
        assert fmt["function"]["name"] == "test"
        assert "x" in fmt["function"]["parameters"]["required"]
        assert "y" not in fmt["function"]["parameters"]["required"]

    def test_to_anthropic_format(self):
        """测试 Anthropic 格式转换."""
        tool = Tool(
            name="test",
            description="测试工具",
            parameters=[ToolParameter("x", "string", "参数x")],
            function=lambda x: x
        )
        
        fmt = tool.to_anthropic_format()
        
        assert fmt["name"] == "test"
        assert "input_schema" in fmt


class TestToolRegistry:
    """测试 ToolRegistry."""

    @pytest.fixture
    def registry(self):
        """创建注册表."""
        return ToolRegistry()

    @pytest.fixture
    def sample_tool(self):
        """创建示例工具."""
        return Tool(
            name="test_tool",
            description="测试工具",
            parameters=[],
            function=lambda: "ok"
        )

    def test_register(self, registry, sample_tool):
        """测试注册工具."""
        registry.register(sample_tool)
        
        assert registry.has("test_tool")
        assert len(registry) == 1

    def test_unregister(self, registry, sample_tool):
        """测试注销工具."""
        registry.register(sample_tool).unregister("test_tool")
        
        assert not registry.has("test_tool")
        assert len(registry) == 0

    def test_get(self, registry, sample_tool):
        """测试获取工具."""
        registry.register(sample_tool)
        
        tool = registry.get("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"
        
        assert registry.get("nonexistent") is None

    def test_list_tools(self, registry, sample_tool):
        """测试列出工具."""
        registry.register(sample_tool)
        
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"

    def test_list_names(self, registry, sample_tool):
        """测试列出工具名称."""
        registry.register(sample_tool)
        
        names = registry.list_names()
        assert "test_tool" in names

    def test_clear(self, registry, sample_tool):
        """测试清空注册表."""
        registry.register(sample_tool).clear()
        
        assert len(registry) == 0

    def test_contains(self, registry, sample_tool):
        """测试 contains 操作符."""
        registry.register(sample_tool)
        
        assert "test_tool" in registry
        assert "other" not in registry

    def test_iter(self, registry, sample_tool):
        """测试迭代."""
        registry.register(sample_tool)
        
        tools = list(registry)
        assert len(tools) == 1
        assert tools[0].name == "test_tool"


class TestToolExecutor:
    """测试 ToolExecutor."""

    @pytest.fixture
    def registry(self):
        """创建注册表."""
        reg = ToolRegistry()
        reg.register(Tool(
            name="greet",
            description="问候",
            parameters=[ToolParameter("name", "string", "名字")],
            function=lambda name: f"Hello, {name}!"
        ))
        return reg

    @pytest.fixture
    def executor(self, registry):
        """创建执行器."""
        return ToolExecutor(registry)

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """测试成功执行."""
        call = ToolCall(id="1", name="greet", arguments={"name": "World"})
        
        result = await executor.execute(call)
        
        assert result.tool_call_id == "1"
        assert result.content == "Hello, World!"
        assert not result.is_error

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, executor):
        """测试工具不存在."""
        call = ToolCall(id="1", name="nonexistent", arguments={})
        
        result = await executor.execute(call)
        
        assert result.is_error
        assert "不存在" in result.content

    @pytest.mark.asyncio
    async def test_execute_missing_param(self, executor):
        """测试缺少参数."""
        call = ToolCall(id="1", name="greet", arguments={})
        
        result = await executor.execute(call)
        
        assert result.is_error
        assert "缺少必需参数" in result.content

    @pytest.mark.asyncio
    async def test_execute_exception(self, executor):
        """测试执行异常."""
        registry = ToolRegistry()
        registry.register(Tool(
            name="error",
            description="会报错",
            parameters=[],
            function=lambda: 1/0
        ))
        executor = ToolExecutor(registry)
        
        call = ToolCall(id="1", name="error", arguments={})
        result = await executor.execute(call)
        
        assert result.is_error
        assert "执行错误" in result.content

    @pytest.mark.asyncio
    async def test_execute_async(self, executor):
        """测试异步函数."""
        async def async_greet(name: str) -> str:
            return f"Hi, {name}!"
        
        registry = ToolRegistry()
        registry.register(Tool(
            name="async_greet",
            description="异步问候",
            parameters=[ToolParameter("name", "string", "名字")],
            function=async_greet
        ))
        executor = ToolExecutor(registry)
        
        call = ToolCall(id="1", name="async_greet", arguments={"name": "Async"})
        result = await executor.execute(call)
        
        assert result.content == "Hi, Async!"

    @pytest.mark.asyncio
    async def test_execute_batch(self, executor):
        """测试批量执行."""
        calls = [
            ToolCall(id="1", name="greet", arguments={"name": "A"}),
            ToolCall(id="2", name="greet", arguments={"name": "B"}),
        ]
        
        results = await executor.execute_batch(calls)
        
        assert len(results) == 2
        assert results[0].content == "Hello, A!"
        assert results[1].content == "Hello, B!"


class TestBuiltinTools:
    """测试内置工具."""

    def test_calculator_basic(self):
        """测试基础计算."""
        assert calculator("2 + 2") == "4"
        assert calculator("10 * 5") == "50"
        assert calculator("100 / 4") == "25"  # 整数结果自动去掉小数

    def test_calculator_advanced(self):
        """测试高级计算."""
        assert calculator("sqrt(16)") == "4"  # 整数结果自动去掉小数
        assert calculator("2 ** 10") == "1024"

    def test_calculator_error(self):
        """测试计算错误."""
        assert "除零" in calculator("1 / 0")
        assert "不允许" in calculator("__import__('os')")

    def test_get_current_time(self):
        """测试获取时间."""
        result = get_current_time()
        # 简单验证格式
        assert len(result) > 0
        assert "202" in result or "2025" in result  # 年份

    def test_get_current_time_with_timezone(self):
        """测试带时区的时间."""
        result_utc = get_current_time("UTC")
        result_sh = get_current_time("Asia/Shanghai")
        # 两者应该不同（如果当前不是 UTC 午夜）
        assert isinstance(result_utc, str)
        assert isinstance(result_sh, str)

    def test_random_number(self):
        """测试随机数."""
        result = random_number(1, 10)
        num = int(result)
        assert 1 <= num <= 10

    def test_calculator_tool(self):
        """测试 calculator_tool."""
        assert calculator_tool.name == "calculator"
        assert "计算" in calculator_tool.description

    def test_get_current_time_tool(self):
        """测试 get_current_time_tool."""
        assert get_current_time_tool.name == "get_current_time"
        assert "时间" in get_current_time_tool.description