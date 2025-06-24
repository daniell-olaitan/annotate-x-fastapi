import os

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    database_username: str
    database_host: str
    database: str
    database_password: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    config: str
    database_uri: str

    model_config = (
        SettingsConfigDict(env_file='.env')
        if os.getenv('CONFIG') == 'development'
        else SettingsConfigDict()
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    return settings
