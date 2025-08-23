"""
Application configuration management.

This module handles all application settings, environment variables,
and configuration validation.
"""

import os
import secrets
import warnings
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


def generate_secure_secret_key() -> str:
    """
    Generate a secure secret key for production use.
    
    Returns:
        str: A cryptographically secure random string
    """
    return secrets.token_urlsafe(32)


def get_default_secret_key() -> str:
    """
    Get default secret key with production warning.
    
    Returns:
        str: Secret key from environment or generated secure key
    """
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        secret_key = generate_secure_secret_key()
        warnings.warn(
            "SECRET_KEY not found in environment variables. "
            "Using auto-generated key. For production, set SECRET_KEY "
            "environment variable to a secure value.",
            UserWarning,
            stacklevel=2
        )
    return secret_key


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Configuration
    app_name: str = Field(default="WhatsApp AI Chatbot", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./data/chatbot.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Änderung durch KI - AI Service Configuration with validation
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    def validate_ai_keys(self):
        """Validate that at least one AI API key is provided."""
        if not self.openai_api_key and not self.anthropic_api_key:
            warnings.warn(
                "No AI API keys configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY "
                "environment variable to enable AI features.",
                UserWarning
            )
    default_ai_model: str = Field(default="gpt-3.5-turbo", env="DEFAULT_AI_MODEL")
    max_tokens: int = Field(default=2000, env="MAX_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Authentication & Security
    secret_key: str = Field(default_factory=get_default_secret_key, env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # File Upload Configuration
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_extensions: str = Field(
        default=".txt,.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif",
        env="ALLOWED_FILE_EXTENSIONS"
    )
    upload_dir: str = Field(default="./data/uploads", env="UPLOAD_DIR")
    
    # Project Management
    default_project_dir: str = Field(default="./data/projects", env="DEFAULT_PROJECT_DIR")
    max_projects_per_user: int = Field(default=10, env="MAX_PROJECTS_PER_USER")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: str = Field(default="./logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10485760, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Vector Database Configuration
    chroma_persist_directory: str = Field(default="./data/chroma", env="CHROMA_PERSIST_DIRECTORY")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # CORS Configuration
    # Änderung durch KI
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="CORS allowed origins"
    )
    # Änderung durch KI - Fixed CORS credentials parsing
    cors_credentials: bool = Field(default=True, description="CORS allow credentials")
    # Änderung durch KI
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="CORS allowed methods"
    )
    cors_headers: List[str] = Field(
        default=["Content-Type", "Authorization"],
        description="CORS allowed headers"
    )
    
    # WebSocket Configuration
    ws_max_connections: int = Field(default=100, env="WS_MAX_CONNECTIONS")
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # Feature Flags
    enable_ai_chat: bool = Field(default=True, env="ENABLE_AI_CHAT")
    enable_project_management: bool = Field(default=True, env="ENABLE_PROJECT_MANAGEMENT")
    enable_file_upload: bool = Field(default=True, env="ENABLE_FILE_UPLOAD")
    enable_voice_messages: bool = Field(default=False, env="ENABLE_VOICE_MESSAGES")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    
    @field_validator("allowed_file_extensions")
    @classmethod
    def parse_file_extensions(cls, v):
        """Parse comma-separated file extensions into a list."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v
    
    # Änderung durch KI - Improved CORS parsing with better error handling
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if v is None:
            return ["http://localhost:3000", "http://localhost:8501"]
        if isinstance(v, str):
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:8501"]
            if v.startswith('[') and v.endswith(']'):
                # Handle JSON-like format: ["url1","url2"]
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    # Fallback to treating as literal string
                    return [v.strip()]
            # Handle comma-separated format: url1,url2
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return [str(v)] if v else ["http://localhost:3000", "http://localhost:8501"]
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.upload_dir,
            self.default_project_dir,
            self.chroma_persist_directory,
            Path(self.log_file).parent,
            Path(self.database_url.replace("sqlite:///", "")).parent,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_parse_none_str": "none",
        "extra": "ignore"
    }


# Änderung durch KI - Global settings instance with validation
settings = Settings()

# Ensure required directories exist
settings.create_directories()

# Validate configuration
settings.validate_ai_keys()