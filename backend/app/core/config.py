from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Agent WAF"
    
    # Base directory is d:\Projects\Aivar\agent-waf\backend
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SAMPLE_DATA_DIR: Path = BASE_DIR / "sample_data"
    
    # Policy / WAF Configurations
    SHADOW_MODE: bool = False
    DATABASE_PATH: str = "agent_waf.db"
    
    # Groq configurations
    GROQ_API_KEY: Optional[str] = None
    MODEL_NAME: str = "llama-3.3-70b-versatile"

settings = Settings()
