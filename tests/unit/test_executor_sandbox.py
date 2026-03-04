"""Executor 沙盒执行器测试."""

import pytest
from ai_toolbox.executor import SandboxExecutor, ExecutionResult


class TestSandboxExecutor:
    """测试沙盒执行器."""

    @pytest.fixture
    def executor(self):
        """创建执行器实例."""
        return SandboxExecutor(timeout=10)

    @pytest.mark.asyncio
    async def test_run_success(self, executor):
        """测试成功执行."""
        result = await executor.run("echo 'hello'")
        
        assert result.success is True
        assert "hello" in result.stdout
        assert result.stderr == ""
        assert result.return_code == 0

    @pytest.mark.asyncio
    async def test_run_failure(self, executor):
        """测试执行失败."""
        result = await executor.run("exit 1")
        
        assert result.success is False
        assert result.return_code == 1

    @pytest.mark.asyncio
    async def test_run_timeout(self, executor):
        """测试超时."""
        result = await executor.run("sleep 20", timeout=0.1)
        
        assert result.success is False
        assert "超时" in result.stderr or "timeout" in result.stderr.lower()

    @pytest.mark.asyncio
    async def test_run_script_bash(self, executor):
        """测试执行 bash 脚本."""
        script = "echo 'test'"
        result = await executor.run_script(script, language="bash")
        
        assert result.success is True
        assert "test" in result.stdout

    @pytest.mark.asyncio
    async def test_run_script_python(self, executor):
        """测试执行 python 脚本."""
        script = "print('hello python')"
        result = await executor.run_script(script, language="python")
        
        assert result.success is True
        assert "hello python" in result.stdout

    @pytest.mark.asyncio
    async def test_check_command_exists(self, executor):
        """测试检查命令存在."""
        result = await executor.check_command("echo")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_command_not_exists(self, executor):
        """测试检查命令不存在."""
        result = await executor.check_command("not_exist_command_12345")
        assert result is False


class TestExecutionResult:
    """测试执行结果."""

    def test_result_creation(self):
        """测试结果创建."""
        result = ExecutionResult(
            success=True,
            stdout="output",
            stderr="",
            return_code=0,
            duration=1.5
        )
        
        assert result.success is True
        assert result.stdout == "output"
        assert result.duration == 1.5