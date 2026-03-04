"""Web Search 模块.

独立的网络搜索功能模块，支持多种搜索引擎.
"""

from .search import (
    WebSearchTool, 
    WebSearchNewsTool, 
    SearchResult, 
    create_web_search_tools,
    HAS_DDGS
)

__all__ = [
    "WebSearchTool",
    "WebSearchNewsTool", 
    "SearchResult",
    "create_web_search_tools",
    "HAS_DDGS",
]