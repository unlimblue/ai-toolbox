#!/usr/bin/env python3
"""
综合示例 4: 视觉/多模态 Agent

展示如何使用视觉能力进行图像分析。
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from ai_toolbox.providers import KimiClient, ImageContent


async def main():
    """主函数."""
    print("=" * 60)
    print("综合示例 4: 视觉/多模态 Agent")
    print("=" * 60)
    
    # 检查 API Key
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("错误: 请设置 KIMI_API_KEY 环境变量")
        return
    
    # 创建 Kimi 客户端
    print("\n[1/4] 创建 Kimi 客户端...")
    client = KimiClient(api_key)
    print("✅ 客户端创建成功")
    
    # 演示各种图像来源
    print("\n[2/4] 图像来源示例...")
    
    # 示例 1: 从文件
    print("\n📁 方式 1: 从本地文件")
    print("image = ImageContent.from_file('photo.jpg')")
    # 实际使用时取消注释:
    # if os.path.exists("photo.jpg"):
    #     image = ImageContent.from_file("photo.jpg")
    #     response = await client.chat_with_image("描述这张图片", [image])
    #     print(f"分析结果: {response.content}")
    
    # 示例 2: 从 URL
    print("\n🌐 方式 2: 从 URL")
    print("image = ImageContent.from_url('https://example.com/photo.jpg')")
    
    # 示例 3: 从 Base64
    print("\n🔢 方式 3: 从 Base64")
    print("image = ImageContent.from_base64('iVBORw0KGgo...', 'image/png')")
    
    # 实际测试（使用示例 URL）
    print("\n[3/4] 实际测试（需要网络）...")
    print("-" * 60)
    
    # 使用示例图片 URL（Unsplash 的公开图片）
    test_url = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800"
    
    print(f"\n🖼️  测试图像分析")
    print(f"图像 URL: {test_url}")
    print("提示: 描述这张图片")
    
    try:
        image = ImageContent.from_url(test_url)
        print("⏳ 正在分析...")
        
        response = await client.chat_with_image(
            "描述这张图片，包括场景、物体、颜色等",
            [image]
        )
        
        print(f"\n📝 分析结果:")
        print(response.content)
        
    except Exception as e:
        print(f"⚠️  错误: {e}")
        print("提示: 可能需要有效的 API Key 和网络连接")
    
    # 多图像分析
    print("\n" + "-" * 60)
    print("\n🖼️🖼️  多图像分析示例")
    print("可以同时传入多张图片进行对比分析")
    print("images = [ImageContent.from_url(url1), ImageContent.from_url(url2)]")
    print("response = await client.chat_with_image('比较这两张图片', images)")
    
    # 清理
    print("\n" + "=" * 60)
    print("[4/4] 清理资源...")
    await client.close()
    print("✅ 完成!")
    
    print("\n💡 使用建议:")
    print("   - 支持格式: JPEG, PNG, GIF, WebP")
    print("   - 最大文件大小: 20MB")
    print("   - 可以组合多张图片进行分析")
    print("   - 适合 OCR、物体识别、场景描述等任务")


if __name__ == "__main__":
    asyncio.run(main())