from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    secret_key: str
    database_username: str
    database_host: str = 'localhost'
    database: str
    database_password: str
    cloudinary_cloud_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    config: str = 'development'
    database_uri: str = ''

    model_config = SettingsConfigDict(env_file='.env')


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_uri = "postgresql://{}:{}@{}/{}".format(
        settings.database_username,
        settings.database_password,
        settings.database_host,
        settings.database
    )

    return settings
