"""API 测试 - 简化版."""

import pytest
from unittest.mock import patch, MagicMock


class TestApiServer:
    """API 服务器测试."""

    def test_import(self):
        """测试 API 模块可导入."""
        from ai_toolbox.api import server
        assert server is not None

    def test_app_exists(self):
        """测试 app 存在."""
        from ai_toolbox.api.server import app
        assert app is not None