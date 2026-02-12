from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Wishlist API"
    secret_key: str = "change-me"
    guest_token_secret: str = "guest-secret"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    database_url: str = "postgresql+psycopg://wishlist:wishlist@localhost:5432/wishlist"
    frontend_url: str = "http://localhost:3000"


settings = Settings()
