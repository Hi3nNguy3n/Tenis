# backend/app/api/registrations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.models import User, Player, Registration
from app.crud import crud_registration
from app.schemas import registration_schemas

from fastapi import BackgroundTasks
from app.core.qr_generator import generate_registration_qr

from datetime import datetime
router = APIRouter()

# 1. VĐV ĐĂNG KÝ GIẢI ĐẤU
@router.post("/", response_model=registration_schemas.RegistrationResponse)
def register_for_tournament(
    reg_in: registration_schemas.RegistrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Tìm hồ sơ Player của User đang đăng nhập
    player = db.query(Player).filter(Player.user_id == current_user.id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Không tìm thấy hồ sơ Vận động viên của bạn.")

    # Gọi hàm xử lý đăng ký
    return crud_registration.register_tournament(db=db, reg_in=reg_in, current_player_id=player.id)


# 2. VĐV XEM CÁC GIẢI MÌNH ĐÃ ĐĂNG KÝ
@router.get("/my-registrations", response_model=List[registration_schemas.RegistrationResponse])
def get_my_registrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    player = db.query(Player).filter(Player.user_id == current_user.id).first()
    if not player:
        return []
        
    registrations = db.query(Registration).filter(
        Registration.player_id == player.id,
        Registration.deleted_at.is_(None)
    ).all()
    
    return registrations

# 3. GIẢ LẬP THANH TOÁN THÀNH CÔNG (Dành cho VĐV)
@router.post("/{registration_id}/confirm-payment")
def confirm_payment(
    registration_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Đơn đăng ký không tồn tại.")
    
    if reg.payment_status == "paid":
        return {"message": "Đơn này đã thanh toán rồi."}

    # Cập nhật trạng thái
    reg.status = "confirmed"
    reg.payment_status = "paid"
    reg.approved_at = datetime.utcnow()

    # Sinh mã QR chạy ngầm (để user không phải đợi lâu)
    def update_qr(r_id: int, t_name: str):
        from app.db.database import SessionLocal
        
        # Mở kết nối Database an toàn
        db_task = SessionLocal()
        try:
            print(f"⏳ [Background] Đang tạo QR Code cho đơn {r_id}...")
            
            # 1. Tạo QR và up lên Cloudinary
            url = generate_registration_qr(r_id, t_name)
            print(f"✅ [Background] Đã up QR lên Cloudinary: {url}")
            
            # 2. Lưu vào Database
            r = db_task.query(Registration).filter(Registration.id == r_id).first()
            if r:
                r.qr_code_url = url # <--- SỬA group_code THÀNH qr_code_url Ở ĐÂY
                db_task.commit()
                print(f"💾 [Background] Đã lưu URL vào DB thành công!")
                
        except Exception as e:
            # NẾU CÓ LỖI, NÓ SẼ IN DÒNG CHỮ ĐỎ NÀY RA TERMINAL
            print(f"❌ [Background Error] Lỗi khi tạo QR Code: {str(e)}")
        finally:
            db_task.close() # Xong việc nhớ đóng kết nối

    background_tasks.add_task(update_qr, reg.id, "Saigon Tennis")
    
    db.commit()
    return {"message": "Thanh toán thành công. Hệ thống đang tạo mã QR cho bạn."}

# 4. ADMIN HỦY ĐƠN / HOÀN TIỀN (CHỈ ADMIN)
@router.delete("/{registration_id}", dependencies=[Depends(get_current_admin)])
def admin_cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn.")
    
    reg.status = "rejected"
    reg.payment_status = "refunded"
    reg.deleted_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Đã hủy đơn và cập nhật trạng thái hoàn tiền."}