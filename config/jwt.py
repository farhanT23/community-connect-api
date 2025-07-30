

from config.base import BaseSettings


class JWTSettings(BaseSettings):
    jwt_secret_key: str|None
    jwt_algorithm: str|None
    jwt_access_token_expire_minutes: int=5
    jwt_refresh_token_expire_minutes: int=2400