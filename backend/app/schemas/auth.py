from pydantic import BaseModel, EmailStr
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_admin: bool

    class Config:
        from_attributes = True
