# app/config.py
from pydantic import BaseSettings
from .config import settings

class Settings(BaseSettings):
    app_name: str = "QuakePredictEC Backend"
    # En producción estos se leen de variables de entorno!!
    secret_key: str = settings.secret_key
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
