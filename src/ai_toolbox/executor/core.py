"""Executor 模块.

提供任务执行和管理功能，支持异步执行、队列管理、超时控制等.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor


@dataclass
class TaskResult:
    """任务执行结果."""
    success: bool
    result: Any
    duration: float  # 执行时间（秒）
    error: str | None = None


class AsyncExecutor:
    """异步执行器.
    
    管理异步任务的执行，支持超时控制和并发限制。
    
    示例:
        executor = AsyncExecutor(max_workers=4)
        
        # 执行单个任务
        result = await executor.execute(my_async_function, args)
        
        # 批量执行
        results = await executor.execute_batch([
            (func1, args1),
            (func2, args2),
        ])
    """
    
    def __init__(self, max_workers: int = 4):
        """初始化执行器.
        
        Args:
            max_workers: 最大并发数
        """
        self.max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)
    
    async def execute(
        self,
        func: Callable[..., Coroutine],
        *args,
        timeout: float | None = None,
        **kwargs
    ) -> TaskResult:
        """执行异步函数.
        
        Args:
            func: 要执行的异步函数
            *args: 位置参数
            timeout: 超时时间（秒）
            **kwargs: 关键字参数
        
        Returns:
            任务执行结果
        """
        start_time = time.time()
        
        async with self._semaphore:
            try:
                if timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                else:
                    result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                return TaskResult(
                    success=True,
                    result=result,
                    duration=duration
                )
                
            except asyncio.TimeoutError:
                duration = time.time() - start_time
                return TaskResult(
                    success=False,
                    result=None,
                    duration=duration,
                    error=f"执行超时（{timeout}秒）"
                )
            except Exception as e:
                duration = time.time() - start_time
                return TaskResult(
                    success=False,
                    result=None,
                    duration=duration,
                    error=str(e)
                )
    
    async def execute_batch(
        self,
        tasks: list[tuple[Callable, tuple, dict]],
        timeout: float | None = None
    ) -> list[TaskResult]:
        """批量执行任务.
        
        Args:
            tasks: 任务列表，每项为 (func, args, kwargs)
            timeout: 每个任务的超时时间
        
        Returns:
            执行结果列表
        """
        coroutines = [
            self.execute(func, *args, timeout=timeout, **kwargs)
            for func, args, kwargs in tasks
        ]
        
        return await asyncio.gather(*coroutines)
    
    async def execute_with_retry(
        self,
        func: Callable[..., Coroutine],
        *args,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float | None = None,
        **kwargs
    ) -> TaskResult:
        """带重试的执行.
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）
            timeout: 超时时间
            **kwargs: 关键字参数
        
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            result = await self.execute(func, *args, timeout=timeout, **kwargs)
            
            if result.success:
                return result
            
            last_error = result.error
            
            if attempt < max_retries:
                await asyncio.sleep(retry_delay)
        
        # 所有重试都失败
        return TaskResult(
            success=False,
            result=None,
            duration=0,
            error=f"重试{max_retries}次后仍失败: {last_error}"
        )


class SyncExecutor:
    """同步执行器.
    
    在线程池中执行同步函数。
    
    示例:
        executor = SyncExecutor(max_workers=4)
        result = await executor.execute(sync_function, args)
    """
    
    def __init__(self, max_workers: int = 4):
        """初始化执行器.
        
        Args:
            max_workers: 最大线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def execute(
        self,
        func: Callable,
        *args,
        timeout: float | None = None,
        **kwargs
    ) -> TaskResult:
        """在线程池中执行同步函数.
        
        Args:
            func: 要执行的同步函数
            *args: 位置参数
            timeout: 超时时间
            **kwargs: 关键字参数
        
        Returns:
            执行结果
        """
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        
        try:
            # 在线程池中执行
            if timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.executor,
                        lambda: func(*args, **kwargs)
                    ),
                    timeout=timeout
                )
            else:
                result = await loop.run_in_executor(
                    self.executor,
                    lambda: func(*args, **kwargs)
                )
            
            duration = time.time() - start_time
            return TaskResult(
                success=True,
                result=result,
                duration=duration
            )
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                result=None,
                duration=duration,
                error=f"执行超时（{timeout}秒）"
            )
        except Exception as e:
            duration = time.time() - start_time
            return TaskResult(
                success=False,
                result=None,
                duration=duration,
                error=str(e)
            )
    
    def shutdown(self):
        """关闭线程池."""
        self.executor.shutdown(wait=True)


# 便捷函数
def create_executor(max_workers: int = 4, async_mode: bool = True):
    """创建执行器.
    
    Args:
        max_workers: 最大工作数
        async_mode: 是否为异步模式
    
    Returns:
        AsyncExecutor 或 SyncExecutor
    """
    if async_mode:
        return AsyncExecutor(max_workers)
    else:
        return SyncExecutor(max_workers)