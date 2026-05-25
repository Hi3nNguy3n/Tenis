# backend/app/schemas/auth_schemas.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

class SendOTPRequest(BaseModel):
    email: EmailStr
    purpose: Optional[str] = "signup"

class RegisterRequest(BaseModel):
    email: EmailStr
    # Ép mật khẩu tối thiểu 6 ký tự
    password: str = Field(..., min_length=6, description="Mật khẩu phải có ít nhất 6 ký tự")
    # Ép họ tên không được để trống (ít nhất 2 ký tự)
    full_name: str = Field(..., min_length=2, description="Họ tên không được để trống")
    otp_code: str
    
    # Regex: Bắt đầu bằng số 0, theo sau là 9-10 chữ số (Tổng 10-11 số)
    phone: Optional[str] = Field(None, pattern=r"^0\d{9,10}$", description="Số điện thoại không hợp lệ")
    
    province: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    account_type: Optional[str] = "player"

    # === BỔ SUNG CÁC TRƯỜNG DÀNH CHO ADMIN TẠO MỚI ===
    avatar_url: Optional[str] = None
    skill_level: Optional[str] = "Beginner"
    preferred_category: Optional[str] = "Singles"
    elo_points: Optional[int] = 1000
    play_hand: Optional[str] = "right"
    aces: Optional[int] = 0
    double_faults: Optional[int] = 0
    first_serve_pct: Optional[float] = 0
    first_serve_points_won_pct: Optional[float] = 0
    second_serve_points_won_pct: Optional[float] = 0
    break_points_faced: Optional[int] = 0
    break_points_saved_pct: Optional[float] = 0
    service_games_played: Optional[int] = 0
    service_games_won_pct: Optional[float] = 0
    total_service_points_won_pct: Optional[float] = 0
    first_serve_return_points_won_pct: Optional[float] = 0
    second_serve_return_points_won_pct: Optional[float] = 0
    break_points_opportunities: Optional[int] = 0
    break_points_converted_pct: Optional[float] = 0
    return_games_played: Optional[int] = 0
    return_games_won_pct: Optional[float] = 0
    return_points_won_pct: Optional[float] = 0
    total_points_won_pct: Optional[float] = 0

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
    role_key: Optional[str] = None
