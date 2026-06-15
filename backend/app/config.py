from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://hedge:hedge@localhost:5432/hedge"
    DATABASE_URL_SYNC: str = "postgresql://hedge:hedge@localhost:5432/hedge"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Debug
    DEBUG: bool = False

    # Polygon.io
    POLYGON_API_KEY: str = ""

    # Interactive Brokers
    IBKR_HOST: str = "127.0.0.1"
    IBKR_PORT: int = 7497
    IBKR_CLIENT_ID: int = 1

    # Default symbols to track
    DEFAULT_SYMBOLS: list[str] = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "META", "GOOGL", "VIX"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
