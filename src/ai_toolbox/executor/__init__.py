"""Executor 模块.

任务执行和管理功能，支持异步执行、并发控制、超时和重试。

示例:
    from ai_toolbox.executor import AsyncExecutor
    
    executor = AsyncExecutor(max_workers=4)
    result = await executor.execute(my_function, args)
"""

from .core import AsyncExecutor, SyncExecutor, TaskResult, create_executor

__all__ = [
    "AsyncExecutor",
    "SyncExecutor",
    "TaskResult",
    "create_executor",
]