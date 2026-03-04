"""日志配置."""

import logging
import sys
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """获取配置好的日志记录器."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger