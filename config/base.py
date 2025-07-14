from pydantic_settings import BaseSettings as BaseBaseSettings

class BaseSettings(BaseBaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"