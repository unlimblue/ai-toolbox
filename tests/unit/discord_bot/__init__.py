"""Discord Bot 模块测试初始化."""

import pytest


@pytest.fixture
def mock_discord_env():
    """模拟 Discord 环境变量."""
    with patch.dict("os.environ", {"DISCORD_TOKEN": "mock.token"}):
        yield