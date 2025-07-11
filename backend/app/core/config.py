from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 