from config.base import BaseSettings


class AppSettings(BaseSettings):
    app_name: str="FastAPI"
    app_version: str="1.0.0"
    env: str = "dev"