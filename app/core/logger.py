import sys
from pathlib import Path

from loguru import logger

# 确保 logs 目录存在
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "server.log"


def setup_logger():
    """
    配置 Loguru 日志系统。
    
    配置项：
    - 输出到 logs/server.log
    - Rotation: 每天 00:00 轮转，或文件大小超过 100MB 时轮转
    - Retention: 保留最近 7 天的日志
    - Format: 包含时间、级别、模块名和具体的 Message
    """
    # 移除默认的 handler
    logger.remove()
    
    # 添加控制台输出（开发环境）
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    
    # 添加文件输出（生产环境）
    # rotation 参数：文件大小超过 100MB 时轮转，或每天 00:00 轮转（loguru 会自动处理时间轮转）
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",  # 文件日志记录更详细的信息
        rotation="100 MB",  # 文件大小超过 100MB 时轮转
        retention="7 days",  # 保留最近 7 天的日志
        compression="zip",  # 压缩旧日志文件
        encoding="utf-8",
        enqueue=True,  # 异步写入，提高性能
    )
    
    logger.info("✅ Loguru 日志系统已初始化")
    logger.info(f"📁 日志文件路径: {LOG_FILE.absolute()}")
    
    return logger


# 导出配置好的 logger 实例
__all__ = ["logger", "setup_logger"]
