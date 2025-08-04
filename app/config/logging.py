"""Logging configuration."""
import logging
import sys
from pathlib import Path
from app.config.settings import settings

# Create logs directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Configure logging for the application.
    
    Sets up:
    1. Console logging (for development)
    2. File logging (for production)
    3. Different levels based on environment
    """
    
    # Set log level based on environment
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(LOG_DIR / "xonebot.log")
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DB_ECHO else logging.WARNING
    )
    
    return logger


# Create logger instance
logger = setup_logging()