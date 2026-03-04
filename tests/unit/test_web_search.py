"""Web Search 工具单元测试."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_toolbox.tools.web_search import (
    WebSearchTool,
    WebSearchNewsTool,
    SearchResult,
    create_web_search_tools,
    HAS_DDGS
)


class TestSearchResult:
    """测试 SearchResult."""

    def test_create(self):
        """测试创建搜索结果."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="duckduckgo"
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "duckduckgo"


class TestWebSearchTool:
    """测试 WebSearchTool."""

    @pytest.fixture
    def search_tool(self):
        """创建搜索工具实例."""
        return WebSearchTool(max_results=3)

    def test_init(self, search_tool):
        """测试初始化."""
        assert search_tool.name == "web_search"
        assert search_tool.max_results == 3
        assert "搜索网络" in search_tool.description
        assert len(search_tool.parameters) == 2

    def test_init_default_params(self):
        """测试默认参数."""
        tool = WebSearchTool()
        assert tool.max_results == 5  # 默认值
        assert tool.region == "wt-wt"
        assert tool.safesearch == "moderate"

    @pytest.mark.asyncio
    async def test_execute_empty_query(self, search_tool):
        """测试空查询."""
        result = await search_tool.execute("")
        assert "不能为空" in result

    @pytest.mark.asyncio
    async def test_execute_whitespace_query(self, search_tool):
        """测试空白查询."""
        result = await search_tool.execute("   ")
        assert "不能为空" in result

    @pytest.mark.asyncio
    async def test_execute_no_ddgs(self, search_tool):
        """测试未安装 DDGS."""
        with patch('ai_toolbox.tools.web_search.HAS_DDGS', False):
            result = await search_tool.execute("valid query")  # 使用有效查询
            assert "未安装" in result

    @pytest.mark.skipif(not HAS_DDGS, reason="duckduckgo-search not installed")
    @pytest.mark.asyncio
    async def test_execute_success(self, search_tool):
        """测试成功搜索（需要网络）."""
        # 这个测试需要实际网络连接
        # 使用 mock 避免真实请求
        mock_result = {
            "title": "Python Tutorial",
            "href": "https://python.org",
            "body": "Python is a programming language"
        }
        
        with patch('ai_toolbox.tools.web_search.AsyncDDGS') as MockDDGS:
            mock_ddgs = MagicMock()
            mock_ddgs.text = AsyncMock(return_value=AsyncMock(
                __aiter__=AsyncMock(return_value=iter([mock_result]))
            ))
            MockDDGS.return_value.__aenter__ = AsyncMock(return_value=mock_ddgs)
            MockDDGS.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await search_tool.execute("python tutorial")
            
            assert "Python Tutorial" in result
            assert "https://python.org" in result

    def test_search_raw_not_async(self):
        """测试 search_raw 是异步方法."""
        tool = WebSearchTool()
        import inspect
        assert inspect.iscoroutinefunction(tool.search_raw)

    @pytest.mark.asyncio
    async def test_max_results_limit(self):
        """测试最大结果数限制."""
        tool = WebSearchTool(max_results=15)  # 超过10
        assert tool.max_results == 10  # 应该被限制为10


class TestWebSearchNewsTool:
    """测试 WebSearchNewsTool."""

    @pytest.fixture
    def news_tool(self):
        """创建新闻工具实例."""
        return WebSearchNewsTool(max_results=3)

    def test_init(self, news_tool):
        """测试初始化."""
        assert news_tool.name == "web_search_news"
        assert "新闻" in news_tool.description

    @pytest.mark.asyncio
    async def test_execute_no_ddgs(self, news_tool):
        """测试未安装 DDGS."""
        with patch('ai_toolbox.tools.web_search.HAS_DDGS', False):
            result = await news_tool.execute("test")
            assert "未安装" in result


class TestCreateWebSearchTools:
    """测试 create_web_search_tools."""

    def test_create(self):
        """测试创建所有搜索工具."""
        tools = create_web_search_tools()
        
        assert len(tools) == 2
        assert any(t.name == "web_search" for t in tools)
        assert any(t.name == "web_search_news" for t in tools)