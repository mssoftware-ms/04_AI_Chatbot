"""Application configuration and settings management."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
# Änderung durch KI
from pydantic import Field, field_validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with validation and type checking."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key")
    github_token: Optional[str] = Field(None, description="GitHub personal access token")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./chatbot.db",
        description="Database connection URL"
    )
    chroma_persist_directory: Path = Field(
        default=Path("./brain/chroma"),
        description="ChromaDB persistence directory"
    )
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=True, description="Enable auto-reload")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Application Settings
    app_name: str = Field(default="WhatsApp AI Chatbot", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    secret_key: str = Field(..., description="Secret key for JWT")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Token expiration time")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Max requests per period")
    rate_limit_period: int = Field(default=60, description="Rate limit period in seconds")
    
    # RAG Configuration
    embedding_model: str = Field(
        default="text-embedding-3-large",
        description="OpenAI embedding model"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI LLM model"
    )
    max_tokens: int = Field(default=2000, description="Max tokens for LLM response")
    temperature: float = Field(default=0.1, description="LLM temperature")
    chunk_size: int = Field(default=500, description="Text chunk size for splitting")
    chunk_overlap: int = Field(default=50, description="Overlap between chunks")
    top_k_results: int = Field(default=5, description="Number of retrieval results")
    
    # UI Configuration
    ui_port: int = Field(default=8550, description="Flet UI port")
    theme_mode: str = Field(default="light", description="UI theme mode")
    
    # File Watching
    watch_directories: List[str] = Field(
        default=["./documents"],
        description="Directories to watch for changes"
    )
    watch_file_types: List[str] = Field(
        default=[".py", ".md", ".txt", ".json", ".yaml", ".yml"],
        description="File types to watch"
    )
    watch_ignore_patterns: List[str] = Field(
        default=["__pycache__", "*.pyc", ".git", ".env"],
        description="Patterns to ignore"
    )
    
    # Voice Settings
    enable_voice: bool = Field(default=False, description="Enable voice mode")
    stt_model: str = Field(default="whisper-1", description="Speech-to-text model")
    tts_engine: str = Field(default="openai", description="Text-to-speech engine")
    tts_voice: str = Field(default="onyx", description="TTS voice selection")
    wake_word: str = Field(default="assistant", description="Wake word for activation")
    barge_in_enabled: bool = Field(default=True, description="Enable barge-in")
    vad_threshold: float = Field(default=0.5, description="Voice activity detection threshold")
    
    # Änderung durch KI
    @field_validator("chroma_persist_directory", mode="before")
    @classmethod
    def create_chroma_directory(cls, v):
        """Ensure ChromaDB directory exists."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @field_validator("watch_directories", mode="before")
    @classmethod
    def parse_watch_directories(cls, v):
        """Parse watch directories from string or list."""
        if isinstance(v, str):
            return [d.strip() for d in v.split(",")]
        return v
    
    @field_validator("watch_file_types", mode="before")
    @classmethod
    def parse_watch_file_types(cls, v):
        """Parse file types from string or list."""
        if isinstance(v, str):
            return [t.strip() for t in v.split(",")]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()
    
    @property
    def database_file_path(self) -> Path:
        """Get database file path from URL."""
        if self.database_url.startswith("sqlite"):
            db_path = self.database_url.split("///")[-1]
            return Path(db_path)
        return None
    
    def get_watch_patterns(self) -> List[str]:
        """Get file patterns for watching."""
        return [f"**/*{ext}" for ext in self.watch_file_types]


# Global settings instance
settings = Settings()