from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = "@cerai"
    REFRESH_SECRET_KEY: str = "@cerai_refresh"  # Separate key for refresh tokens (optional but recommended)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 320
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh tokens expire in 7 days
    BASE_URL: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()