from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    
    postgres_url: str = os.getenv("POSTGRES_URL", "postgresql://ai:aishop123@postgres:5432/ai_shop")
    mysql_url: str = os.getenv("MYSQL_URL", "mysql+pymysql://ai:aishop123@mysql:3306/ai_orders")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()