"""FastAPI 服务."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from ai_toolbox.core import get_logger, settings
from ai_toolbox.providers import ChatMessage, create_provider
from ai_toolbox.providers.base import BaseProvider
from ai_toolbox.executor import SandboxExecutor

logger = get_logger(__name__)

# 全局客户端缓存
_clients: dict[str, BaseProvider] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理."""
    logger.info("Starting AI-Toolbox API server")
    yield
    # 清理
    for client in _clients.values():
        await client.close()
    logger.info("Server shutdown")


app = FastAPI(
    title="AI-Toolbox API",
    description="统一 AI 模型调用接口",
    version="0.1.0",
    lifespan=lifespan,
)


# Pydantic 模型
class ChatRequest(BaseModel):
    """聊天请求."""

    provider: str = "kimi"
    model: str | None = None
    messages: list[dict[str, str]]
    temperature: float = 0.7
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应."""

    content: str
    model: str
    usage: dict[str, int] | None = None


class ExecutionRequest(BaseModel):
    """执行请求."""

    command: str
    timeout: float = 30.0


class ExecutionResponse(BaseModel):
    """执行响应."""

    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration: float


def get_client(provider: str) -> BaseProvider:
    """获取或创建客户端."""
    if provider not in _clients:
        api_key = _get_api_key(provider)
        if not api_key:
            raise HTTPException(
                status_code=400, detail=f"{provider} API key not configured"
            )
        _clients[provider] = create_provider(provider, api_key)
    return _clients[provider]


def verify_api_key(x_api_key: str | None = Header(None)) -> None:
    """验证 API key."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _get_api_key(provider: str) -> str | None:
    """获取 API key."""
    if provider == "kimi":
        return settings.kimi_api_key
    elif provider == "openrouter":
        return settings.openrouter_api_key
    return None


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(
    request: ChatRequest,
    _=Depends(verify_api_key),
) -> ChatResponse:
    """聊天补全接口."""
    client = get_client(request.provider)

    messages = [ChatMessage(role=m["role"], content=m["content"]) for m in request.messages]

    try:
        response = await client.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
        )
        return ChatResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/models")
async def list_models(provider: str = "kimi") -> dict[str, Any]:
    """列出可用模型."""
    client = get_client(provider)
    return {"provider": provider, "models": client.list_models()}


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查."""
    return {"status": "ok"}


@app.post("/v1/execute", response_model=ExecutionResponse)
async def execute_command(
    request: ExecutionRequest,
) -> ExecutionResponse:
    """执行 shell 命令（沙盒）."""
    executor = SandboxExecutor(timeout=request.timeout)
    result = await executor.run(request.command)
    
    return ExecutionResponse(
        success=result.success,
        stdout=result.stdout,
        stderr=result.stderr,
        return_code=result.return_code,
        duration=result.duration
    )


@app.get("/v1/search")
async def search_web(q: str, max_results: int = 5) -> dict[str, Any]:
    """网络搜索."""
    from ai_toolbox.web_search import WebSearchTool
    
    try:
        tool = WebSearchTool(max_results=max_results)
        result = await tool.execute(q)
        return {
            "success": True,
            "query": q,
            "result": result
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))