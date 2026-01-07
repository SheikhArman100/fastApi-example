from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    port:str

    # JWT Configuration
    access_token_secret: str
    refresh_token_secret: str
    access_token_expire_time: str 
    refresh_token_expire_time: str 

    class Config:
        env_file = ".env"

settings = Settings()
