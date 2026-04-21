# backend/app/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class SendOTPRequest(BaseModel):
    email: EmailStr

class RegisterRequest(BaseModel):
    email: EmailStr
    # Ép mật khẩu tối thiểu 6 ký tự
    password: str = Field(..., min_length=6, description="Mật khẩu phải có ít nhất 6 ký tự")
    # Ép họ tên không được để trống (ít nhất 2 ký tự)
    full_name: str = Field(..., min_length=2, description="Họ tên không được để trống")
    otp_code: str
    
    # Regex: Bắt buộc bắt đầu bằng số 0, theo sau là 9 chữ số (Tổng 10 số)
    phone: Optional[str] = Field(None, pattern=r"^0\d{9}$", description="Số điện thoại không hợp lệ")
    
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
