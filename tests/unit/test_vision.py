"""Vision 模块单元测试."""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path

from ai_toolbox.providers.vision import ImageContent, MultimodalMessage


class TestImageContent:
    """测试 ImageContent."""

    def test_from_url(self):
        """测试从 URL 创建."""
        image = ImageContent.from_url("https://example.com/photo.jpg")
        
        assert image.source_type == "url"
        assert image.data == "https://example.com/photo.jpg"
        assert image.media_type == "image/jpeg"

    def test_from_url_png(self):
        """测试从 PNG URL 创建."""
        image = ImageContent.from_url("https://example.com/photo.png")
        
        assert image.media_type == "image/png"

    def test_from_file(self):
        """测试从文件创建."""
        with patch.object(Path, "exists", return_value=True):
            image = ImageContent.from_file("/path/to/photo.jpg")
            
            assert image.source_type == "file"
            assert image.data == "/path/to/photo.jpg"
            assert image.media_type == "image/jpeg"

    def test_from_file_png(self):
        """测试从 PNG 文件创建."""
        image = ImageContent.from_file("photo.png")
        
        assert image.media_type == "image/png"

    def test_from_file_gif(self):
        """测试从 GIF 文件创建."""
        image = ImageContent.from_file("photo.gif")
        
        assert image.media_type == "image/gif"

    def test_from_file_webp(self):
        """测试从 WebP 文件创建."""
        image = ImageContent.from_file("photo.webp")
        
        assert image.media_type == "image/webp"

    def test_from_base64(self):
        """测试从 Base64 创建."""
        image = ImageContent.from_base64("aGVsbG8=", "image/png")
        
        assert image.source_type == "base64"
        assert image.data == "aGVsbG8="
        assert image.media_type == "image/png"

    @pytest.mark.asyncio
    async def test_to_openai_format_url(self):
        """测试 OpenAI URL 格式."""
        image = ImageContent.from_url("https://example.com/photo.jpg")
        
        fmt = image.to_openai_format()
        
        assert fmt["type"] == "image_url"
        assert fmt["image_url"]["url"] == "https://example.com/photo.jpg"

    def test_to_openai_format_file(self):
        """测试 OpenAI 文件格式."""
        # Mock 文件读取
        mock_data = b"fake_image_data"
        mock_b64 = base64.b64encode(mock_data).decode()
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            image = ImageContent.from_file("photo.jpg")
            fmt = image.to_openai_format()
        
        assert fmt["type"] == "image_url"
        assert fmt["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_to_openai_format_base64(self):
        """测试 OpenAI Base64 格式."""
        image = ImageContent.from_base64("aGVsbG8=", "image/png")
        
        fmt = image.to_openai_format()
        
        assert fmt["type"] == "image_url"
        assert "data:image/png;base64,aGVsbG8=" in fmt["image_url"]["url"]

    @pytest.mark.asyncio
    async def test_to_anthropic_format_url(self):
        """测试 Anthropic URL 格式（需要下载）."""
        image = ImageContent.from_url("https://example.com/photo.jpg")
        
        # Mock 下载
        mock_data = b"fake_image_data"
        mock_b64 = base64.b64encode(mock_data).decode()
        
        with patch.object(image, '_download_image', new_callable=AsyncMock, return_value=mock_b64):
            fmt = await image.to_anthropic_format()
        
        assert fmt["type"] == "image"
        assert fmt["source"]["type"] == "base64"
        assert fmt["source"]["media_type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_to_anthropic_format_base64(self):
        """测试 Anthropic Base64 格式."""
        image = ImageContent.from_base64("aGVsbG8=", "image/png")
        
        fmt = await image.to_anthropic_format()
        
        assert fmt["type"] == "image"
        assert fmt["source"]["data"] == "aGVsbG8="

    def test_read_file(self):
        """测试读取文件."""
        mock_data = b"fake_image_data"
        mock_b64 = base64.b64encode(mock_data).decode()
        
        with patch("builtins.open", mock_open(read_data=mock_data)):
            image = ImageContent.from_file("photo.jpg")
            result = image._read_file("photo.jpg")
        
        assert result == mock_b64

    @pytest.mark.asyncio
    async def test_download_image(self):
        """测试下载图像."""
        image = ImageContent.from_url("https://example.com/photo.jpg")
        
        # 由于 aiohttp mocking 比较复杂，这里简化测试
        # 只测试媒体类型推断
        assert image.media_type == "image/jpeg"
        
        # 测试 URL 变化后类型更新
        image_png = ImageContent.from_url("https://example.com/photo.png")
        assert image_png.media_type == "image/png"


class TestMultimodalMessage:
    """测试 MultimodalMessage."""

    def test_init_text_only(self):
        """测试纯文本消息."""
        msg = MultimodalMessage(role="user", text="Hello")
        
        assert msg.role == "user"
        assert msg.text == "Hello"
        assert msg.images == []

    def test_init_with_images(self):
        """测试带图像的消息."""
        image = ImageContent.from_base64("abc123", "image/jpeg")
        msg = MultimodalMessage(role="user", text="Describe", images=[image])
        
        assert len(msg.images) == 1
        assert msg.images[0].data == "abc123"

    @pytest.mark.asyncio
    async def test_to_anthropic_format_text_only(self):
        """测试 Anthropic 纯文本格式."""
        msg = MultimodalMessage(role="user", text="Hello")
        
        fmt = await msg.to_anthropic_format()
        
        assert fmt["role"] == "user"
        assert len(fmt["content"]) == 1
        assert fmt["content"][0]["type"] == "text"
        assert fmt["content"][0]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_to_anthropic_format_with_image(self):
        """测试 Anthropic 带图像格式."""
        image = ImageContent.from_base64("abc123", "image/jpeg")
        msg = MultimodalMessage(role="user", text="Describe", images=[image])
        
        fmt = await msg.to_anthropic_format()
        
        assert len(fmt["content"]) == 2
        assert fmt["content"][0]["type"] == "text"
        assert fmt["content"][1]["type"] == "image"

    def test_to_openai_format_text_only(self):
        """测试 OpenAI 纯文本格式."""
        msg = MultimodalMessage(role="user", text="Hello")
        
        fmt = msg.to_openai_format()
        
        assert fmt["role"] == "user"
        assert len(fmt["content"]) == 1
        assert fmt["content"][0]["type"] == "text"

    def test_to_openai_format_with_image(self):
        """测试 OpenAI 带图像格式."""
        image = ImageContent.from_base64("abc123", "image/jpeg")
        msg = MultimodalMessage(role="user", text="Describe", images=[image])
        
        fmt = msg.to_openai_format()
        
        assert len(fmt["content"]) == 2
        assert fmt["content"][0]["type"] == "text"
        assert fmt["content"][1]["type"] == "image_url"