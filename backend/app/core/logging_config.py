"""
Logging setup using loguru. Call configure_logging() once at startup.
"""
import os
import sys

from loguru import logger

from app.core.config import settings


def configure_logging() -> None:
    logger.remove()  # remove default handler

    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

    # Console handler -- human readable, colorized
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File handler -- rotated, retained, compressed
    logger.add(
        settings.LOG_FILE,
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


__all__ = ["logger", "configure_logging"]
