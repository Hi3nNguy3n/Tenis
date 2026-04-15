# backend/app/crud/crud_registration.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.models.models import Tournament, Player, Registration, User, Payment
from app.schemas.registration_schemas import RegistrationCreate

def register_tournament(db: Session, reg_in: RegistrationCreate, current_player_id: int):
    # 1. KHÓA DÒNG GIẢI ĐẤU (Chống trùng slot)
    tournament = db.query(Tournament).filter(
        Tournament.id == reg_in.tournament_id
    ).with_for_update().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Giải đấu không tồn tại.")
        
    if tournament.status != "open":
        raise HTTPException(status_code=400, detail="Giải đấu hiện không mở đăng ký.")

    # 2. Kiểm tra VĐV đã đăng ký giải này chưa
    existing_reg = db.query(Registration).filter(
        Registration.tournament_id == reg_in.tournament_id,
        Registration.player_id == current_player_id,
        Registration.status.notin_(["cancelled", "rejected"]),
        Registration.deleted_at.is_(None)
    ).first()
    
    if existing_reg:
        raise HTTPException(status_code=400, detail="Bạn đã đăng ký hoặc đang giữ chỗ giải này rồi.")

    # 3. Đếm số lượng slot ĐANG GIỮ CHỖ hoặc ĐÃ THANH TOÁN
    current_time = datetime.utcnow()
    active_count = db.query(Registration).filter(
        Registration.tournament_id == tournament.id,
        Registration.deleted_at.is_(None),
        (Registration.payment_status == "paid") | 
        ((Registration.payment_status == "holding") & (Registration.hold_expires_at > current_time))
    ).count()

    limit = tournament.max_participants if tournament.max_participants is not None else tournament.draw_size
    if limit and active_count >= limit:
        raise HTTPException(status_code=400, detail=f"Rất tiếc, giải đấu đã đủ số lượng người tham gia ({limit}).")

    # 4. TẠO ĐƠN ĐĂNG KÝ (GIỮ CHỖ 10 PHÚT)
    expires = current_time + timedelta(minutes=10)
    
    new_reg = Registration(
        tournament_id=reg_in.tournament_id,
        registrant_type=reg_in.registrant_type,
        player_id=current_player_id,
        team_id=reg_in.team_id if reg_in.registrant_type == "team" else None,
        status="pending",
        payment_status="holding",
        registered_at=current_time,
        hold_expires_at=expires,
        notes=reg_in.notes,
        partner_name=reg_in.partner_name,
        partner_phone=reg_in.partner_phone,
        partner_email=reg_in.partner_email,
        partner_user_id=reg_in.partner_user_id,
        team_members_data=[m.model_dump() for m in reg_in.team_members_data] if reg_in.team_members_data else []
    )
    
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

def cleanup_expired_registrations(db: Session):
    now = datetime.utcnow()
    expired_regs = db.query(Registration).filter(
        Registration.payment_status == "holding",
        Registration.hold_expires_at < now,
        Registration.status == "pending"
    ).all()

    for reg in expired_regs:
        reg.status = "cancelled"
        reg.payment_status = "expired"
        reg.notes = (reg.notes or "") + " | Tự động hủy do hết hạn thanh toán."
    
    db.commit()
    return len(expired_regs)

# --- CÁC HÀM BỔ SUNG CHO TẦNG API ---

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

def confirm_simulated_payment(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg: return None, None
    if reg.payment_status == "paid": return reg, None

    reg.status = "confirmed"
    reg.payment_status = "paid"
    reg.approved_at = datetime.utcnow()
    reg.deleted_at = None

    tourn = db.query(Tournament).filter(Tournament.id == reg.tournament_id).first()
    fee = float(tourn.entry_fee if reg.registrant_type == "single" else tourn.entry_fee_team)
    
    new_payment = Payment(
        registration_id=reg.id,
        amount=fee,
        currency="VND",
        payment_method="Simulated Pay",
        transaction_ref=f"SIM_{reg.id}_{int(datetime.utcnow().timestamp())}",
        status="completed",
        paid_at=datetime.utcnow()
    )
    db.add(new_payment)
    db.commit()
    return reg, tourn

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