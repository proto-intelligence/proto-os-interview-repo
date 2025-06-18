# app/core/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "FastAPI App"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Environment
    ENVIRONMENT: str = "local"
    
    # Database
    DATABASE_URL: str | None = None
    
    # Security
    SECRET_KEY: str | None = None

    # Integrations
    GOOGLE_CALENDAR_API_URL: str | None = None

    # Logging
    LOGS_FILE_NAME: str = "app.log"
    LOGS_FILE_ROTATION: str = "600 MB"
    LOGS_FILE_SERIALIZE: bool = False
    LOGS_LEVEL: str = "DEBUG"
    ENABLE_LOGGING_FILE: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
