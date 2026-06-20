from pydantic_settings import BaseSettings
from pydantic import AnyUrl
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: AnyUrl
    supabase_anon_key: str
    supabase_service_role_key: str

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 720  # 30 days

    # App
    app_env: str = "development"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
