#!/usr/bin/env python3
"""
综合示例 2: 多工具组合 Agent

展示如何组合多个工具，让 Agent 完成复杂任务。
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import (
    ToolRegistry,
    calculator_tool,
    get_current_time_tool,
    random_number_tool,
    count_words_tool,
    WebSearchTool,
    WebSearchNewsTool,
)


async def main():
    """主函数."""
    print("=" * 60)
    print("综合示例 2: 多工具组合 Agent")
    print("=" * 60)
    
    # 创建 Provider
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("错误: 请设置 OPENROUTER_API_KEY 环境变量")
        return
    
    provider = create_provider("openrouter", api_key)
    
    # 创建工具注册表（注册所有工具）
    print("\n[1/3] 注册所有工具...")
    registry = ToolRegistry()
    
    # 基础工具
    registry.register(calculator_tool)
    registry.register(get_current_time_tool)
    registry.register(random_number_tool)
    registry.register(count_words_tool)
    
    # 搜索工具
    registry.register(WebSearchTool())
    registry.register(WebSearchNewsTool())
    
    print(f"✅ 已注册 {len(registry)} 个工具")
    
    # 创建 Agent
    print("\n[2/3] 创建 Agent...")
    agent = Agent(provider, registry, max_iterations=5)
    
    # 测试场景
    print("\n[3/3] 运行测试场景...")
    print("-" * 60)
    
    # 场景 1: 计算 + 时间
    print("\n📊 场景 1: 计算当前小时数的平方")
    print("用户: 现在的小时数是多少？计算它的平方。")
    try:
        response = await agent.run("现在的小时数是多少？计算它的平方。")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 场景 2: 随机 + 计算
    print("\n🎲 场景 2: 随机数计算")
    print("用户: 生成一个 1-100 的随机数，然后计算它乘以 2 的结果")
    try:
        response = await agent.run("生成一个 1-100 的随机数，然后计算它乘以 2 的结果")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 场景 3: 搜索 + 统计
    print("\n🔍 场景 3: 搜索并统计字数")
    print("用户: 搜索 'Python'，统计第一条结果的标题有多少个中文字符")
    try:
        response = await agent.run("搜索 'Python'，统计第一条结果的标题有多少个字符")
        print(f"Agent: {response[:500]}...")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 清理
    print("\n" + "=" * 60)
    await provider.close()
    print("✅ 完成!")


if __name__ == "__main__":
    asyncio.run(main())