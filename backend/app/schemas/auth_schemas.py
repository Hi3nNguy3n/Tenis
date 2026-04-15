# backend/app/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class SendOTPRequest(BaseModel):
    email: EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    otp_code: str
    phone: Optional[str] = None
    province: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    account_type: Optional[str] = "player"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: Optional[int] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    account_type: Optional[str] = None
