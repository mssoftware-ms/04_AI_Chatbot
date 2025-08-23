"""
Logging configuration for the application.

This module sets up structured logging with proper formatting,
file rotation, and different log levels for development and production.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

# Änderung durch KI
# Import only available dependencies
try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False

try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    colorlog = None
    HAS_COLORLOG = False

# Import appropriate settings module
try:
    from config.config import settings
except ImportError:
    from config.settings import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Set up application logging with both standard and structured logging.
    
    Args:
        log_level: Override the default log level from settings
    """
    # Use provided log level or fall back to settings
    level = log_level or settings.log_level
    log_level_num = getattr(logging, level.upper(), logging.INFO)
    
    # Ensure log directory exists
    log_file_path = Path(settings.log_file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers
    logging.getLogger().handlers.clear()
    
    # Configure root logger
    logging.basicConfig(
        level=log_level_num,
        format=settings.log_format,
        handlers=[]
    )
    
    # Änderung durch KI - Console handler with colors for development (optional dependency)
    debug_mode = getattr(settings, 'debug', False)
    if debug_mode and HAS_COLORLOG:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        )
        console_handler.setLevel(log_level_num)
        logging.getLogger().addHandler(console_handler)
    else:
        # Fallback to standard console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        console_handler.setLevel(log_level_num)
        logging.getLogger().addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(
        logging.Formatter(
            settings.log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    file_handler.setLevel(log_level_num)
    logging.getLogger().addHandler(file_handler)
    
    # Änderung durch KI - Configure structured logging with structlog (optional dependency)
    if HAS_STRUCTLOG:
        debug_mode = getattr(settings, 'debug', False)
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if not debug_mode else structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    # Set specific log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log the logging setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}, File: {settings.log_file}")


# Änderung durch KI
def get_logger(name: str):
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structlog logger if available, standard logger otherwise
    """
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


# Änderung durch KI
class LoggerMixin:
    """Mixin class to add logging capability to other classes."""
    
    @property
    def logger(self):
        """Get a logger instance for this class."""
        return get_logger(self.__class__.__name__)


# Create application-wide logger instances
app_logger = get_logger("app")
api_logger = get_logger("api")
database_logger = get_logger("database")
ai_logger = get_logger("ai")
auth_logger = get_logger("auth")