from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://hedge:hedge@localhost:5432/hedge"
    DATABASE_URL_SYNC: str = "postgresql://hedge:hedge@localhost:5432/hedge"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
