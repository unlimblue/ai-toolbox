"""视觉/多模态能力支持.

为 Providers 添加图像理解能力.
"""

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import aiohttp


@dataclass
class ImageContent:
    """图像内容.
    
    支持多种图像来源：URL、本地文件、Base64.
    
    示例:
        # 从 URL
        image = ImageContent.from_url("https://example.com/photo.jpg")
        
        # 从本地文件
        image = ImageContent.from_file("/path/to/photo.jpg")
        
        # 从 Base64
        image = ImageContent.from_base64("iVBORw0KGgo...", "image/png")
    """
    source_type: Literal["url", "base64", "file"]
    data: str  # URL、base64 字符串或文件路径
    media_type: str = "image/jpeg"  # image/jpeg, image/png, image/gif, image/webp
    
    @classmethod
    def from_url(cls, url: str) -> "ImageContent":
        """从 URL 创建.
        
        Args:
            url: 图像 URL
        
        Returns:
            ImageContent 实例
        """
        # 尝试从 URL 推断媒体类型
        media_type = "image/jpeg"  # 默认
        if url.endswith(".png"):
            media_type = "image/png"
        elif url.endswith(".gif"):
            media_type = "image/gif"
        elif url.endswith(".webp"):
            media_type = "image/webp"
        
        return cls(source_type="url", data=url, media_type=media_type)
    
    @classmethod
    def from_file(cls, file_path: str | Path) -> "ImageContent":
        """从本地文件创建.
        
        Args:
            file_path: 图像文件路径
        
        Returns:
            ImageContent 实例
        """
        path = Path(file_path)
        
        # 推断媒体类型
        suffix = path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")
        
        return cls(source_type="file", data=str(path), media_type=media_type)
    
    @classmethod
    def from_base64(cls, base64_data: str, media_type: str = "image/jpeg") -> "ImageContent":
        """从 Base64 创建.
        
        Args:
            base64_data: Base64 编码的图像数据
            media_type: 媒体类型
        
        Returns:
            ImageContent 实例
        """
        return cls(source_type="base64", data=base64_data, media_type=media_type)
    
    async def to_anthropic_format(self) -> dict:
        """转换为 Anthropic 格式.
        
        Returns:
            Anthropic API 格式的图像内容
        """
        if self.source_type == "url":
            # Anthropic 不直接支持 URL，需要下载
            base64_data = await self._download_image(self.data)
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": base64_data,
                }
            }
        elif self.source_type == "file":
            base64_data = self._read_file(self.data)
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": base64_data,
                }
            }
        elif self.source_type == "base64":
            return {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": self.media_type,
                    "data": self.data,
                }
            }
    
    def to_openai_format(self) -> dict:
        """转换为 OpenAI 格式.
        
        Returns:
            OpenAI API 格式的图像内容
        """
        if self.source_type == "url":
            return {
                "type": "image_url",
                "image_url": {"url": self.data}
            }
        elif self.source_type == "file":
            base64_data = self._read_file(self.data)
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.media_type};base64,{base64_data}"
                }
            }
        elif self.source_type == "base64":
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{self.media_type};base64,{self.data}"
                }
            }
    
    def _read_file(self, file_path: str) -> str:
        """读取文件并转为 Base64."""
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def _download_image(self, url: str) -> str:
        """下载图像并转为 Base64."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.read()
                # 更新媒体类型
                content_type = resp.headers.get("content-type", "image/jpeg")
                if content_type.startswith("image/"):
                    self.media_type = content_type
                return base64.b64encode(data).decode("utf-8")


class MultimodalMessage:
    """多模态消息.
    
    支持文本 + 图像混合内容.
    
    示例:
        message = MultimodalMessage(
            role="user",
            text="描述这张图片",
            images=[ImageContent.from_file("photo.jpg")]
        )
    """
    
    def __init__(
        self,
        role: str,
        text: str | None = None,
        images: list[ImageContent] | None = None
    ):
        """初始化多模态消息.
        
        Args:
            role: 消息角色 (user, assistant)
            text: 文本内容
            images: 图像内容列表
        """
        self.role = role
        self.text = text
        self.images = images or []
    
    async def to_anthropic_format(self) -> dict:
        """转换为 Anthropic 格式."""
        content = []
        
        if self.text:
            content.append({"type": "text", "text": self.text})
        
        for image in self.images:
            content.append(await image.to_anthropic_format())
        
        return {
            "role": self.role,
            "content": content
        }
    
    def to_openai_format(self) -> dict:
        """转换为 OpenAI 格式."""
        content = []
        
        if self.text:
            content.append({"type": "text", "text": self.text})
        
        for image in self.images:
            content.append(image.to_openai_format())
        
        return {
            "role": self.role,
            "content": content
        }