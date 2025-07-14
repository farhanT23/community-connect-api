

from config.base import BaseSettings


class DatabaseSettings(BaseSettings):
    database_driver: str="sqlite"
    database_host: str|None
    database_port: int|None
    database_user: str|None
    database_password: str|None
    database_name: str|None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"