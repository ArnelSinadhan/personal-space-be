from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_space"

    # Firebase
    firebase_service_account_key: str | None = None
    firebase_service_account_path: str | None = None
    firebase_storage_bucket: str = ""

    # Security
    vault_encryption_secret: str = "change-me"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    vault_session_expire_minutes: int = 30

    # CORS
    allowed_origins: str = "http://localhost:3000"

    # Environment
    environment: str = "development"
    debug: bool = True

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
