from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "@cerai"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BASE_URL: str = "http://localhost:8000"
    AIEVAL_DB_URL: str = "mariadb+mariadbconnector://root:password@localhost:3306/test"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()