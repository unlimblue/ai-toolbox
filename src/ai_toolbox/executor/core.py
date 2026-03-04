"""Executor 模块 - 沙盒执行器.

支持执行 bash 脚本、Python 代码等，类似 OpenClaw 的 sandbox。
"""

import asyncio
import subprocess
import tempfile
import os
from dataclasses import dataclass
from typing import Any
from pathlib import Path

from ai_toolbox.core import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """执行结果."""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration: float


class SandboxExecutor:
    """沙盒执行器.
    
    安全地执行 shell 命令和脚本。
    
    示例:
        executor = SandboxExecutor()
        result = await executor.run("ls -la")
        print(result.stdout)
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        cwd: str | None = None,
        env: dict[str, str] | None = None
    ):
        """初始化执行器.
        
        Args:
            timeout: 默认超时时间（秒）
            cwd: 工作目录
            env: 环境变量
        """
        self.timeout = timeout
        self.cwd = cwd or os.getcwd()
        self.env = {**os.environ, **(env or {})}
    
    async def run(
        self,
        command: str,
        timeout: float | None = None,
        cwd: str | None = None
    ) -> ExecutionResult:
        """执行 shell 命令.
        
        Args:
            command: 命令字符串
            timeout: 超时时间（秒）
            cwd: 工作目录
        
        Returns:
            执行结果
        """
        timeout = timeout or self.timeout
        cwd = cwd or self.cwd
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=self.env
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            duration = asyncio.get_event_loop().time() - start_time
            
            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout.decode('utf-8', errors='replace'),
                stderr=stderr.decode('utf-8', errors='replace'),
                return_code=process.returncode,
                duration=duration
            )
            
        except asyncio.TimeoutError:
            duration = asyncio.get_event_loop().time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"执行超时（{timeout}秒）",
                return_code=-1,
                duration=duration
            )
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                duration=duration
            )
    
    async def run_script(
        self,
        script: str,
        language: str = "bash",
        timeout: float | None = None
    ) -> ExecutionResult:
        """执行脚本.
        
        Args:
            script: 脚本内容
            language: 语言类型 (bash, python, sh)
            timeout: 超时时间
        
        Returns:
            执行结果
        """
        timeout = timeout or self.timeout
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{language}',
            delete=False
        ) as f:
            f.write(script)
            script_path = f.name
        
        try:
            # 根据语言选择执行命令
            if language == 'python':
                command = f'python3 "{script_path}"'
            elif language == 'bash':
                command = f'bash "{script_path}"'
            else:
                command = f'sh "{script_path}"'
            
            result = await self.run(command, timeout)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(script_path)
            except:
                pass
        
        return result
    
    async def check_command(self, command: str) -> bool:
        """检查命令是否存在.
        
        Args:
            command: 命令名
        
        Returns:
            是否存在
        """
        result = await self.run(f'which {command}')
        return result.success