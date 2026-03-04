"""CLI 主入口."""

import asyncio
from pathlib import Path
from typing import Any

import click

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import ChatMessage, create_provider, ImageContent
from ai_toolbox.tools import (
    ToolRegistry,
    calculator_tool,
    get_current_time_tool,
    random_number_tool,
    random_choice_tool,
    count_words_tool,
    format_json_tool,
    read_file_tool,
    list_directory_tool,
)
from ai_toolbox.agent import Agent

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
@click.option("--image", "-i", required=True, help="图像路径或 URL")
@click.option("--prompt", required=True, help="分析提示")
@click.option("--model", "-m", help="模型名称")
@click.option("--temperature", "-t", default=0.7, type=float, help="温度参数")
def vision(provider: str, image: str, prompt: str, model: str | None, temperature: float) -> None:
    """分析图像内容."""
    asyncio.run(_vision_async(provider, image, prompt, model, temperature))


async def _vision_async(
    provider: str, image: str, prompt: str, model: str | None, temperature: float
) -> None:
    """异步图像分析实现."""
    api_key = _get_api_key(provider)
    if not api_key:
        click.echo(f"错误: 未设置 {provider.upper()}_API_KEY", err=True)
        return

    # 检查 provider 是否支持视觉
    if provider not in ["kimi", "openrouter"]:
        click.echo(f"错误: {provider} 不支持视觉功能", err=True)
        return

    try:
        # 准备图像
        if image.startswith("http://") or image.startswith("https://"):
            img_content = ImageContent.from_url(image)
        else:
            if not Path(image).exists():
                click.echo(f"错误: 图像文件不存在: {image}", err=True)
                return
            img_content = ImageContent.from_file(image)

        client = create_provider(provider, api_key)
        
        click.echo("分析图像中...")
        
        # 使用 chat_with_image 方法
        if hasattr(client, 'chat_with_image'):
            response = await client.chat_with_image(
                prompt,
                [img_content],
                model=model,
                temperature=temperature
            )
            click.echo(response.content)
        else:
            click.echo(f"错误: {provider} 客户端不支持视觉功能", err=True)
            
        await client.close()
        
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        click.echo(f"错误: {e}", err=True)


@cli.command()
@click.option("--provider", "-p", default="openrouter", help="AI 提供商")
@click.option("--prompt", "-p", required=True, help="用户输入")
@click.option("--tools", "-t", help="启用的工具（逗号分隔）", default="calculator,get_current_time")
@click.option("--max-iterations", default=5, type=int, help="最大迭代次数")
def agent(provider: str, prompt: str, tools: str, max_iterations: int) -> None:
    """运行 Agent（支持工具调用）."""
    asyncio.run(_agent_async(provider, prompt, tools, max_iterations))


async def _agent_async(provider: str, prompt: str, tools_str: str, max_iterations: int) -> None:
    """异步 Agent 实现."""
    api_key = _get_api_key(provider)
    if not api_key:
        click.echo(f"错误: 未设置 {provider.upper()}_API_KEY", err=True)
        return

    # 解析工具列表
    tool_names = [t.strip() for t in tools_str.split(",")]
    
    # 构建工具注册表
    registry = ToolRegistry()
    available_tools = {
        "calculator": calculator_tool,
        "get_current_time": get_current_time_tool,
        "random_number": random_number_tool,
        "random_choice": random_choice_tool,
        "count_words": count_words_tool,
        "format_json": format_json_tool,
        "read_file": read_file_tool,
        "list_directory": list_directory_tool,
    }
    
    for name in tool_names:
        if name in available_tools:
            registry.register(available_tools[name])
        else:
            click.echo(f"警告: 未知工具 '{name}'，已跳过", err=True)

    try:
        client = create_provider(provider, api_key)
        agent = Agent(client, registry, max_iterations=max_iterations)
        
        click.echo(f"运行 Agent（启用工具: {', '.join(registry.list_names())}）...")
        click.echo()
        
        response = await agent.run(prompt)
        click.echo(response)
        
        await client.close()
        
    except Exception as e:
        logger.error(f"Agent failed: {e}")
        click.echo(f"错误: {e}", err=True)


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