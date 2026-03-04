"""网络搜索工具 - 使用 DuckDuckGo (免费).

提供网络搜索能力，无需 API Key.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

try:
    from duckduckgo_search import AsyncDDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

from ai_toolbox.core import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """搜索结果项."""
    title: str
    url: str
    snippet: str
    source: str = "duckduckgo"


class WebSearchTool:
    """网络搜索工具.
    
    使用 DuckDuckGo 进行免费网络搜索，无需 API Key.
    """
    
    def __init__(
        self,
        max_results: int = 5,
        region: str = "wt-wt",
        safesearch: str = "moderate"
    ):
        self.max_results = min(max_results, 10)
        self.region = region
        self.safesearch = safesearch
        
        if not HAS_DDGS:
            logger.warning("duckduckgo-search not installed")
    
    async def execute(
        self,
        query: str,
        max_results: int | None = None
    ) -> str:
        """执行搜索."""
        if not query or not query.strip():
            return "错误: 搜索关键词不能为空"
        
        if not HAS_DDGS:
            return "错误: duckduckgo-search 未安装"
        
        max_res = max_results or self.max_results
        max_res = min(max_res, 10)
        
        try:
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
            
            formatted = [f"搜索 '{query}' 的结果：\n"]
            for i, r in enumerate(results, 1):
                formatted.append(f"{i}. {r.title}")
                formatted.append(f"   URL: {r.url}")
                formatted.append(f"   摘要: {r.snippet[:150]}...")
                formatted.append("")
            
            return "\n".join(formatted)
            
        except Exception as e:
            return f"搜索错误: {str(e)}"


class WebSearchNewsTool:
    """新闻搜索工具."""
    
    def __init__(self, max_results: int = 5):
        self.max_results = min(max_results, 10)
    
    async def execute(self, query: str, max_results: int | None = None) -> str:
        """执行新闻搜索."""
        if not HAS_DDGS:
            return "错误: duckduckgo-search 未安装"
        
        max_res = max_results or self.max_results
        
        try:
            results = []
            async with AsyncDDGS() as ddgs:
                async for result in ddgs.news(query, max_results=max_res):
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


def create_web_search_tools() -> list[Any]:
    """创建所有网络搜索工具."""
    return [WebSearchTool(), WebSearchNewsTool()]