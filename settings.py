import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    CRM_BASE_URL: str = os.getenv("CRM_BASE_URL", "http://localhost:8001")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_TRANSCRIPT_LENGTH: int = 1000
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    USE_AI_NLU: bool = os.getenv("USE_AI_NLU", "false").lower() == "true"

settings = Settings()
