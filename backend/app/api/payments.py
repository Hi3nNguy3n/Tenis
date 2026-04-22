# backend/app/api/payments.py
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime

# ĐÃ IMPORT SessionLocal
from app.db.database import get_db, SessionLocal 
from app.api.deps import get_current_user
from app.core.audit import audit_log
from app.crud import crud_payment

from typing import Optional

# ĐÃ IMPORT hàm tạo QR
from app.core.qr_generator import generate_registration_qr
from app.crud import crud_challenge
from app.models.models import User, MatchChallenge # Thêm MatchChallenge vào đây

router = APIRouter()

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

@audit_log(module="PAYMENT", action="UPDATE", event_name="Xác nhận thanh toán")
def vnpay_callback(
    status: str, 
    regId: Optional[int] = Query(None), # Chuyển thành Optional
    challengeId: Optional[int] = Query(None), # Thêm challengeId
    db: Session = Depends(get_db)
):
    if status != "success":
        return {"message": "Thanh toán thất bại hoặc đã hủy"}

    # LUỒNG 1: Thanh toán Đăng ký giải đấu
    if regId:
        reg = crud_payment.get_registration_by_id(db, regId)
        if not reg: raise HTTPException(status_code=404, detail="Không tìm thấy đơn đăng ký")
        crud_payment.confirm_payment_transaction(db, reg)
        return {"message": "Thanh toán giải đấu thành công"}

    # LUỒNG 2: Thanh toán Kèo thách đấu
    if challengeId:
        challenge = crud_challenge.confirm_challenge_payment(db, challengeId)
        if not challenge: raise HTTPException(status_code=404, detail="Không tìm thấy kèo thách đấu")
        return {"message": "Thanh toán kèo thách đấu thành công"}

    return {"message": "Dữ liệu không hợp lệ"}

@router.get("/list")
def list_payments(
    tournament_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    records = crud_payment.get_all_payments_with_details(db, tournament_id, search)
    results = []
    
    for payment, reg, tour, user in records:
        results.append({
            "id": payment.id,
            "transaction_ref": payment.transaction_ref,
            "registration_id": payment.registration_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
            "payer_name": user.full_name if user else "Khách vãng lai",
            "tournament_name": tour.name if tour else "Phí dịch vụ 1vs1 (Giao hữu)"
        })
        
    return results

@router.post("/challenge/{challenge_id}/create-url")
def create_challenge_payment_url(
    challenge_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # 1. Kiểm tra kèo thách đấu có tồn tại không
    challenge = db.query(MatchChallenge).filter(MatchChallenge.id == challenge_id).first()
    if not challenge:
        raise HTTPException(status_code=404, detail="Không tìm thấy kèo thách đấu")
    
    if challenge.status == "paid":
        raise HTTPException(status_code=400, detail="Kèo này đã được thanh toán")

    # 2. Tạo URL thanh toán (Giả lập giống bên giải đấu của ông)
    # Sau này ông thay bằng logic tạo link VNPay thật nhé
    mock_payment_url = f"http://localhost:5173/profile/challenges/waiting/{challenge_id}"    
    return {"payment_url": mock_payment_url}