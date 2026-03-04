#!/usr/bin/env python3
"""快速测试 - 使用 Kimi 测试 Agent"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import ToolRegistry, calculator_tool, get_current_time_tool

async def main():
    print("=" * 60)
    print("AI-Toolbox 快速测试 - 丞相 Bot 启动前验证")
    print("=" * 60)
    
    # 使用 Kimi
    api_key = os.getenv("KIMI_API_KEY")
    if not api_key:
        print("❌ 错误: KIMI_API_KEY 未设置")
        return False
    
    print("\n[1/3] 创建 Kimi Provider...")
    provider = create_provider("kimi", api_key)
    print("✅ Provider 创建成功")
    
    print("\n[2/3] 注册工具...")
    registry = ToolRegistry()
    registry.register(calculator_tool)
    registry.register(get_current_time_tool)
    print(f"✅ 已注册 {len(registry)} 个工具")
    
    print("\n[3/3] 测试 Agent...")
    agent = Agent(provider, registry, max_iterations=3)
    
    # 简单测试
    print("\n🧮 测试: 计算 2 + 2")
    try:
        response = await agent.run("计算 2 + 2")
        print(f"✅ Agent 响应: {response[:100]}...")
        success = True
    except Exception as e:
        print(f"❌ 错误: {e}")
        success = False
    
    await provider.close()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！系统运行正常")
    else:
        print("❌ 测试失败")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)