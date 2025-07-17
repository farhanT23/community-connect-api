
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from typing import Optional
from jose import JWTError, jwt
from config import app_settings


from utils.jwt_token import JWTToken

oauth2_scheme = HTTPBearer(auto_error=False)
oauth1_scheme = HTTPBearer()
def get_current_user(token: str = Depends(oauth1_scheme)):
    payload = JWTToken.decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

async def optional_get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[dict]:
    if token is None:
        return None

    payload = JWTToken.decode_token(token.credentials)
    if not payload:
        return None
    return payload

