# backend/app/api/registrations.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db, SessionLocal
from app.api.deps import get_current_user, get_current_admin
from app.models.models import User
from app.crud import crud_registration, crud_player # Import crud_player
from app.schemas import registration_schemas
from app.core.qr_generator import generate_registration_qr

router = APIRouter()

# --- BACKGROUND TASK ---
def update_qr(r_id: int, t_name: str):
    db_task = SessionLocal()
    try:
        url = generate_registration_qr(r_id, t_name)
        crud_registration.update_registration_qr_url(db_task, r_id, url)
    except Exception as e:
        print(f"❌ [Background Error] Lỗi khi tạo QR Code: {str(e)}")
    finally:
        db_task.close()

# 1. VĐV ĐĂNG KÝ GIẢI ĐẤU
@router.post("/", response_model=registration_schemas.RegistrationResponse)
def register_for_tournament(
    reg_in: registration_schemas.RegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ Vận động viên của bạn.")

    return crud_registration.register_tournament(db=db, reg_in=reg_in, current_player_id=player.id)

# 2. VĐV XEM CÁC GIẢI MÌNH ĐÃ ĐĂNG KÝ
@router.get("/my-registrations", response_model=List[registration_schemas.RegistrationResponse])
def get_my_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player:
        return []
        
    registrations_data = crud_registration.get_registrations_by_player(db, player.id)
    
    response_items = []
    for reg, tourn in registrations_data:
        item = registration_schemas.RegistrationResponse.model_validate(reg)
        item.tournament_name = tourn.name
        item.location = tourn.location
        item.category_type = tourn.category_type
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

# 4. GIẢ LẬP THANH TOÁN THÀNH CÔNG
@router.post("/{registration_id}/confirm-payment")
def confirm_payment(
    registration_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reg, tourn = crud_registration.confirm_simulated_payment(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Đơn đăng ký không tồn tại.")
    if not tourn: # Đã trả về None từ tuple nếu đã payment
        return {"message": "Đơn này đã thanh toán rồi."}

    # Sinh mã QR chạy ngầm...
    background_tasks.add_task(update_qr, reg.id, tourn.name if tourn else "Saigon Tennis")
    
    return {"message": "Thanh toán thành công. Đã lưu Payment & Sinh mã QR."}

# 5. ADMIN XEM TẤT CẢ ĐƠN ĐĂNG KÝ
@router.get("/", response_model=List[registration_schemas.RegistrationResponse])
def admin_get_all_registrations(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    results = crud_registration.get_all_registrations_admin(db)
    
    response_items = []
    for reg, tourn, player, user in results:
        item = registration_schemas.RegistrationResponse.model_validate(reg)
        item.tournament_name = tourn.name
        item.location = tourn.location
        item.player_name = user.full_name
        item.tournament_date = tourn.start_date
        item.category_type = tourn.category_type
        item.entry_fee = float(tourn.entry_fee) if tourn.entry_fee else 0
        item.player_phone = user.phone
        item.player_email = user.email
        item.player_skill = player.skill_level
        response_items.append(item)
        
    return response_items

# 6. ADMIN HỦY ĐƠN / HOÀN TIỀN
@router.delete("/{registration_id}", dependencies=[Depends(get_current_admin)])
def admin_cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = crud_registration.admin_cancel_registration(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn.")
    return {"message": "Đã hủy đơn và cập nhật trạng thái hoàn tiền."}

# 7. ADMIN QUÉT QR CHECK-IN
@router.post("/{registration_id}/check-in", dependencies=[Depends(get_current_admin)])
def admin_check_in(registration_id: int, db: Session = Depends(get_db)):
    reg, info = crud_registration.admin_check_in_registration(db, registration_id)
    
    if info == "not_found":
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký.")
    if info == "not_paid":
        raise HTTPException(status_code=400, detail="Đơn này chưa thanh toán, không thể check-in.")
    
    return {
        "message": "Vận động viên đã check-in thành công!", 
        "player_id": reg.player_id,
        "player_name": info["user"].full_name,
        "tournament_name": info["tourn"].name,
        "location": info["tourn"].location
    }