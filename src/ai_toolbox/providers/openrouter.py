"""OpenRouter 提供商实现."""

import aiohttp
from typing import Any, AsyncGenerator

from .base import BaseProvider, ChatMessage, ChatResponse


class OpenRouterClient(BaseProvider):
    """OpenRouter API 客户端."""

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

    POPULAR_MODELS = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-opus",
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "google/gemini-pro-1.5",
        "meta-llama/llama-3.1-70b-instruct",
    ]

    def __init__(self, api_key: str, **kwargs: Any):
        super().__init__(api_key, **kwargs)
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.config.get("referer", "https://ai-toolbox.local"),
                    "X-Title": self.config.get("title", "AI-Toolbox"),
                }
            )
        return self.session

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> ChatResponse:
        """发送聊天请求."""
        session = await self._get_session()
        model = model or self.DEFAULT_MODEL

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        payload.update(kwargs)

        async with session.post(
            f"{self.BASE_URL}/chat/completions", json=payload
        ) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise RuntimeError(f"OpenRouter API error: {data}")

            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", model),
                usage=data.get("usage"),
                raw_response=data,
            )

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """流式聊天响应."""
        session = await self._get_session()
        model = model or self.DEFAULT_MODEL

        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        payload.update(kwargs)

        async with session.post(
            f"{self.BASE_URL}/chat/completions", json=payload
        ) as resp:
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    chunk = json.loads(data)
                    delta = chunk["choices"][0]["delta"]
                    if "content" in delta:
                        yield delta["content"]

    def list_models(self) -> list[str]:
        """返回热门模型列表."""
        return self.POPULAR_MODELS.copy()

    async def close(self) -> None:
        """关闭会话."""
        if self.session and not self.session.closed:
            await self.session.close()