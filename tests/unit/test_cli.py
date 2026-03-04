"""CLI 测试 - 简化版."""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, AsyncMock

from ai_toolbox.cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_help(runner):
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0


def test_chat_command(runner):
    with patch('ai_toolbox.cli.main.settings') as mock_settings:
        mock_settings.kimi_api_key = 'test_key'
        
        with patch('ai_toolbox.cli.main.create_provider') as mock_create:
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value=MagicMock(content='Hello'))
            mock_client.close = AsyncMock()
            mock_create.return_value = mock_client
            
            result = runner.invoke(cli, ['chat', '--prompt', '你好'])
            assert result.exit_code == 0


def test_models_command(runner):
    with patch('ai_toolbox.cli.main.settings') as mock_settings:
        mock_settings.kimi_api_key = 'test_key'
        
        with patch('ai_toolbox.cli.main.create_provider') as mock_create:
            mock_client = MagicMock()
            mock_client.list_models.return_value = ['model1']
            mock_create.return_value = mock_client
            
            result = runner.invoke(cli, ['models'])
            assert result.exit_code == 0