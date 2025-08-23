"""Logging configuration for the application."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    
    # Create logs directory if needed
    if log_file:
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
    
    # Logging configuration dictionary
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            # JSON formatter removed - optional dependency
            # To enable JSON logging, install: pip install python-json-logger
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "default",
                "stream": sys.stdout
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "chromadb": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "openai": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "httpcore": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    # Add file handler if log file is specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }
        config["root"]["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Logging to file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Custom log levels for application-specific events
def add_custom_log_levels():
    """Add custom log levels for application-specific events."""
    
    # RAG-specific log level
    RAG_LEVEL = 25  # Between INFO (20) and WARNING (30)
    logging.addLevelName(RAG_LEVEL, "RAG")
    
    def rag(self, message, *args, **kwargs):
        if self.isEnabledFor(RAG_LEVEL):
            self._log(RAG_LEVEL, message, args, **kwargs)
    
    logging.Logger.rag = rag
    
    # Voice-specific log level
    VOICE_LEVEL = 26
    logging.addLevelName(VOICE_LEVEL, "VOICE")
    
    def voice(self, message, *args, **kwargs):
        if self.isEnabledFor(VOICE_LEVEL):
            self._log(VOICE_LEVEL, message, args, **kwargs)
    
    logging.Logger.voice = voice


# Initialize custom log levels
add_custom_log_levels()