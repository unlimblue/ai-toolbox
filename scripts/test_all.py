#!/usr/bin/env python3
"""AI-Toolbox 完整测试脚本 - 测试所有三种使用方式."""

import asyncio
import os
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_toolbox.core.config import Settings
from ai_toolbox.providers import create_provider, ChatMessage


class Colors:
    """终端颜色."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def print_info(msg: str) -> None:
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def print_section(title: str) -> None:
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}{title}{Colors.RESET}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}")


async def test_config() -> bool:
    """测试配置模块."""
    print_section("测试 1: 配置模块")

    try:
        settings = Settings()
        print_success("配置实例创建成功")

        # 检查 API Keys
        kimi_key = settings.kimi_api_key
        openrouter_key = settings.openrouter_api_key

        if kimi_key:
            print_success(f"Kimi API Key: {kimi_key[:10]}...")
        else:
            print_error("Kimi API Key 未配置")

        if openrouter_key:
            print_success(f"OpenRouter API Key: {openrouter_key[:10]}...")
        else:
            print_error("OpenRouter API Key 未配置")

        return bool(kimi_key and openrouter_key)
    except Exception as e:
        print_error(f"配置测试失败: {e}")
        return False


async def test_kimi() -> bool:
    """测试 Kimi API."""
    print_section("测试 2: Kimi Provider")

    try:
        settings = Settings()
        if not settings.kimi_api_key:
            print_error("Kimi API Key 未配置，跳过测试")
            return False

        client = create_provider("kimi", settings.kimi_api_key)
        print_success("Kimi 客户端创建成功")

        # 测试模型列表
        models = client.list_models()
        print_info(f"可用模型: {models}")

        # 测试聊天
        print_info("发送测试消息...")
        messages = [ChatMessage(role="user", content="你好，请用一句话介绍自己")]
        response = await client.chat(messages, temperature=0.7)

        print_success(f"响应成功")
        print_info(f"使用模型: {response.model}")
        print_info(f"Token 使用: {response.usage}")
        print(f"\n响应内容:\n{response.content[:200]}...")

        await client.close()
        return True

    except Exception as e:
        print_error(f"Kimi 测试失败: {e}")
        return False


async def test_openrouter() -> bool:
    """测试 OpenRouter API."""
    print_section("测试 3: OpenRouter Provider")

    try:
        settings = Settings()
        if not settings.openrouter_api_key:
            print_error("OpenRouter API Key 未配置，跳过测试")
            return False

        client = create_provider("openrouter", settings.openrouter_api_key)
        print_success("OpenRouter 客户端创建成功")

        # 测试模型列表
        models = client.list_models()
        print_info(f"可用模型: {models}")

        # 测试聊天 (使用 Claude)
        print_info("发送测试消息 (Claude)...")
        messages = [ChatMessage(role="user", content="Hello, introduce yourself in one sentence")]
        response = await client.chat(
            messages,
            model="anthropic/claude-3.5-sonnet",
            temperature=0.7,
            max_tokens=100,  # 降低 token 数以避免余额不足
        )

        print_success(f"响应成功")
        print_info(f"使用模型: {response.model}")
        print_info(f"Token 使用: {response.usage}")
        print(f"\n响应内容:\n{response.content[:200]}...")

        await client.close()
        return True

    except Exception as e:
        print_error(f"OpenRouter 测试失败: {e}")
        return False


async def test_streaming() -> bool:
    """测试流式响应."""
    print_section("测试 4: 流式响应")

    try:
        settings = Settings()
        client = create_provider("kimi", settings.kimi_api_key)

        print_info("测试流式输出...")
        messages = [ChatMessage(role="user", content="数到5")]

        print("流式响应: ", end="", flush=True)
        async for chunk in client.stream_chat(messages, temperature=0.7):
            print(chunk, end="", flush=True)
        print()

        print_success("流式响应完成")
        await client.close()
        return True

    except Exception as e:
        print_error(f"流式测试失败: {e}")
        return False


async def main() -> int:
    """主测试函数."""
    print(f"{Colors.YELLOW}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           AI-Toolbox 完整测试套件                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

    results = []

    # 运行所有测试
    results.append(("配置模块", await test_config()))
    results.append(("Kimi API", await test_kimi()))
    results.append(("OpenRouter API", await test_openrouter()))
    results.append(("流式响应", await test_streaming()))

    # 汇总结果
    print_section("测试结果汇总")
    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = f"{Colors.GREEN}通过{Colors.RESET}" if result else f"{Colors.RED}失败{Colors.RESET}"
        print(f"  {name}: {status}")

    print()
    if passed == total:
        print(f"{Colors.GREEN}所有测试通过! ({passed}/{total}){Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}部分测试失败 ({passed}/{total}){Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))