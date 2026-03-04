"""Discord Bot 模块 - 独立的 Discord 机器人实现.

此模块独立于 providers 和 API 模块，仅复用核心配置和工具。
可通过 `import` 使用，也可作为独立服务运行。
"""

from .bot import AIToolboxBot

__all__ = ["AIToolboxBot"]