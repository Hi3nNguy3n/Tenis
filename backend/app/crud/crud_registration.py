# backend/app/crud/crud_registration.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta

from app.models.models import Tournament, Player, Registration
from app.schemas.registration_schemas import RegistrationCreate

def register_tournament(db: Session, reg_in: RegistrationCreate, current_player_id: int):
    # 1. TÌM VÀ KHÓA DÒNG GIẢI ĐẤU (with_for_update giúp chống trùng slot khi nhiều người click cùng lúc)
    tournament = db.query(Tournament).filter(
        Tournament.id == reg_in.tournament_id
    ).with_for_update().first()

    if not tournament:
        raise HTTPException(status_code=404, detail="Giải đấu không tồn tại.")
        
    if tournament.status != "open":
        raise HTTPException(status_code=400, detail="Giải đấu hiện không mở đăng ký.")

    # 2. Kiểm tra VĐV đã đăng ký giải này chưa (Chỉ xét các đơn hợp lệ)
    existing_reg = db.query(Registration).filter(
        Registration.tournament_id == reg_in.tournament_id,
        Registration.player_id == current_player_id,
        Registration.status.notin_(["cancelled", "rejected"]),
        Registration.deleted_at.is_(None)
    ).first()
    
    if existing_reg:
        raise HTTPException(status_code=400, detail="Bạn đã đăng ký hoặc đang giữ chỗ giải này rồi.")

    # 3. Đếm số lượng slot ĐANG GIỮ CHỖ (chưa hết hạn) hoặc ĐÃ THANH TOÁN
    current_time = datetime.utcnow()
    active_count = db.query(Registration).filter(
        Registration.tournament_id == tournament.id,
        Registration.deleted_at.is_(None),
        (Registration.payment_status == "paid") | 
        ((Registration.payment_status == "holding") & (Registration.hold_expires_at > current_time))
    ).count()

    if active_count >= tournament.max_participants:
        raise HTTPException(status_code=400, detail="Rất tiếc, giải đấu đã hết chỗ.")

    # 4. TẠO ĐƠN ĐĂNG KÝ (GIỮ CHỖ 15 PHÚT)
    expires = current_time + timedelta(minutes=15)
    
    new_reg = Registration(
        tournament_id=reg_in.tournament_id,
        registrant_type=reg_in.registrant_type,
        player_id=current_player_id if reg_in.registrant_type == "player" else None,
        team_id=reg_in.team_id if reg_in.registrant_type == "team" else None,
        status="pending",
        payment_status="holding", # Trạng thái đang chờ thanh toán
        registered_at=current_time,
        hold_expires_at=expires,
        notes=reg_in.notes
    )
    
    db.add(new_reg)
    db.commit() # Lưu vào DB và mở khóa cho người tiếp theo
    db.refresh(new_reg)
    
    return new_reg

def cleanup_expired_registrations(db: Session):
    now = datetime.utcnow()
    # Tìm các đơn đang giữ chỗ nhưng đã hết hạn
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