"""Application Configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://aicte_user:aicte_password@localhost:5433/aicte_db"
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://aicte_user:aicte_password@localhost:5433/aicte_db"
    TEST_DATABASE_URL: str = "sqlite:///./test.db"

    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadminpassword"
    S3_BUCKET: str = "aicte-documents"
    STORAGE_DIR: str = "./storage/documents"

    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025

    JWT_SECRET: str = "dev_secret_key_change_in_production_super_secure_32_bytes_min"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24

    CLOCK_OFFSET_SECONDS: int = 0


settings = Settings()
