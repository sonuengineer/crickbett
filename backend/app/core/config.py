from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://cricket_arb:cricket_arb_secret@localhost:5433/cricket_arb"

    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"

    # JWT
    JWT_SECRET_KEY: str = "dev-cricket-arb-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cricket Arbitrage
    SCRAPE_INTERVAL_SECONDS: int = 30
    MATCH_DISCOVERY_INTERVAL_SECONDS: int = 300
    MIN_ARB_PROFIT_PCT: float = 0.5
    MAX_ODDS_AGE_SECONDS: int = 120
    PROXY_LIST: str = ""  # comma-separated proxy URLs
    BETFAIR_COMMISSION_PCT: float = 5.0
    DEFAULT_ARB_STAKE: float = 1000.0
    ODDS_CLEANUP_HOURS: int = 24

    # The Odds API (free tier: 500 requests/month)
    THE_ODDS_API_KEY: str = ""
    ODDS_API_REGIONS: str = "uk,eu,au"  # comma-separated: us,uk,eu,au

    # Data source mode: "api" (recommended), "playwright", "demo"
    DATA_SOURCE_MODE: str = "demo"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
