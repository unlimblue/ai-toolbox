"""GitHub Issue 管理模块.

提供创建、列出、更新、关闭 Issue 的功能.
"""

import os
from typing import Any

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from ai_toolbox.core import get_logger

logger = get_logger(__name__)


class GitHubIssueManager:
    """GitHub Issue 管理器."""
    
    def __init__(self, token: str | None = None, repo: str | None = None):
        """初始化.
        
        Args:
            token: GitHub Personal Access Token
            repo: 仓库名，格式: owner/repo
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo = repo or os.getenv("GITHUB_REPO")
        self.base_url = "https://api.github.com"
        
        if not self.token:
            raise ValueError("GitHub token required")
        if not self.repo:
            raise ValueError("GitHub repo required (format: owner/repo)")
    
    def _get_headers(self) -> dict[str, str]:
        """获取请求头."""
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    async def create_issue(
        self,
        title: str,
        body: str | None = None,
        labels: list[str] | None = None
    ) -> dict[str, Any]:
        """创建 Issue.
        
        Args:
            title: Issue 标题
            body: Issue 内容
            labels: 标签列表
        
        Returns:
            创建的 Issue 信息
        """
        if not HAS_HTTPX:
            raise ImportError("httpx required. Run: pip install httpx")
        
        url = f"{self.base_url}/repos/{self.repo}/issues"
        
        data = {"title": title}
        if body:
            data["body"] = body
        if labels:
            data["labels"] = labels
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json=data
            )
            response.raise_for_status()
            return response.json()
    
    async def list_issues(
        self,
        state: str = "open",
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """列出 Issue.
        
        Args:
            state: 状态 (open, closed, all)
            limit: 数量限制
        
        Returns:
            Issue 列表
        """
        if not HAS_HTTPX:
            raise ImportError("httpx required")
        
        url = f"{self.base_url}/repos/{self.repo}/issues"
        params = {"state": state, "per_page": limit}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json()
    
    async def get_issue(self, issue_number: int) -> dict[str, Any]:
        """获取单个 Issue.
        
        Args:
            issue_number: Issue 编号
        
        Returns:
            Issue 信息
        """
        if not HAS_HTTPX:
            raise ImportError("httpx required")
        
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
    
    async def close_issue(self, issue_number: int) -> dict[str, Any]:
        """关闭 Issue.
        
        Args:
            issue_number: Issue 编号
        
        Returns:
            更新后的 Issue 信息
        """
        if not HAS_HTTPX:
            raise ImportError("httpx required")
        
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self._get_headers(),
                json={"state": "closed"}
            )
            response.raise_for_status()
            return response.json()
    
    async def add_comment(
        self,
        issue_number: int,
        body: str
    ) -> dict[str, Any]:
        """添加评论.
        
        Args:
            issue_number: Issue 编号
            body: 评论内容
        
        Returns:
            创建的评论信息
        """
        if not HAS_HTTPX:
            raise ImportError("httpx required")
        
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={"body": body}
            )
            response.raise_for_status()
            return response.json()