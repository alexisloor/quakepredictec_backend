# app/schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional



class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None

