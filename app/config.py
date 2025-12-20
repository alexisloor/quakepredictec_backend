# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "QuakePredictEC Backend"
    # En producción estos se leen de variables de entorno!!
    secret_key: str = "cambiar esta clave por env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

