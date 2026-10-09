from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str
    SECRET_KEY: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    ALGORITHM: str
    TOKEN_EXPIRE_IN_MINUTES: int
    GEMINI_API_KEY: str
    GEMINI_MODEL: str
    TEST_DATABASE_URL: Optional[str] = None
    CHROMA_DISTANCE_THRESHOLD: float = 0.35
    STORAGE_DIR: str = "./storage"


settings = Settings()
