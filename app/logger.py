import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add standard stdout logger (formatted & colored for console)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file handler for structured persistence (retains logs, rotates daily)
logger.add(
    "logs/elder_robot.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    backtrace=True,
    diagnose=True
)

__all__ = ["logger"]
