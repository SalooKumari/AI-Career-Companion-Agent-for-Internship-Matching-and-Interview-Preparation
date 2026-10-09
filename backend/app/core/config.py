"""
Central app configuration, loaded from environment variables (.env).
Keeping this in one place means every module imports `settings`
instead of calling os.getenv() everywhere.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Local development default: works without a separate PostgreSQL service.
    # If you want PostgreSQL instead, set DATABASE_URL in backend/.env.
    DATABASE_URL: str = "sqlite:///./career_companion.db"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = ""
    UPLOAD_DIR: str = "uploads"
    FRONTEND_ORIGIN: str = "http://127.0.0.1:5500"

    JWT_SECRET_KEY: str = "change-this-to-a-long-random-string-in-your-.env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
