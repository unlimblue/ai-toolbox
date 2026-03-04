#!/usr/bin/env python3
"""
综合示例 3: 自定义工具

展示如何创建自定义工具并集成到 Agent 中。
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from ai_toolbox import Agent, create_provider
from ai_toolbox.tools import Tool, ToolParameter, ToolRegistry
from ai_toolbox.tools.builtin import calculator_tool


# 自定义工具 1: 温度转换
async def convert_temperature(value: float, from_unit: str, to_unit: str) -> str:
    """转换温度单位.
    
    Args:
        value: 温度值
        from_unit: 源单位 (C, F, K)
        to_unit: 目标单位 (C, F, K)
    
    Returns:
        转换后的温度
    """
    from_unit = from_unit.upper()
    to_unit = to_unit.upper()
    
    # 先转为摄氏度
    if from_unit == "C":
        celsius = value
    elif from_unit == "F":
        celsius = (value - 32) * 5 / 9
    elif from_unit == "K":
        celsius = value - 273.15
    else:
        return f"不支持的单位: {from_unit}"
    
    # 再转为目标单位
    if to_unit == "C":
        result = celsius
    elif to_unit == "F":
        result = celsius * 9 / 5 + 32
    elif to_unit == "K":
        result = celsius + 273.15
    else:
        return f"不支持的单位: {to_unit}"
    
    return f"{value}°{from_unit} = {result:.2f}°{to_unit}"


# 自定义工具 2: 货币转换（模拟）
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """转换货币（使用模拟汇率）.
    
    Args:
        amount: 金额
        from_currency: 源货币 (USD, EUR, CNY, JPY)
        to_currency: 目标货币
    
    Returns:
        转换后的金额
    """
    # 模拟汇率（以 USD 为基准）
    rates = {
        "USD": 1.0,
        "EUR": 0.85,
        "CNY": 7.2,
        "JPY": 110.0,
    }
    
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    if from_currency not in rates:
        return f"不支持的货币: {from_currency}"
    if to_currency not in rates:
        return f"不支持的货币: {to_currency}"
    
    # 转换
    usd_amount = amount / rates[from_currency]
    result = usd_amount * rates[to_currency]
    
    return f"{amount} {from_currency} = {result:.2f} {to_currency}"


async def main():
    """主函数."""
    print("=" * 60)
    print("综合示例 3: 自定义工具")
    print("=" * 60)
    
    # 创建 Provider
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("错误: 请设置 OPENROUTER_API_KEY 环境变量")
        return
    
    provider = create_provider("openrouter", api_key)
    
    # 创建工具注册表
    print("\n[1/4] 创建自定义工具...")
    registry = ToolRegistry()
    
    # 注册内置工具
    registry.register(calculator_tool)
    
    # 注册自定义工具 1: 温度转换
    temp_tool = Tool(
        name="convert_temperature",
        description="转换温度单位（摄氏度C、华氏度F、开尔文K）",
        parameters=[
            ToolParameter("value", "number", "温度值", required=True),
            ToolParameter("from_unit", "string", "源单位 (C/F/K)", required=True),
            ToolParameter("to_unit", "string", "目标单位 (C/F/K)", required=True),
        ],
        function=convert_temperature
    )
    registry.register(temp_tool)
    
    # 注册自定义工具 2: 货币转换
    currency_tool = Tool(
        name="convert_currency",
        description="转换货币（USD/EUR/CNY/JPY）",
        parameters=[
            ToolParameter("amount", "number", "金额", required=True),
            ToolParameter("from_currency", "string", "源货币", required=True),
            ToolParameter("to_currency", "string", "目标货币", required=True),
        ],
        function=convert_currency
    )
    registry.register(currency_tool)
    
    print(f"✅ 已注册 {len(registry)} 个工具:")
    for name in registry.list_names():
        print(f"   - {name}")
    
    # 创建 Agent
    print("\n[2/4] 创建 Agent...")
    agent = Agent(provider, registry)
    
    # 测试自定义工具
    print("\n[3/4] 测试自定义工具...")
    print("-" * 60)
    
    # 测试温度转换
    print("\n🌡️  测试温度转换")
    print("用户: 将 100°F 转换为摄氏度")
    try:
        response = await agent.run("将 100°F 转换为摄氏度")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 测试货币转换
    print("\n💱 测试货币转换")
    print("用户: 100 USD 等于多少 CNY？")
    try:
        response = await agent.run("100 USD 等于多少 CNY？")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 组合使用
    print("\n🔢 组合使用")
    print("用户: 如果我有 100 USD，汇率是 7.2，计算我能得到多少 CNY，然后减去 10% 的手续费")
    try:
        response = await agent.run("如果我有 100 USD，汇率是 7.2，计算我能得到多少 CNY")
        print(f"Agent: {response}")
    except Exception as e:
        print(f"⚠️  错误: {e}")
    
    # 清理
    print("\n" + "=" * 60)
    await provider.close()
    print("✅ 完成!")
    print("\n💡 提示: 你可以根据需要创建任何自定义工具！")


if __name__ == "__main__":
    asyncio.run(main())