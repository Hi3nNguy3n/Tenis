# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import random

from app.db.redis_client import get_redis
from app.db.database import get_db
from app.schemas.auth_schemas import SendOTPRequest, RegisterRequest, LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.core.mail import send_email
from app.crud import crud_auth
from app.api.deps import get_current_user
from app.models.models import User
router = APIRouter()

# ==========================================
# 1. API GỬI OTP ĐĂNG KÝ
# ==========================================
@router.post("/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    email_key = request.email.lower().strip()
    purpose = (request.purpose or "signup").strip().lower()
    existing_user = crud_auth.get_user_by_email(db, email_key)
    if purpose != "signup" and not existing_user:
        raise HTTPException(status_code=404, detail="Email khong ton tai trong he thong.")
    if purpose == "signup" and existing_user:
        raise HTTPException(status_code=400, detail="Email này đã được sử dụng trong hệ thống.")

    # Tạo mã OTP ngẫu nhiên
    otp_code = str(random.randint(100000, 999999))
    
    # Lưu OTP vào Redis với thời hạn 300s (5 phút)
    print(f"[DEBUG SEND OTP]: Key='otp:{email_key}', Value='{otp_code}'")
    r.setex(f"otp:{email_key}", 300, otp_code) 
    
    # Gửi email qua SMTP/app password
    subject = "Mã xác nhận OTP - Saigon Tennis Tours"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Xin chào,</h2>
        <p>Bạn vừa yêu cầu mã OTP để xác thực tài khoản tại Saigon Tennis Tours.</p>
        <p>Mã xác nhận của bạn là: <strong style="font-size: 24px; color: #10b981;">{otp_code}</strong></p>
        <p>Mã này sẽ hết hạn sau 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.</p>
    </div>
    """
    await send_email(email_to=request.email, subject=subject, html_content=html_content)
    
    return {"message": "Mã OTP đã được gửi đến email của bạn!"}

# ==========================================
# 2. API XÁC NHẬN ĐĂNG KÝ (CHECK REDIS)
# ==========================================
@router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    # Kiểm tra OTP trong Redis
    email_key = request.email.lower().strip()
    if crud_auth.get_user_by_email(db, email_key):
        raise HTTPException(status_code=400, detail="Email này đã được sử dụng trong hệ thống.")

    cached_otp = r.get(f"otp:{email_key}")
    
    # Xử lý trường hợp cached_otp là kiểu bytes (tùy cấu hình Redis)
    decoded_otp = cached_otp.decode("utf-8") if isinstance(cached_otp, bytes) else cached_otp
    print(f"[DEBUG VERIFY OTP]: Key='otp:{email_key}', Cached='{decoded_otp}', Sent='{request.otp_code}'")

    if not decoded_otp or str(decoded_otp).strip() != str(request.otp_code).strip():
        raise HTTPException(status_code=400, detail="Mã OTP không đúng hoặc hết hạn.")

    role = crud_auth.get_role_by_key(db, "user")
    if not role:
        raise HTTPException(status_code=500, detail="Hệ thống chưa cấu hình Role 'user'.")
    
    try:
        user = crud_auth.create_user_and_player_transaction(db, request, role.id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email này đã được sử dụng trong hệ thống.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi DB: {str(e)}")
    
    # Dùng xong xóa OTP
    r.delete(f"otp:{email_key}")
    return {"message": "Đăng ký thành công", "user_id": user.id}

# ==========================================
# 3. API ĐĂNG NHẬP
# ==========================================
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

# ==========================================
# 4. API QUÊN MẬT KHẨU (GỬI OTP)
# ==========================================
@router.post("/forgot-password")
async def forgot_password(request: SendOTPRequest, db: Session = Depends(get_db), r = Depends(get_redis)):
    user = crud_auth.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại trong hệ thống.")

    otp = str(random.randint(100000, 999999))
    r.setex(f"reset_otp:{request.email}", 600, otp) # Thời hạn 10 phút

    subject = "Khôi phục mật khẩu - Saigon Tennis Tours"
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>Xin chào,</h2>
        <p>Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản của bạn.</p>
        <p>Mã xác thực của bạn là: <strong style="font-size: 24px; color: #eab308;">{otp}</strong></p>
        <p>Mã có hiệu lực trong 10 phút. Vui lòng không cung cấp mã này cho bất kỳ ai.</p>
    </div>
    """
    await send_email(email_to=request.email, subject=subject, html_content=html_content)
    
    return {"message": "Mã khôi phục đã được gửi tới email của bạn."}

# ==========================================
# 5. API ĐẶT LẠI MẬT KHẨU (CHECK REDIS)
# ==========================================
@router.post("/reset-password")
def reset_password(email: str, otp: str, new_password: str, db: Session = Depends(get_db), r = Depends(get_redis)):
    cached_otp = r.get(f"reset_otp:{email}")
    decoded_otp = cached_otp.decode("utf-8") if isinstance(cached_otp, bytes) else cached_otp
    
    if not decoded_otp or decoded_otp != otp:
        raise HTTPException(status_code=400, detail="Mã xác thực không đúng hoặc đã hết hạn.")
    
    user = crud_auth.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại.")
    
    crud_auth.update_password(db, user=user, new_password=new_password)
    r.delete(f"reset_otp:{email}")
    
    return {"message": "Đổi mật khẩu thành công!"}

# ==========================================
# 6. ĐỔI MẬT KHẨU BÊN TRONG HỆ THỐNG
# ==========================================
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

# ==========================================
# 7. HÀM HELPER 
# ==========================================
def verify_otp(email: str, otp_code: str):
    """Hàm helper để kiểm tra mã OTP nội bộ"""
    try:
        redis_gen = get_redis()
        r = next(redis_gen)
        
        cached_otp = r.get(f"otp:{email}")
        if not cached_otp:
            return False
            
        decoded_otp = cached_otp.decode("utf-8") if isinstance(cached_otp, bytes) else cached_otp
        
        if str(decoded_otp) == str(otp_code):
            r.delete(f"otp:{email}") 
            return True
    except Exception as e:
        print(f"Lỗi Redis verify_otp: {e}")
        
    return False
