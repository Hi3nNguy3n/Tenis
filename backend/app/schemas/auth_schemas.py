# backend/app/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class SendOTPRequest(BaseModel):
    email: EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    otp_code: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"