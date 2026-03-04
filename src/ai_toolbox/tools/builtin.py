"""内置工具集."""

import asyncio
import json
import math
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Tool, ToolParameter


def calculator(expression: str, precision: int = 10) -> str:
    """计算数学表达式.
    
    支持基本数学运算、常用函数。
    
    Args:
        expression: 数学表达式，如 "2 + 2"、"sqrt(16)"、"sin(pi/2)"
        precision: 结果精度（小数位数）
    
    Returns:
        计算结果
    
    示例:
        >>> calculator("2 + 2")
        '4'
        >>> calculator("sqrt(16)")
        '4.0'
        >>> calculator("2 ** 10")
        '1024'
    """
    # 安全计算环境
    safe_dict = {
        # 数学函数
        "abs": abs,
        "round": round,
        "max": max,
        "min": min,
        "sum": sum,
        # 数学常数
        "pi": math.pi,
        "e": math.e,
        # 数学运算
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "pow": pow,
        # 其他
        "floor": math.floor,
        "ceil": math.ceil,
        "factorial": math.factorial,
        "gcd": math.gcd,
        "degrees": math.degrees,
        "radians": math.radians,
    }
    
    try:
        # 预处理表达式
        expr = expression.strip()
        
        # 检查危险字符
        dangerous = ["__", "import", "eval", "exec", "compile", "open", "file"]
        for d in dangerous:
            if d in expr.lower():
                return f"错误: 表达式包含不允许的内容 '{d}'"
        
        # 计算
        result = eval(expr, {"__builtins__": {}}, safe_dict)
        
        # 格式化结果
        if isinstance(result, float):
            # 去掉末尾的0
            result = round(result, precision)
            if result == int(result):
                return str(int(result))
        
        return str(result)
        
    except ZeroDivisionError:
        return "错误: 除零错误"
    except Exception as e:
        return f"计算错误: {str(e)}"


def get_current_time(timezone: str = "UTC", format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间.
    
    Args:
        timezone: 时区，如 "UTC"、"Asia/Shanghai"、"America/New_York"
        format: 时间格式
    
    Returns:
        格式化的时间字符串
    
    示例:
        >>> get_current_time()
        '2024-01-15 10:30:00'
        >>> get_current_time("Asia/Shanghai")
        '2024-01-15 18:30:00'
    """
    try:
        from zoneinfo import ZoneInfo
        
        tz = ZoneInfo(timezone)
        now = datetime.now(tz)
        return now.strftime(format)
    except Exception as e:
        return f"错误: {str(e)}"


def random_number(min: int = 0, max: int = 100) -> str:
    """生成随机数.
    
    Args:
        min: 最小值（包含）
        max: 最大值（包含）
    
    Returns:
        随机整数
    
    示例:
        >>> random_number(1, 6)  # 模拟骰子
        '4'
    """
    return str(random.randint(min, max))


def random_choice(options: str) -> str:
    """从选项中随机选择.
    
    Args:
        options: 逗号分隔的选项，如 "A,B,C" 或 "选项1, 选项2, 选项3"
    
    Returns:
        随机选择的选项
    
    示例:
        >>> random_choice("吃饭,睡觉,打代码")
        '睡觉'
    """
    try:
        # 解析选项
        items = [item.strip() for item in options.split(",")]
        items = [item for item in items if item]  # 去掉空项
        
        if not items:
            return "错误: 选项不能为空"
        
        return random.choice(items)
    except Exception as e:
        return f"错误: {str(e)}"


def count_words(text: str) -> str:
    """统计文本字数.
    
    Args:
        text: 要统计的文本
    
    Returns:
        字数统计信息
    """
    # 中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 英文单词
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 数字
    numbers = len(re.findall(r'\d+', text))
    # 总字符数（不含空白）
    total_chars = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    
    return json.dumps({
        "chinese_characters": chinese_chars,
        "english_words": english_words,
        "numbers": numbers,
        "total_characters": total_chars
    }, ensure_ascii=False)


def format_json(data: str, indent: int = 2) -> str:
    """格式化 JSON 字符串.
    
    Args:
        data: JSON 字符串
        indent: 缩进空格数
    
    Returns:
        格式化后的 JSON
    """
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"JSON 解析错误: {str(e)}"
    except Exception as e:
        return f"错误: {str(e)}"


async def read_file(file_path: str, max_lines: int = 100) -> str:
    """读取文件内容（沙箱安全）.
    
    只能读取 workspace 目录内的文件。
    
    Args:
        file_path: 文件路径（相对或绝对）
        max_lines: 最大读取行数
    
    Returns:
        文件内容
    """
    try:
        # 获取 workspace 路径
        workspace = Path(os.getenv("AI_TOOLBOX_WORKSPACE", "/root/.openclaw/workspace"))
        
        # 解析路径
        path = Path(file_path).expanduser().resolve()
        
        # 安全检查：必须在 workspace 内
        if not str(path).startswith(str(workspace)):
            return f"错误: 只能访问 workspace 目录内的文件"
        
        if not path.exists():
            return f"错误: 文件不存在: {file_path}"
        
        if not path.is_file():
            return f"错误: 不是文件: {file_path}"
        
        # 读取文件
        content = path.read_text(encoding="utf-8")
        
        # 限制行数
        lines = content.split("\n")
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append(f"\n... (已截断，共 {len(content.split(chr(10)))} 行)")
        
        return "\n".join(lines)
        
    except Exception as e:
        return f"读取错误: {str(e)}"


async def list_directory(directory: str = ".") -> str:
    """列出目录内容（沙箱安全）.
    
    只能列出 workspace 目录内的目录。
    
    Args:
        directory: 目录路径
    
    Returns:
        目录内容列表
    """
    try:
        # 获取 workspace 路径
        workspace = Path(os.getenv("AI_TOOLBOX_WORKSPACE", "/root/.openclaw/workspace"))
        
        # 解析路径
        path = Path(directory).expanduser().resolve()
        
        # 安全检查
        if not str(path).startswith(str(workspace)):
            return "错误: 只能访问 workspace 目录"
        
        if not path.exists():
            return f"错误: 目录不存在: {directory}"
        
        if not path.is_dir():
            return f"错误: 不是目录: {directory}"
        
        # 列出内容
        items = []
        for item in sorted(path.iterdir()):
            item_type = "📁" if item.is_dir() else "📄"
            size = ""
            if item.is_file():
                size_bytes = item.stat().st_size
                if size_bytes < 1024:
                    size = f" ({size_bytes} B)"
                elif size_bytes < 1024 * 1024:
                    size = f" ({size_bytes / 1024:.1f} KB)"
                else:
                    size = f" ({size_bytes / (1024 * 1024):.1f} MB)"
            
            items.append(f"{item_type} {item.name}{size}")
        
        if not items:
            return "目录为空"
        
        return "\n".join(items)
        
    except Exception as e:
        return f"错误: {str(e)}"


# 创建 Tool 实例
calculator_tool = Tool.from_function(
    calculator,
    description="计算数学表达式，支持基本运算、常用函数如 sqrt、sin、cos 等"
)

get_current_time_tool = Tool.from_function(
    get_current_time,
    description="获取当前时间，支持指定时区和格式"
)

random_number_tool = Tool.from_function(
    random_number,
    description="生成指定范围内的随机整数"
)

random_choice_tool = Tool.from_function(
    random_choice,
    description="从逗号分隔的选项中随机选择一个"
)

count_words_tool = Tool.from_function(
    count_words,
    description="统计文本中的中文字符、英文单词和数字数量"
)

format_json_tool = Tool.from_function(
    format_json,
    description="格式化 JSON 字符串，使其更易读"
)

# 异步工具需要手动创建
read_file_tool = Tool(
    name="read_file",
    description="读取文件内容（只能访问 workspace 目录内的文件）",
    parameters=[
        ToolParameter("file_path", "string", "文件路径", required=True),
        ToolParameter("max_lines", "number", "最大读取行数", required=False, default=100)
    ],
    function=read_file
)

list_directory_tool = Tool(
    name="list_directory",
    description="列出目录内容（只能访问 workspace 目录）",
    parameters=[
        ToolParameter("directory", "string", "目录路径", required=False, default=".")
    ],
    function=list_directory
)