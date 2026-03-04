"""CLI 主入口."""

import asyncio
from typing import Any

import click

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import ChatMessage, create_provider

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """AI-Toolbox CLI."""
    pass


@cli.command()
@click.option("--provider", "-p", default="kimi", help="AI 提供商 (kimi, openrouter)")
@click.option("--model", "-m", help="模型名称")
@click.option("--prompt", required=True, help="对话内容")
@click.option("--temperature", "-t", default=0.7, type=float, help="温度参数")
@click.option("--stream", is_flag=True, help="流式输出")
def chat(provider: str, model: str | None, prompt: str, temperature: float, stream: bool) -> None:
    """与 AI 对话."""
    asyncio.run(_chat_async(provider, model, prompt, temperature, stream))


async def _chat_async(
    provider: str, model: str | None, prompt: str, temperature: float, stream: bool
) -> None:
    """异步聊天实现."""
    # 获取 API key
    api_key = _get_api_key(provider)
    if not api_key:
        click.echo(f"错误: 未设置 {provider.upper()}_API_KEY", err=True)
        return

    client = create_provider(provider, api_key)

    try:
        messages = [ChatMessage(role="user", content=prompt)]

        if stream:
            click.echo("思考中...", nl=False)
            async for chunk in client.stream_chat(messages, model=model, temperature=temperature):
                click.echo(chunk, nl=False)
            click.echo()
        else:
            response = await client.chat(messages, model=model, temperature=temperature)
            click.echo(response.content)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        click.echo(f"错误: {e}", err=True)
    finally:
        await client.close()


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