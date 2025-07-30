import re


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
    

class UserSchema(UserBaseSchema):
    id: int
    is_active: bool
    profile_image: str|None
    cover_image: str|None
    birthdate: date|None
    gender: str|None = Field(examples=["male", "female"])
    bio: str|None
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

class UserProfileUpdateSchema(BaseModel):
    birthdate: date|None
    gender: str|None = Field(examples=["male", "female"])
    bio: str|None


class UserSummaryOut(BaseModel):
    id: int
    name: str
    profile_image: Optional[str]
    model_config = {"from_attributes": True}

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


