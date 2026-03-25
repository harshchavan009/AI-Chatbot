import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Application settings for the AI Chatbot.
    """
    APP_NAME: str = os.getenv("APP_NAME", "AI Chatbot")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-12345")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PORT: int = int(os.getenv("PORT", 8000))

    class Config:
        env_file = ".env"

settings = Settings()
