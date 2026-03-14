"""
Central settings loader.
Reads from .env file automatically.
Import `settings` anywhere in the project to access config values.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8000
    whisper_model: str = "base"
    database_path: str = "data/ecommerce.db"
    log_level: str = "info"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
