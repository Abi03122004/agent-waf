from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Agent WAF"
    
    # Base directory is backend root
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SAMPLE_DATA_DIR: Path = BASE_DIR / "sample_data"
    
    # Policy / WAF Configurations
    SHADOW_MODE: bool = False
    DATABASE_PATH: str = "agent_waf.db"
    
    # Groq configurations
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    MODEL_NAME: str = "llama-3.3-70b-versatile"
    
    # CORS Configurations
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # API Rate Limiting (per IP)
    API_RATE_LIMIT_ENABLED: bool = True
    API_RATE_LIMIT_MAX: int = 60
    API_RATE_LIMIT_WINDOW: int = 60

settings = Settings()

