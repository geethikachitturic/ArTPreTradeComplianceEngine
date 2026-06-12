from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://art_user:art_password@localhost:5432/art_db"
    app_env: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
