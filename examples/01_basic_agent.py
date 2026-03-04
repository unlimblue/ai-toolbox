#!/usr/bin/env python3
"""
综合示例 1: 基础 Agent 组装

展示如何使用 ai-toolbox 组装一个基础 Agent，
包含 Provider、Tools 和 Agent 的完整流程。
"""

import asyncio
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import (
    ToolRegistry,
    calculator_tool,
    get_current_time_tool,
    WebSearchTool,
)


async def main():
    """主函数."""
    print("=" * 60)
    print("综合示例 1: 基础 Agent 组装")
    print("=" * 60)
    
    # 1. 创建 Provider
    print("\n[1/4] 创建 AI Provider...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("错误: 请设置 OPENROUTER_API_KEY 环境变量")
        return
    
    provider = create_provider("openrouter", api_key)
    print(f"✅ Provider 创建成功: {provider.__class__.__name__}")
    
    # 2. 创建工具注册表
    print("\n[2/4] 创建工具注册表...")
    registry = ToolRegistry()
    
    # 注册工具
    registry.register(calculator_tool)
    registry.register(get_current_time_tool)
    registry.register(WebSearchTool())
    
    print(f"✅ 已注册 {len(registry)} 个工具:")
    for name in registry.list_names():
        print(f"   - {name}")
    
    # 3. 创建 Agent
    print("\n[3/4] 创建 Agent...")
    agent = Agent(
        provider=provider,
        tools=registry,
        max_iterations=3,
    )
    print("✅ Agent 创建成功")
    
    # 4. 运行 Agent
    print("\n[4/4] 运行 Agent...")
    print("-" * 60)
    
    # 测试 1: 数学计算
    print("\n🧮 测试 1: 数学计算")
    print("用户: 计算 123 * 456")
    response = await agent.run("计算 123 * 456")
    print(f"Agent: {response}")
    
    # 测试 2: 获取时间
    print("\n🕐 测试 2: 获取时间")
    print("用户: 现在几点")
    response = await agent.run("现在几点")
    print(f"Agent: {response}")
    
    # 测试 3: 搜索（需要网络）
    print("\n🔍 测试 3: 网络搜索")
    print("用户: 搜索 Python 3.12 新特性")
    try:
        response = await agent.run("搜索 Python 3.12 新特性")
        print(f"Agent: {response[:500]}...")  # 截断长输出
    except Exception as e:
        print(f"⚠️  搜索失败 (可能需要网络): {e}")
    
    # 清理
    print("\n" + "=" * 60)
    print("清理资源...")
    await provider.close()
    print("✅ 完成!")


if __name__ == "__main__":
    asyncio.run(main())