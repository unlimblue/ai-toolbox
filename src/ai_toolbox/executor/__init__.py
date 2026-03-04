"""Executor 模块 - 沙盒执行器.

支持执行 bash 脚本、Python 代码等。

示例:
    from ai_toolbox.executor import SandboxExecutor
    
    executor = SandboxExecutor()
    result = await executor.run("ls -la")
    print(result.stdout)
"""

from .core import SandboxExecutor, ExecutionResult

__all__ = [
    "SandboxExecutor",
    "ExecutionResult",
]