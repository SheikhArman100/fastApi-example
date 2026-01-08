from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    port:str

    # JWT Configuration
    access_token_secret: str
    refresh_token_secret: str
    forget_password_secret: str
    access_token_expire_time: str
    refresh_token_expire_time: str
    forget_password_expire_time: str
    client_url: str

    # Email/SMTP Configuration
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str

    class Config:
        env_file = ".env"

settings = Settings()
