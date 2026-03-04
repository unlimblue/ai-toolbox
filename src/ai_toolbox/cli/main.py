"""CLI 主入口 - 简化版."""

import asyncio
from typing import Any

import click

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import ChatMessage, create_provider
from ai_toolbox.web_search import WebSearchTool

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


def _get_api_key(provider: str) -> str | None:
    """获取 API key."""
    if provider == "kimi":
        return settings.kimi_api_key
    elif provider == "openrouter":
        return settings.openrouter_api_key
    return None


if __name__ == "__main__":
    cli()