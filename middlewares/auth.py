
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer


from utils.jwt_token import JWTToken

oauth2_scheme = HTTPBearer(auto_error=False)
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


def optional_get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    payload = JWTToken.decode_token(token.credentials)
    if not payload:
        return None
    return payload