from datetime import datetime, timedelta, timezone
from jose import jwt
from config import jwt_settings


class JWTToken:
    @staticmethod
    def create_access_token(data: dict, expires_delta: int = None):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta or jwt_settings.jwt_access_token_expire_minutes
        )
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            jwt_settings.jwt_secret_key,
            algorithm=jwt_settings.jwt_algorithm
        )

    @staticmethod
    def create_refresh_token(data: dict, expires_delta: int = None):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta or jwt_settings.jwt_refresh_token_expire_minutes
        )
        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode,
            jwt_settings.jwt_secret_key,
            algorithm=jwt_settings.jwt_algorithm
        )

    @staticmethod
    def decode_token(token: str):
        try:
            return jwt.decode(
                token,
                jwt_settings.jwt_secret_key,
                algorithms=[jwt_settings.jwt_algorithm]
            )
        except Exception:
            return None
