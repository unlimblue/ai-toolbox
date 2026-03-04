"""Kimi (Moonshot) 提供商实现.

支持两种 API 端点:
1. 标准 Moonshot API: https://api.moonshot.cn/v1 (OpenAI 格式)
2. Kimi Coding API: https://api.kimi.com/coding/ (Anthropic 格式)
"""

import aiohttp
from typing import Any, AsyncGenerator

from .base import BaseProvider, ChatMessage, ChatResponse


class KimiClient(BaseProvider):
    """Kimi API 客户端.

    默认使用 Kimi Coding API (与 OpenClaw 一致).
    """

    # Kimi Coding API (Anthropic Messages 格式)
    BASE_URL = "https://api.kimi.com/coding"
    DEFAULT_MODEL = "k2p5"

    AVAILABLE_MODELS = [
        "k2p5",  # Kimi for Coding (与 OpenClaw 一致)
    ]

    def __init__(self, api_key: str, **kwargs: Any):
        super().__init__(api_key, **kwargs)
        self.session: aiohttp.ClientSession | None = None
        self.use_anthropic_format = True  # 默认使用 Anthropic 格式

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话."""
        if self.session is None or self.session.closed:
            # Anthropic Messages API 使用 x-api-key 头
            self.session = aiohttp.ClientSession(
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                }
            )
        return self.session

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,  # 降低默认 token 数避免余额不足
        **kwargs: Any,
    ) -> ChatResponse:
        """发送聊天请求 (Anthropic Messages API 格式)."""
        session = await self._get_session()
        model = model or self.DEFAULT_MODEL

        # Anthropic Messages API 格式
        # 转换消息格式
        system_msg = None
        chat_messages = []

        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
        }

        if system_msg:
            payload["system"] = system_msg

        if temperature is not None:
            payload["temperature"] = temperature

        payload.update(kwargs)

        async with session.post(
            f"{self.BASE_URL}/v1/messages", json=payload
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"Kimi API error: {data}")

            # Anthropic 格式响应
            content = ""
            if "content" in data and len(data["content"]) > 0:
                content = data["content"][0].get("text", "")

            return ChatResponse(
                content=content,
                model=data.get("model", model),
                usage=data.get("usage"),
                raw_response=data,
            )

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """流式聊天响应."""
        session = await self._get_session()
        model = model or self.DEFAULT_MODEL

        # 转换消息格式
        system_msg = None
        chat_messages = []

        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        payload: dict[str, Any] = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if system_msg:
            payload["system"] = system_msg

        if temperature is not None:
            payload["temperature"] = temperature

        payload.update(kwargs)

        async with session.post(
            f"{self.BASE_URL}/v1/messages", json=payload
        ) as resp:
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    import json

                    try:
                        chunk = json.loads(data_str)
                        # Anthropic 流式格式
                        if chunk.get("type") == "content_block_delta":
                            delta = chunk.get("delta", {})
                            if "text" in delta:
                                yield delta["text"]
                    except json.JSONDecodeError:
                        continue

    def list_models(self) -> list[str]:
        """返回可用模型列表."""
        return self.AVAILABLE_MODELS.copy()

    async def close(self) -> None:
        """关闭会话."""
        if self.session and not self.session.closed:
            await self.session.close()