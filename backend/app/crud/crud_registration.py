# backend/app/crud/crud_registration.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from datetime import datetime, timedelta
from typing import Optional

from app.models.models import Tournament, Player, Registration, User, Payment, TournamentCategory
from app.schemas.registration_schemas import RegistrationCreate

def register_with_otp_flow(db: Session, tournament_id: int, category_id: int, player_id: int, notes: str, partners: list):
    # Lấy thông tin partner nếu có
    partner_player_id = None
    partner_user_id = None
    partner_name = None
    partner_phone = None
    partner_email = None

    if partners and isinstance(partners, list) and len(partners) > 0:
        p = partners[0]
        partner_player_id = p.get("player_id")
        partner_name = p.get("name")
        partner_phone = p.get("phone")
        partner_email = p.get("email")
        
        # Nếu có partner_player_id, lấy user_id tương ứng
        if partner_player_id:
            partner_obj = db.query(Player).filter(Player.id == partner_player_id).first()
            if partner_obj:
                partner_user_id = partner_obj.user_id

    # 1. Kiểm tra xem người đăng ký đã tham gia nội dung này chưa (Dù là người đăng ký chính hay đồng đội của người khác)
    existing_registrant = db.query(Registration).filter(
        Registration.tournament_id == tournament_id,
        Registration.tournament_category_id == category_id,
        Registration.deleted_at.is_(None),
        Registration.status.notin_(["rejected", "cancelled"]),
        or_(
            Registration.player_id == player_id,
            Registration.partner_player_id == player_id
        )
    ).first()
    
    if existing_registrant:
        if existing_registrant.player_id == player_id:
            raise HTTPException(status_code=400, detail="Bạn đã đăng ký nội dung này rồi.")
        else:
            raise HTTPException(status_code=400, detail="Bạn đã được đăng ký làm đồng đội trong một đội khác cho nội dung này.")

    # 2. Kiểm tra đồng đội (nếu có liên kết tài khoản)
    if partner_player_id:
        # 2.1 Không cho tự đánh với chính mình
        if partner_player_id == player_id:
            raise HTTPException(status_code=400, detail="Bạn không thể chọn chính mình làm đồng đội.")

        # 2.2 Kiểm tra xem đồng đội đã tham gia chưa
        existing_partner = db.query(Registration).filter(
            Registration.tournament_id == tournament_id,
            Registration.tournament_category_id == category_id,
            Registration.deleted_at.is_(None),
            Registration.status.notin_(["rejected", "cancelled"]),
            or_(
                Registration.player_id == partner_player_id,
                Registration.partner_player_id == partner_player_id
            )
        ).first()
        
        if existing_partner:
            raise HTTPException(status_code=400, detail=f"Đồng đội {partner_name} đã đăng ký tham gia nội dung này rồi.")

    # 3. Validate category and partner requirements
    category = db.query(TournamentCategory).filter(TournamentCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung thi đấu.")
    
    cat_type = category.category_type.lower()
    
    # Validation for doubles
    if "doubles" in cat_type:
        if not partner_player_id:
             raise HTTPException(status_code=400, detail="Đăng ký đánh đôi yêu cầu thông tin đồng đội (đã liên kết tài khoản).")

    # 4. Xác định registrant_type (đơn/đôi)
    registrant_type = "single" if "singles" in cat_type else "team"


    # 2. Tạo bản ghi mới ở trạng thái chờ duyệt
    db_reg = Registration(
        tournament_id=tournament_id,
        tournament_category_id=category_id,
        player_id=player_id,
        partner_player_id=partner_player_id,
        partner_user_id=partner_user_id,
        partner_name=partner_name,
        partner_phone=partner_phone,
        partner_email=partner_email,
        notes=notes,
        registrant_type=registrant_type,
        status="confirmed",          # Mặc định đã xác nhận sau khi OTP thành công
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
        or_(
            Registration.player_id == player_id,
            Registration.partner_player_id == player_id
        ),
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
    return db.query(Registration, Tournament, Player, User, TournamentCategory).join(
        Tournament, Registration.tournament_id == Tournament.id
    ).join(
        Player, Registration.player_id == Player.id
    ).join(
        User, Player.user_id == User.id
    ).outerjoin(
        TournamentCategory, Registration.tournament_category_id == TournamentCategory.id
    ).filter(Registration.deleted_at.is_(None)).all()

def admin_cancel_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg: return None
    
    reg.status = "rejected"
    reg.payment_status = "refunded"
    # Bỏ dòng gán deleted_at để đơn bị từ chối vẫn nằm trên giao diện quản trị
    db.commit()
    return reg

def admin_check_in_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg: 
        return None, "not_found"
    
    tourn = db.query(Tournament).filter(Tournament.id == reg.tournament_id).first()
    player = db.query(Player).filter(Player.id == reg.player_id).first()
    user = db.query(User).filter(User.id == player.user_id).first()
    
    info = {
        "user": user, 
        "tourn": tourn,
        "entry_fee": float(tourn.entry_fee) if tourn and tourn.entry_fee else 0
    }

    # Trường hợp chưa thanh toán
    if reg.payment_status != "paid":
        info["status"] = "requires_payment"
        return reg, info
    
    # Trường hợp đã check-in rồi
    if reg.status == "checked_in":
        info["status"] = "already_checked_in"
        return reg, info
        
    # Trường hợp hợp lệ -> Thực hiện check-in
    reg.notes = (reg.notes or "") + f" | Checked-in at {datetime.utcnow()}"
    reg.status = "checked_in"
    db.commit()
    
    info["status"] = "success"
    return reg, info

def update_registration_qr_url(db: Session, reg_id: int, url: str):
    r = db.query(Registration).filter(Registration.id == reg_id).first()
    if r:
        r.qr_code_url = url
        db.commit()

def lock_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        return None
    reg.is_locked = True
    db.commit()
    db.refresh(reg)
    return reg

def unlock_registration(db: Session, registration_id: int):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        return None
    reg.is_locked = False
    db.commit()
    db.refresh(reg)
    return reg

def admin_delete_registration(db: Session, registration_id: int):
    # Soft delete the registration by setting deleted_at
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        return None
    reg.deleted_at = datetime.utcnow()
    db.commit()
    return reg

def admin_change_registration_category(db: Session, registration_id: int, category_id: int, partner_player_id: Optional[int] = None):
    # Change category and update partner information accordingly
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
        
    category = db.query(TournamentCategory).filter(
        TournamentCategory.id == category_id,
        TournamentCategory.tournament_id == reg.tournament_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy nội dung thi đấu thuộc giải đấu hiện tại.")
        
    cat_type = category.category_type.lower()
    
    # Update registration category and registrant type
    reg.tournament_category_id = category_id
    reg.registrant_type = "single" if "singles" in cat_type else "team"
    
    # Handle partner details based on singles/doubles format
    if "doubles" in cat_type:
        if not partner_player_id:
            raise HTTPException(status_code=400, detail="Nội dung đánh đôi yêu cầu thông tin đồng đội (đã liên kết tài khoản).")
        
        if partner_player_id == reg.player_id:
            raise HTTPException(status_code=400, detail="Không thể chọn chính mình làm đồng đội.")
            
        partner = db.query(Player).filter(Player.id == partner_player_id).first()
        if not partner:
            raise HTTPException(status_code=404, detail="Không tìm thấy đồng đội.")
            
        partner_user = db.query(User).filter(User.id == partner.user_id).first()
        if not partner_user:
            raise HTTPException(status_code=404, detail="Đồng đội chưa được liên kết tài khoản User.")
            
        reg.partner_player_id = partner.id
        reg.partner_user_id = partner_user.id
        reg.partner_name = partner_user.full_name
        reg.partner_phone = partner_user.phone
        reg.partner_email = partner_user.email
    else:
        # Clear partner details for singles format
        reg.partner_player_id = None
        reg.partner_user_id = None
        reg.partner_name = None
        reg.partner_phone = None
        reg.partner_email = None
        
    db.commit()
    db.refresh(reg)
    return reg
