"""测试配置."""

import pytest


@pytest.fixture
def mock_api_key():
    """模拟 API key."""
    return "test-api-key-12345"