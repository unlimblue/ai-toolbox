"""网络搜索工具 - 使用 DuckDuckGo (免费).

提供网络搜索能力，无需 API Key.
"""

import asyncio
from dataclasses import dataclass
from typing import Literal

try:
    from duckduckgo_search import AsyncDDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

from ai_toolbox.core import get_logger
from ai_toolbox.tools.base import Tool, ToolParameter

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜索结果项."""
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


class WebSearchTool(Tool):
    """网络搜索工具.
    
    使用 DuckDuckGo 进行免费网络搜索，无需 API Key.
    
    示例:
        >>> tool = WebSearchTool()
        >>> results = await tool.execute(query="Python 教程")
        >>> print(results)
    """
    
    def __init__(
        self,
        max_results: int = 5,
        region: str = "wt-wt",  # 全球
        safesearch: str = "moderate"
    ):
        """初始化搜索工具.
        
        Args:
            max_results: 最大结果数 (1-10)
            region: 地区代码，如 "cn-zh" (中国), "us-en" (美国)
            safesearch: 安全搜索级别 (on, moderate, off)
        """
        self.max_results = min(max_results, 10)
        self.region = region
        self.safesearch = safesearch
        
        if not HAS_DDGS:
            logger.warning("duckduckgo-search not installed. Run: pip install duckduckgo-search")
        
        # 初始化 Tool 基类
        super().__init__(
            name="web_search",
            description="搜索网络获取实时信息。当需要最新数据、新闻、或不确定的信息时使用。",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="搜索关键词",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="number",
                    description=f"返回结果数量 (1-10，默认 {self.max_results})",
                    required=False,
                    default=self.max_results
                )
            ],
            function=self.execute
        )
    
    async def execute(
        self,
        query: str,
        max_results: int | None = None
    ) -> str:
        """执行搜索.
        
        Args:
            query: 搜索关键词
            max_results: 返回结果数量
        
        Returns:
            格式化的搜索结果字符串
        """
        # 先检查查询有效性
        if not query or not query.strip():
            return "错误: 搜索关键词不能为空"
        
        # 再检查依赖
        if not HAS_DDGS:
            return "错误: duckduckgo-search 未安装。运行: pip install duckduckgo-search"
        
        max_res = max_results or self.max_results
        max_res = min(max_res, 10)  # 限制最大10条
        
        try:
            logger.info(f"Searching: {query}")
            
            results = []
            async with AsyncDDGS() as ddgs:
                async for result in ddgs.text(
                    query,
                    region=self.region,
                    safesearch=self.safesearch,
                    max_results=max_res
                ):
                    results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("href", ""),
                        snippet=result.get("body", ""),
                        source="duckduckgo"
                    ))
            
            if not results:
                return f"未找到关于 '{query}' 的搜索结果"
            
            # 格式化结果
            formatted = [f"搜索 '{query}' 的结果：\n"]
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. {r.title}")
                formatted.append(f"   URL: {r.url}")
                formatted.append(f"   摘要: {r.snippet[:150]}...")
                formatted.append("")
            
            return "\n".join(formatted)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"搜索错误: {str(e)}"
    
    async def search_raw(
        self,
        query: str,
        max_results: int = 5
    ) -> list[SearchResult]:
        """原始搜索，返回结构化结果.
        
        Args:
            query: 搜索关键词
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        if not HAS_DDGS:
            return []
        
        results = []
        async with AsyncDDGS() as ddgs:
            async for result in ddgs.text(
                query,
                region=self.region,
                safesearch=self.safesearch,
                max_results=max_results
            ):
                results.append(SearchResult(
                    title=result.get("title", ""),
                    url=result.get("href", ""),
                    snippet=result.get("body", ""),
                    source="duckduckgo"
                ))
        
        return results


class WebSearchNewsTool(Tool):
    """新闻搜索工具.
    
    专门用于搜索最新新闻.
    """
    
    def __init__(self, max_results: int = 5):
        self.max_results = min(max_results, 10)
        
        super().__init__(
            name="web_search_news",
            description="搜索最新新闻。当需要获取最新新闻、事件时使用。",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="搜索关键词",
                    required=True
                ),
                ToolParameter(
                    name="max_results",
                    type="number",
                    description=f"返回结果数量 (1-10，默认 {self.max_results})",
                    required=False,
                    default=self.max_results
                )
            ],
            function=self.execute
        )
    
    async def execute(
        self,
        query: str,
        max_results: int | None = None
    ) -> str:
        """执行新闻搜索."""
        if not HAS_DDGS:
            return "错误: duckduckgo-search 未安装"
        
        max_res = max_results or self.max_results
        
        try:
            results = []
            async with AsyncDDGS() as ddgs:
                async for result in ddgs.news(
                    query,
                    max_results=max_res
                ):
                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "source": result.get("source", ""),
                        "date": result.get("date", ""),
                        "body": result.get("body", "")
                    })
            
            if not results:
                return f"未找到关于 '{query}' 的新闻"
            
            formatted = [f"'{query}' 相关新闻：\n"]
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. {r['title']}")
                formatted.append(f"   来源: {r['source']} | 日期: {r['date']}")
                formatted.append(f"   URL: {r['url']}")
                formatted.append("")
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"新闻搜索错误: {str(e)}"


# 便捷函数
def create_web_search_tools() -> list[Tool]:
    """创建所有网络搜索工具.
    
    Returns:
        工具列表
    """
    return [
        WebSearchTool(),
        WebSearchNewsTool()
    ]