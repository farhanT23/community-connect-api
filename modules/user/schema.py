import re
from pydantic import BaseModel, Field, field_validator,EmailStr, model_validator
from enum import Enum


from asyncmy.connection import Optional
from pydantic import BaseModel, Field, field_validator,EmailStr

from pydantic import BaseModel, Field, field_validator,EmailStr, model_validator

from datetime import date, datetime

class UserBaseSchema(BaseModel):
    name: str
    email: EmailStr

class UserCreateSchema(UserBaseSchema):
    password: str
    birthdate: date|None
    gender: str|None = Field(examples=["male", "female"])

    @field_validator("gender")
    def validate_gender(cls, v):
        if v not in ["male", "female"]:
            raise ValueError("Gender must be 'male', 'female', or 'other'.")
        return v
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
    

class UserSchema(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_active: Optional[bool] = None
    profile_image: Optional[str] = None
    cover_image: Optional[str] = None
    birthdate: Optional[date] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    followers_count: Optional[int] = 0
    following_count: Optional[int] = 0
    is_followed: Optional[bool] = False

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

class UserProfileUpdateSchema(BaseModel):
    birthdate: date|None
    gender: str|None = Field(examples=["male", "female"])
    bio: str|None


class UserSummaryOut(BaseModel):
    id: int
    name: str
    profile_image: Optional[str]
    model_config = {"from_attributes": True}


class ReactionResponse(BaseModel):
    detail: str


class UserForgotPasswordSchema(BaseModel):
    email: EmailStr

class UserResetPasswordSchema(BaseModel):
    password: str
    new_password: str

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

    @model_validator(mode="after")
    def check_passwords_match(self) -> 'PasswordChange':
        if self.password != self.new_password:
            raise ValueError("Password and new password must be the same")
        return self


