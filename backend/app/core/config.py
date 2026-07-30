from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Agent WAF"
    
    # Base directory is d:\Projects\Aivar\agent-waf\backend
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    SAMPLE_DATA_DIR: Path = BASE_DIR / "sample_data"
    
    # Policy / WAF Configurations
    SHADOW_MODE: bool = False
    DATABASE_PATH: str = "agent_waf.db"

    class Config:
        env_file = ".env"

settings = Settings()
