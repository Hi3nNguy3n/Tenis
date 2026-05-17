# backend/app/crud/crud_auth.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import User, Player, AuthOtp, Role
from app.schemas.auth_schemas import RegisterRequest
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_role_by_key(db: Session, role_key: str):
    return db.query(Role).filter(Role.role_key == role_key).first()

def get_role_by_id(db: Session, role_id: int):
    return db.query(Role).filter(Role.id == role_id).first()

def update_password(db: Session, user: User, new_password: str):
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

def update_last_login(db: Session, user: User):
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def create_otp_record(db: Session, email: str, otp_code: str, expire_time: datetime):
    new_otp = AuthOtp(
        target_email=email,
        otp_code=otp_code,
        purpose="signup",
        expired_at=expire_time
    )
    db.add(new_otp)
    db.commit()
    db.refresh(new_otp)
    return new_otp

def get_valid_otp(db: Session, email: str, otp_code: str):
    return db.query(AuthOtp).filter(
        AuthOtp.target_email == email,
        AuthOtp.otp_code == otp_code,
        AuthOtp.purpose == "signup",
        AuthOtp.is_used == False
    ).order_by(AuthOtp.created_at.desc()).first()

def create_user_and_player_transaction(db: Session, request: RegisterRequest, role_id: int):
    try:
        new_user = User(
            email=request.email,
            password_hash=get_password_hash(request.password),
            full_name=request.full_name,
            account_type=request.account_type or "user",
            phone=request.phone,
            province=request.province,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            role_id=role_id,
            is_verified=True,
            avatar_url=request.avatar_url # BỔ SUNG LƯU AVATAR VÀO BẢNG USER
        )
        db.add(new_user)
        db.flush()

        new_player = Player(
            user_id=new_user.id,
            gender=request.gender,                         # ĐỒNG BỘ GIỚI TÍNH
            date_of_birth=request.date_of_birth,           # ĐỒNG BỘ NGÀY SINH
            play_hand=request.play_hand,                   # BỔ SUNG TAY THUẬN
            skill_level=request.skill_level,               # BỔ SUNG TRÌNH ĐỘ
            preferred_category=request.preferred_category, # BỔ SUNG SỞ TRƯỜNG
            elo_points=request.elo_points                  # BỔ SUNG ĐIỂM ELO
        )
        db.add(new_player)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise e