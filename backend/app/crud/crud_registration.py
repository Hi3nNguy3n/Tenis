# backend/app/crud/crud_registration.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.models.models import Tournament, Player, Registration, User, Payment
from app.schemas.registration_schemas import RegistrationCreate

def register_with_otp_flow(db: Session, tournament_id: int, player_id: int, notes: str, partners: list):
    # 1. Kiểm tra xem đã đăng ký chưa
    existing = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.player_id == player_id,
        Registration.deleted_at.is_(None)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã đăng ký giải đấu này rồi.")

    # 2. Tạo bản ghi mới ở trạng thái chờ duyệt
    db_reg = Registration(
        tournament_id=tournament_id,
        player_id=player_id,
        notes=notes,
        registrant_type="player",
        status="confirmed",          # Mặc định chờ duyệt
        payment_status="pending",  # Mặc định chờ đối soát chuyển khoản
        registered_at=datetime.utcnow(),
        approved_at=datetime.utcnow()
    )
    db.add(db_reg)
    db.commit()
    db.refresh(db_reg)
    
    return db_reg

def get_registrations_by_player(db: Session, player_id: int):
    return db.query(Registration, Tournament).join(
        Tournament, Registration.tournament_id == Tournament.id
    ).filter(
        Registration.player_id == player_id,
        Registration.deleted_at.is_(None)
    ).all()

def cancel_registration_by_user(db: Session, registration_id: int, player_id: int):
    reg = db.query(Registration).filter(
        Registration.id == registration_id,
        Registration.player_id == player_id
    ).first()
    
    if not reg: return None
    if reg.status == "cancelled": return reg
        
    reg.status = "cancelled"
    reg.deleted_at = datetime.utcnow()
    db.commit()
    return reg

def get_all_registrations_admin(db: Session):
    return db.query(Registration, Tournament, Player, User).join(
        Tournament, Registration.tournament_id == Tournament.id
    ).join(
        Player, Registration.player_id == Player.id
    ).join(
        User, Player.user_id == User.id
    ).filter(Registration.deleted_at.is_(None)).all()

def admin_cancel_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg: return None
    
    reg.status = "rejected"
    reg.payment_status = "refunded"
    reg.deleted_at = datetime.utcnow()
    db.commit()
    return reg

def admin_check_in_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg: return None, "not_found"
    if reg.payment_status != "paid": return None, "not_paid"
    
    reg.notes = (reg.notes or "") + f" | Checked-in at {datetime.utcnow()}"
    reg.status = "checked_in"
    
    tourn = db.query(Tournament).filter(Tournament.id == reg.tournament_id).first()
    player = db.query(Player).filter(Player.id == reg.player_id).first()
    user = db.query(User).filter(User.id == player.user_id).first()
    
    db.commit()
    return reg, {"user": user, "tourn": tourn}

def update_registration_qr_url(db: Session, reg_id: int, url: str):
    r = db.query(Registration).filter(Registration.id == reg_id).first()
    if r:
        r.qr_code_url = url
        db.commit()