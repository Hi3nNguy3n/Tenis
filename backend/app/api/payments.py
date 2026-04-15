# backend/app/api/payments.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

# ĐÃ IMPORT SessionLocal
from app.db.database import get_db, SessionLocal 
from app.models.models import User
from app.api.deps import get_current_user
from app.core.audit import audit_log
from app.crud import crud_payment

# ĐÃ IMPORT hàm tạo QR
from app.core.qr_generator import generate_registration_qr

router = APIRouter()

@router.post("/{registration_id}/create-url")
def create_payment_url(
    registration_id: int, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reg = crud_payment.get_registration_by_id(db, registration_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký")
    
    if reg.payment_status == "paid":
        raise HTTPException(status_code=400, detail="Đơn này đã thanh toán rồi")

    mock_payment_url = f"http://localhost:5173/payment-gateway?regId={registration_id}&amount=500000"
    return {"payment_url": mock_payment_url}

# TÁCH HÀM BACKGROUND TASK RA NGOÀI ĐỂ CODE GỌN GÀNG
def process_qr_background(r_id: int, t_name: str):
    db_task = SessionLocal() # Khởi tạo session độc lập
    try:
        url = generate_registration_qr(r_id, t_name)
        reg = crud_payment.get_registration_by_id(db_task, r_id)
        if reg:
            reg.qr_code_url = url
            db_task.commit()
    except Exception as e:
        print(f"Lỗi tạo QR Code: {e}")
    finally:
        db_task.close() # Luôn đóng session ngầm

@router.get("/vnpay-callback")
@audit_log(module="PAYMENT", action="UPDATE", event_name="Xác nhận thanh toán từ VNPay")
async def vnpay_callback(
    regId: int, 
    status: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    reg = crud_payment.get_registration_by_id(db, regId)
    if not reg:
        raise HTTPException(status_code=404, detail="Order not found")

    if status == "success":
        # REFACTORED: Gọi 1 dòng duy nhất xử lý cả DB và Transaction
        crud_payment.confirm_payment_transaction(db, reg)
        
        # Gọi background task an toàn
        background_tasks.add_task(process_qr_background, reg.id, "Saigon Tennis")
        
        return {"message": "Payment confirmed and QR code generating"}
    
    return {"message": "Payment failed or pending"}

@router.get("/list")
def list_payments(db: Session = Depends(get_db)):
    return crud_payment.get_all_payments(db)