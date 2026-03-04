"""CLI 主入口 - 简化版."""

import asyncio
from typing import Any

import click

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import ChatMessage, create_provider
from ai_toolbox.web_search import WebSearchTool
from ai_toolbox.executor import SandboxExecutor

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """AI-Toolbox CLI."""
    pass


@cli.command()
@click.option("--provider", "-p", default="kimi", help="AI 提供商 (kimi, openrouter)")
@click.option("--prompt", required=True, help="对话内容")
def chat(provider: str, prompt: str) -> None:
    """与 AI 对话."""
    asyncio.run(_chat_async(provider, prompt))


async def _chat_async(provider: str, prompt: str) -> None:
    """异步聊天实现."""
    api_key = _get_api_key(provider)
    if not api_key:
        click.echo(f"错误: 未设置 {provider.upper()}_API_KEY", err=True)
        return

    client = create_provider(provider, api_key)

    try:
        messages = [ChatMessage(role="user", content=prompt)]
        response = await client.chat(messages)
        click.echo(response.content)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        click.echo(f"错误: {e}", err=True)
    finally:
        await client.close()


@cli.command()
@click.option("--query", "-q", required=True, help="搜索关键词")
def search(query: str) -> None:
    """网络搜索."""
    asyncio.run(_search_async(query))


async def _search_async(query: str) -> None:
    """异步搜索实现."""
    try:
        tool = WebSearchTool()
        result = await tool.execute(query)
        click.echo(result)
    except Exception as e:
        click.echo(f"搜索错误: {e}", err=True)


@cli.command()
@click.option("--command", "-c", required=True, help="要执行的命令")
@click.option("--timeout", "-t", default=30.0, help="超时时间（秒）")
def exec(command: str, timeout: float) -> None:
    """执行 shell 命令（沙盒）."""
    asyncio.run(_exec_async(command, timeout))


async def _exec_async(command: str, timeout: float) -> None:
    """异步执行实现."""
    executor = SandboxExecutor(timeout=timeout)
    result = await executor.run(command)
    
    if result.stdout:
        click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)
    
    if not result.success:
        click.echo(f"执行失败 (返回码: {result.return_code})", err=True)


@cli.command()
@click.option("--script", "-s", required=True, help="脚本内容")
@click.option("--language", "-l", default="bash", help="脚本语言 (bash, python, sh)")
@click.option("--timeout", "-t", default=30.0, help="超时时间（秒）")
def script(script: str, language: str, timeout: float) -> None:
    """执行脚本（沙盒）."""
    asyncio.run(_script_async(script, language, timeout))


async def _script_async(script_content: str, language: str, timeout: float) -> None:
    """异步脚本执行实现."""
    executor = SandboxExecutor(timeout=timeout)
    result = await executor.run_script(script_content, language)
    
    if result.stdout:
        click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)


@cli.command()
@click.option("--provider", "-p", default="kimi", help="AI 提供商")
def models(provider: str) -> None:
    """列出可用模型."""
    api_key = _get_api_key(provider)
    if not api_key:
        click.echo(f"错误: 未设置 {provider.upper()}_API_KEY", err=True)
        return

    client = create_provider(provider, api_key)
    model_list = client.list_models()

    click.echo(f"{provider} 可用模型:")
    for m in model_list:
        click.echo(f"  - {m}")


# GitHub Issue 命令组
@cli.group()
def issue():
    """GitHub Issue 管理."""
    pass


@issue.command()
@click.option("--title", "-t", required=True, help="Issue 标题")
@click.option("--body", "-b", help="Issue 内容")
@click.option("--repo", "-r", help="仓库 (格式: owner/repo)")
def create(title: str, body: str | None, repo: str | None) -> None:
    """创建 GitHub Issue."""
    asyncio.run(_issue_create_async(title, body, repo))


async def _issue_create_async(title: str, body: str | None, repo: str | None) -> None:
    """异步创建 Issue."""
    try:
        from ai_toolbox.github import GitHubIssueManager
        
        manager = GitHubIssueManager(repo=repo)
        issue = await manager.create_issue(title=title, body=body)
        
        click.echo(f"✅ Issue 创建成功!")
        click.echo(f"   编号: #{issue['number']}")
        click.echo(f"   标题: {issue['title']}")
        click.echo(f"   链接: {issue['html_url']}")
    except Exception as e:
        click.echo(f"❌ 创建失败: {e}", err=True)


@issue.command()
@click.option("--repo", "-r", help="仓库 (格式: owner/repo)")
@click.option("--limit", "-l", default=10, help="数量限制")
def list(repo: str | None, limit: int) -> None:
    """列出 GitHub Issues."""
    asyncio.run(_issue_list_async(repo, limit))


async def _issue_list_async(repo: str | None, limit: int) -> None:
    """异步列出 Issues."""
    try:
        from ai_toolbox.github import GitHubIssueManager
        
        manager = GitHubIssueManager(repo=repo)
        issues = await manager.list_issues(limit=limit)
        
        click.echo(f"📋 Issues ({len(issues)}):")
        for issue in issues:
            state = "🟢" if issue["state"] == "open" else "🔴"
            click.echo(f"   {state} #{issue['number']}: {issue['title']}")
    except Exception as e:
        click.echo(f"❌ 列出失败: {e}", err=True)


@issue.command()
@click.argument("number", type=int)
@click.option("--repo", "-r", help="仓库 (格式: owner/repo)")
def close(number: int, repo: str | None) -> None:
    """关闭 GitHub Issue."""
    asyncio.run(_issue_close_async(number, repo))


async def _issue_close_async(number: int, repo: str | None) -> None:
    """异步关闭 Issue."""
    try:
        from ai_toolbox.github import GitHubIssueManager
        
        manager = GitHubIssueManager(repo=repo)
        issue = await manager.close_issue(number)
        
        click.echo(f"✅ Issue #{number} 已关闭")
        click.echo(f"   链接: {issue['html_url']}")
    except Exception as e:
        click.echo(f"❌ 关闭失败: {e}", err=True)


def _get_api_key(provider: str) -> str | None:
    """获取 API key."""
    if provider == "kimi":
        return settings.kimi_api_key
    elif provider == "openrouter":
        return settings.openrouter_api_key
    return None


if __name__ == "__main__":
    cli()