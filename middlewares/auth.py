
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from typing import Optional
from jose import JWTError, jwt
from config import app_settings


from utils.jwt_token import JWTToken

oauth2_scheme = HTTPBearer()
def get_current_user(token: str = Depends(oauth2_scheme)):
    print(token.credentials)
    payload = JWTToken.decode_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

async def optional_get_current_user(request: Request) -> Optional[dict]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # No token present, return None (unauthenticated)
        return None

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, app_settings.jwt_secret, algorithms=[app_settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return {"user_id": int(user_id)}
    except JWTError:
        # Invalid token; treat as unauthenticated, return None
        return None

