"""提供商工厂."""

from typing import Any

from .base import BaseProvider
from .kimi import KimiClient
from .openrouter import OpenRouterClient


PROVIDERS = {
    "kimi": KimiClient,
    "openrouter": OpenRouterClient,
}


def create_provider(name: str, api_key: str, **kwargs: Any) -> BaseProvider:
    """创建提供商客户端.

    Args:
        name: 提供商名称 (kimi, openrouter)
        api_key: API 密钥
        **kwargs: 额外配置

    Returns:
        BaseProvider: 提供商客户端实例

    Raises:
        ValueError: 未知提供商
    """
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")

    return PROVIDERS[name](api_key, **kwargs)