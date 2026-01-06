from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    secret_key: str

    # JWT Configuration
    access_token_secret: str
    refresh_token_secret: str
    access_token_expire_time: str = "15m"  # Default 15 minutes
    refresh_token_expire_time: str = "7d"  # Default 7 days

    class Config:
        env_file = ".env"

settings = Settings()
