# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

# --- BỔ SUNG CÁC IMPORT DƯỚI ĐÂY ---
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings
from app.db.redis_client import get_redis
# ----------------------------------

from app.db.database import get_db
from app.schemas.auth_schemas import SendOTPRequest, RegisterRequest, LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.crud import crud_auth
from fastapi.security import OAuth2PasswordRequestForm
router = APIRouter()

# Cấu hình Mail (Sử dụng settings đã import)
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    # 1. Rate limit (Redis)
    if r.get(f"limit:{request.email}"):
        raise HTTPException(status_code=429, detail="Vui lòng thử lại sau 60 giây.")

    if crud_auth.get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="Email đã được đăng ký.")

    # 2. Sinh OTP & lưu Redis
    otp = str(random.randint(100000, 999999))
    r.setex(f"otp:{request.email}", 300, otp)
    r.setex(f"limit:{request.email}", 60, "locked")

    # 3. Gửi Mail THẬT
    message = MessageSchema(
        subject="Mã xác thực Saigon Tennis Tour",
        recipients=[request.email],
        body=f"Mã OTP của bạn là: {otp}. Mã có hiệu lực trong 5 phút.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)

    return {"message": "Mã OTP đã được gửi thành công!"}

@router.post("/register")
async def register(
    request: RegisterRequest, 
    db: Session = Depends(get_db), 
    r = Depends(get_redis)
):
    # 1. Verify OTP từ Redis
    cached_otp = r.get(f"otp:{request.email}")
    if not cached_otp or cached_otp != request.otp_code:
        raise HTTPException(status_code=400, detail="Mã OTP không đúng hoặc hết hạn.")

    # 2. Lấy Role 'member'
    role = crud_auth.get_role_by_key(db, "user")
    if not role:
        raise HTTPException(status_code=500, detail="Hệ thống chưa cấu hình Role 'member'.")
    
    # 3. Chạy Transaction
    try:
        user = crud_auth.create_user_and_player_transaction(db, request, role.id)
    except Exception as e: # Bắt biến 'e' để lấy chi tiết lỗi
        # In lỗi chữ đỏ/to ra màn hình Terminal của VS Code để dễ nhìn
        print("\n" + "="*50)
        print("🚨 LỖI TRANSACTION KHI ĐĂNG KÝ:")
        print(str(e))
        print("="*50 + "\n")
        
        # Đồng thời ném thẳng lỗi ra ngoài Swagger UI để bạn thấy
        raise HTTPException(status_code=500, detail=f"Lỗi DB: {str(e)}")
    
    # 4. Xóa OTP sau khi dùng xong
    r.delete(f"otp:{request.email}")
    
    return {"message": "Đăng ký thành công", "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Đổi form_data.username thành request.email
    user = crud_auth.get_user_by_email(db, request.email)
    
    # Đổi form_data.password thành request.password
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị khóa.")

    access_token = create_access_token(
        data={"sub": str(user.id), "role_id": user.role_id}
    )
    
    user.last_login_at = datetime.utcnow()
    db.commit()

    return {"access_token": access_token, "token_type": "bearer"}