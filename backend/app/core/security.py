# backend/app/core/security.py
from datetime import datetime, timedelta
import bcrypt
from jose import jwt
from app.core.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 ngày

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt yêu cầu dữ liệu phải được encode sang bytes (utf-8) trước khi kiểm tra
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    # Sinh salt và băm mật khẩu
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    # Decode trả về dạng string để lưu vào Database dễ dàng
    return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt