from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/personal_space"

    # Firebase
    firebase_service_account_key: str | None = None
    firebase_service_account_path: str | None = None
    firebase_storage_bucket: str = ""
    firebase_session_expire_days: int = 7

    # Supabase Storage
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_profile_images_bucket: str = "profile-images"
    supabase_company_images_bucket: str = "company-images"
    supabase_certification_images_bucket: str = "certification-images"
    supabase_project_images_bucket: str = "project-images"
    supabase_resume_files_bucket: str = "resume-files"
    signed_url_expire_seconds: int = 3600
    max_image_upload_bytes: int = 5 * 1024 * 1024
    max_resume_upload_bytes: int = 10 * 1024 * 1024

    # Security
    vault_encryption_secret: str = "change-me"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    vault_session_expire_minutes: int = 30

    # CORS
    allowed_origins: str = "http://localhost:3000"
    frontend_app_url: str = "http://localhost:3000"

    # Public testimonial protection
    public_testimonial_rate_limit_window_minutes: int = 60
    public_testimonial_rate_limit_max_attempts: int = 3
    public_testimonial_captcha_secret: str | None = None
    public_testimonial_captcha_verify_url: str = (
        "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    )

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
