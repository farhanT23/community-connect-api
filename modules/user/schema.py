import re
from pydantic import BaseModel, field_validator,EmailStr
from datetime import datetime

class UserBaseSchema(BaseModel):
    name: str
    email: EmailStr

class UserCreateSchema(UserBaseSchema):
    password: str

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v
    

class UserSchema(UserBaseSchema):
    id: int
    is_active: bool
    profile_image: str|None
    cover_image: str|None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str="bearer"

class UserLoginResponseSchema(BaseModel):
    token:Token
    user: UserSchema
