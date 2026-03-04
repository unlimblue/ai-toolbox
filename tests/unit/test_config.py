"""配置模块测试."""

import os
from unittest.mock import patch

from ai_toolbox.core.config import Settings


class TestSettings:
    """测试配置类."""

    def test_default_values(self):
        """测试默认值."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.api_host == "0.0.0.0"
            assert settings.api_port == 8000
            assert settings.log_level == "INFO"

    def test_env_override(self):
        """测试环境变量覆盖."""
        env = {
            "API_HOST": "127.0.0.1",
            "API_PORT": "9000",
            "KIMI_API_KEY": "test-key",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000
            assert settings.kimi_api_key == "test-key"