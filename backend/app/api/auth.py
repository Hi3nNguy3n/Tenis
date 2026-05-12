# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import random

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings
from app.db.redis_client import get_redis

from app.db.database import get_db
from app.schemas.auth_schemas import SendOTPRequest, RegisterRequest, LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.crud import crud_auth

from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@router.post("/change-password")
def change_password(
    old_password: str, 
    new_password: str, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không chính xác.")
    
    crud_auth.update_password(db, user=current_user, new_password=new_password)
    return {"message": "Đổi mật khẩu thành công!"}

@router.post("/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    otp = str(random.randint(100000, 999999))
    
    # Lưu OTP vào Redis (giữ nguyên thời gian hết hạn của ông)
    r.setex(f"otp:{request.email}", 300, otp) 

    # Gửi Email (giữ nguyên template của ông)
    message = MessageSchema(
        subject="Mã xác thực Saigon Tennis Tour",
        recipients=[request.email],
        body=f"Mã xác thực của bạn là: {otp}. Mã có hiệu lực trong 5 phút.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return {"message": "Mã OTP đã được gửi thành công."}

@router.post("/register")
def register(
    request: RegisterRequest, 
    db: Session = Depends(get_db), 
    r = Depends(get_redis)
):
    cached_otp = r.get(f"otp:{request.email}")
    if not cached_otp or cached_otp != request.otp_code:
        raise HTTPException(status_code=400, detail="Mã OTP không đúng hoặc hết hạn.")

    role = crud_auth.get_role_by_key(db, "user")
    if not role:
        raise HTTPException(status_code=500, detail="Hệ thống chưa cấu hình Role 'user'.")
    
    try:
        user = crud_auth.create_user_and_player_transaction(db, request, role.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi DB: {str(e)}")
    
    r.delete(f"otp:{request.email}")
    return {"message": "Đăng ký thành công", "user_id": user.id}

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = crud_auth.get_user_by_email(db, request.email)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị khóa.")

    access_token = create_access_token(
        data={"sub": str(user.id), "role_id": user.role_id}
    )
    
    crud_auth.update_last_login(db, user)

    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "full_name": user.full_name,
        "role_id": user.role_id,
        "account_type": user.account_type
    }

@router.post("/forgot-password")
async def forgot_password(request: SendOTPRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    user = crud_auth.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống.")

    otp = str(random.randint(100000, 999999))
    r.setex(f"reset_otp:{request.email}", 600, otp) 

    message = MessageSchema(
        subject="Khôi phục mật khẩu Saigon Tennis Tour",
        recipients=[request.email],
        body=f"Mã xác thực khôi phục mật khẩu của bạn là: {otp}. Vui lòng không cung cấp mã này cho bất kỳ ai.",
        subtype=MessageType.plain
    )
    fm = FastMail(conf)
    await fm.send_message(message)
    return {"message": "Mã khôi phục đã được gửi tới email của bạn."}

@router.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db), r = Depends(get_redis)):
    cached_otp = r.get(f"reset_otp:{email}")
    if not cached_otp or cached_otp != otp:
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng hoặc đã hết hạn.")
    
    user = crud_auth.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại.")
    
    crud_auth.update_password(db, user=user, new_password=new_password)
    r.delete(f"reset_otp:{email}")
    return {"message": "Đổi mật khẩu thành công!"}

def verify_otp(email: str, otp_code: str):
    """Hàm helper để kiểm tra mã OTP từ Redis"""
    from app.db.redis_client import get_redis
    
    try:
        # Vì get_redis là một generator, ta dùng next() để lấy instance
        redis_gen = get_redis()
        r = next(redis_gen)
        
        cached_otp = r.get(f"otp:{email}")
        
        if not cached_otp:
            return False
            
        # Nếu redis_client đã set decode_responses=True thì cached_otp là string
        # Nếu chưa, ta cần decode. Để an toàn nhất, ta ép kiểu về string để so sánh
        if str(cached_otp) == str(otp_code):
            r.delete(f"otp:{email}") # Dùng xong xóa luôn
            return True
    except StopIteration:
        pass
    except Exception as e:
        print(f"Lỗi Redis verify_otp: {e}")
        
    return False