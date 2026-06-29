# backend/app/api/registrations.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging

from app.db.database import get_db, SessionLocal
from app.api.deps import get_current_user, get_current_admin
from app.models.models import User, Registration, Tournament, Player, Payment, TournamentCategory
from app.crud import crud_registration, crud_player
from app.schemas import registration_schemas
from app.core.qr_generator import generate_registration_qr

router = APIRouter()
logger = logging.getLogger(__name__)
INTERNAL_ERROR_MESSAGE = "Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên."

# --- BACKGROUND TASK ---
def update_qr(r_id: int, t_name: str):
    db_task = SessionLocal()
    try:
        url = generate_registration_qr(r_id, t_name)
        crud_registration.update_registration_qr_url(db_task, r_id, url)
    except Exception:
        logger.exception("Registration QR generation failed")
    finally:
        db_task.close()

# 2. VĐV XEM CÁC GIẢI MÌNH ĐÃ ĐĂNG KÝ
@router.get("/my-registrations", response_model=List[registration_schemas.RegistrationResponse])
def get_my_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player:
        return []
        
    from sqlalchemy import or_
    registrations_data = db.query(Registration, Tournament, TournamentCategory).join(
        Tournament, Registration.tournament_id == Tournament.id
    ).outerjoin(
        TournamentCategory, Registration.tournament_category_id == TournamentCategory.id
    ).filter(
        or_(
            Registration.player_id == player.id,
            Registration.partner_player_id == player.id
        ),
        Registration.deleted_at.is_(None)
    ).all()
    
    response_items = []
    for reg, tourn, category in registrations_data:
        item = registration_schemas.RegistrationResponse.model_validate(reg)
        item.tournament_name = tourn.name
        item.location = tourn.location
        item.category_id = reg.tournament_category_id
        item.category_type = category.category_type if category else tourn.category_type
        item.category_name = category.name if category else "Mặc định"
        item.entry_fee = float(tourn.entry_fee) if tourn.entry_fee else 0
        item.entry_fee_team = float(tourn.entry_fee_team) if tourn.entry_fee_team else 0
        item.tournament_date = tourn.start_date
        response_items.append(item)
        
    return response_items

# 3. VĐV TỰ HỦY ĐƠN ĐĂNG KÝ
@router.post("/{registration_id}/cancel")
def user_cancel_registration(
    registration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ Vận động viên.")
        
    reg = crud_registration.cancel_registration_by_user(db, registration_id, player.id)
    if not reg:
        raise HTTPException(status_code=404, detail="Đơn đăng ký không tồn tại hoặc không thuộc quyền sở hữu của bạn.")
    
    if reg.status == "cancelled" and reg.deleted_at is None: 
        # Đã hủy trước đó
        return {"message": "Đơn này đã được hủy trước đó."}
        
    return {"message": "Hủy đăng ký thành công. Slot của bạn đã được giải phóng."}

# 5. ADMIN XEM TẤT CẢ ĐƠN ĐĂNG KÝ
@router.get("", response_model=List[registration_schemas.RegistrationResponse], include_in_schema=False)
@router.get("/", response_model=List[registration_schemas.RegistrationResponse])
def admin_get_all_registrations(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    results = crud_registration.get_all_registrations_admin(db)
    
    response_items = []
    for reg, tourn, player, user, category in results:
        item = registration_schemas.RegistrationResponse.model_validate(reg)
        item.tournament_name = tourn.name
        item.location = tourn.location
        item.player_name = user.full_name
        item.tournament_date = tourn.start_date
        item.registered_at = reg.registered_at
        item.category_id = reg.tournament_category_id
        item.category_type = category.category_type if category else tourn.category_type
        item.category_name = category.name if category else "Mặc định"
        item.entry_fee = float(tourn.entry_fee) if tourn.entry_fee else 0
        item.player_phone = user.phone
        item.player_email = user.email
        item.player_skill = player.skill_level
        response_items.append(item)
        
    return response_items

# 6. ADMIN HỦY ĐƠN / HOÀN TIỀN
@router.post("/admin/tournaments/{tournament_id}/add-player", dependencies=[Depends(get_current_admin)])
def admin_add_player_to_tournament(
    tournament_id: int,
    payload: registration_schemas.AdminAddTournamentRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    tournament = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not tournament:
        raise HTTPException(status_code=404, detail="Khong tim thay giai dau.")

    category = db.query(TournamentCategory).filter(
        TournamentCategory.id == payload.category_id,
        TournamentCategory.tournament_id == tournament_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Khong tim thay noi dung thi dau cua giai.")

    player = db.query(Player).filter(Player.id == payload.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Khong tim thay van dong vien.")

    partners = []
    if payload.partner_player_id:
        partner = db.query(Player).filter(Player.id == payload.partner_player_id).first()
        partner_user = db.query(User).filter(User.id == partner.user_id).first() if partner else None
        if not partner or not partner_user:
            raise HTTPException(status_code=404, detail="Khong tim thay dong doi.")
        partners.append({
            "player_id": partner.id,
            "name": partner_user.full_name,
            "phone": partner_user.phone,
            "email": partner_user.email,
        })

    reg = crud_registration.register_with_otp_flow(
        db=db,
        tournament_id=tournament_id,
        category_id=payload.category_id,
        player_id=payload.player_id,
        notes=payload.notes,
        partners=partners,
    )

    if payload.mark_paid or payload.check_in:
        reg.payment_status = "paid"
    if payload.check_in:
        reg.status = "checked_in"
    db.commit()
    db.refresh(reg)

    background_tasks.add_task(update_qr, reg.id, tournament.name)
    return {"message": "Da them van dong vien vao giai dau thanh cong.", "registration_id": reg.id}

@router.delete("/{registration_id}", dependencies=[Depends(get_current_admin)])
def admin_cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = crud_registration.admin_cancel_registration(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn.")
    return {"message": "Đã hủy đơn và cập nhật trạng thái hoàn tiền."}

@router.delete("/{registration_id}/delete", dependencies=[Depends(get_current_admin)])
def admin_delete_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = crud_registration.admin_delete_registration(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn.")
    return {"message": "Đã xóa đăng ký khỏi danh sách thành công."}

@router.put("/{registration_id}/change-category", dependencies=[Depends(get_current_admin)])
def admin_change_registration_category(
    registration_id: int,
    payload: registration_schemas.AdminChangeCategoryRequest,
    db: Session = Depends(get_db)
):
    reg = crud_registration.admin_change_registration_category(
        db=db,
        registration_id=registration_id,
        category_id=payload.category_id,
        partner_player_id=payload.partner_player_id
    )
    return {"message": "Đã thay đổi nội dung thi đấu thành công.", "registration_id": reg.id}

# 7. ADMIN QUÉT QR CHECK-IN
@router.post("/{registration_id}/check-in", dependencies=[Depends(get_current_admin)])
def admin_check_in(registration_id: int, db: Session = Depends(get_db)):
    reg, info = crud_registration.admin_check_in_registration(db, registration_id)
    
    if info == "not_found":
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
    
    return {
        "status": info["status"],
        "registration_id": reg.id,
        "player_name": info["user"].full_name,
        "tournament_name": info["tourn"].name,
        "location": info["tourn"].location,
        "entry_fee": info["entry_fee"]
    }

# 8. ADMIN THU TIỀN MẶT & CHECK-IN TẠI CHỖ
@router.post("/{registration_id}/pay-and-check-in")
def admin_pay_and_check_in(
    registration_id: int,
    notes: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
        
    tourn = db.query(Tournament).filter(Tournament.id == reg.tournament_id).first()
    player = db.query(Player).filter(Player.id == reg.player_id).first()
    user = db.query(User).filter(User.id == player.user_id).first()

    try:
        # 1. Tạo bản ghi Thanh toán Tiền mặt
        new_payment = Payment(
            registration_id=reg.id,
            amount=(tourn.entry_fee_team if reg.registrant_type == "team" else tourn.entry_fee) if tourn else 0,
            currency="VND",
            payment_method="cash_onsite",
            status="completed",
            transaction_ref=f"CASH-ADM{current_admin.id}-{int(datetime.utcnow().timestamp())}",
            paid_at=datetime.utcnow(),
            notes=notes
        )
        db.add(new_payment)
        
        # 2. Cập nhật Đăng ký
        reg.payment_status = "paid"
        reg.status = "checked_in"
        reg.notes = (reg.notes or "") + f" | Admin {current_admin.full_name} thu tiền mặt & Check-in lúc {datetime.utcnow()}"
        if notes:
            reg.notes += f" (Ghi chú: {notes})"
        
        db.commit()
        
        return {
            "message": "Đã thu tiền và check-in thành công!",
            "player_name": user.full_name,
            "amount": float(tourn.entry_fee) if tourn and tourn.entry_fee else 0
        }
    except Exception:
        db.rollback()
        logger.exception("Admin pay-and-check-in failed")
        raise HTTPException(status_code=500, detail=INTERNAL_ERROR_MESSAGE)

@router.post("/{registration_id}/confirm", dependencies=[Depends(get_current_admin)])
def admin_confirm_registration(
    registration_id: int, 
    background_tasks: BackgroundTasks, # 1. Thêm BackgroundTasks vào đây
    db: Session = Depends(get_db)
):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
    
    reg.status = "confirmed"
    reg.payment_status = "paid"
    reg.approved_at = datetime.utcnow()
    
    # 2. Lấy tên giải đấu để in lên QR Code
    tourn = db.query(Tournament).filter(Tournament.id == reg.tournament_id).first()
    tourn_name = tourn.name if tourn else "Saigontennistours"

    # 3. Kích hoạt chạy ngầm tạo QR Code
    background_tasks.add_task(update_qr, reg.id, tourn_name)
    
    db.commit()
    return {"message": "Đã duyệt vận động viên và tạo mã QR thành công!"}

@router.post("/{registration_id}/lock", dependencies=[Depends(get_current_admin)])
def lock_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = crud_registration.lock_registration(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
    return {"message": "Đã khóa vận động viên khỏi giải đấu thành công.", "is_locked": reg.is_locked}

@router.post("/{registration_id}/unlock", dependencies=[Depends(get_current_admin)])
def unlock_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = crud_registration.unlock_registration(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
    return {"message": "Đã mở khóa vận động viên thành công.", "is_locked": reg.is_locked}
