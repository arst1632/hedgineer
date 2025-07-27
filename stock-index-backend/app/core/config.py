from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "stocks.db")
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    CACHE_TTL: int = 3600  # 1 hour
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Stock Index Tracker"
    
    # Data source
    DATA_SOURCE: str = "yahoo"  # yahoo, alphavantage
    ALPHA_VANTAGE_API_KEY: Optional[str] = '6PJVILAR0HQRSNRL'
    
    class Config:
        env_file = ".env"

settings = Settings()
