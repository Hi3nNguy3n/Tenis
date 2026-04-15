# backend/app/crud/crud_payment.py
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.models import Registration, Payment

def get_registration_by_id(db: Session, reg_id: int):
    return db.query(Registration).filter(Registration.id == reg_id).first()

def confirm_payment_transaction(db: Session, reg: Registration):
    """
    Cập nhật trạng thái đăng ký và tạo bản ghi Payment trong 1 transaction
    """
    try:
        reg.status = "confirmed"
        reg.payment_status = "paid"
        reg.approved_at = datetime.utcnow()
        
        new_payment = Payment(
            registration_id=reg.id,
            amount=500000, 
            currency="VND",
            payment_method="VNPAY",
            transaction_ref=f"TXN_{datetime.utcnow().timestamp()}",
            status="completed",
            paid_at=datetime.utcnow()
        )
        db.add(new_payment)
        db.commit()
        db.refresh(new_payment)
        return new_payment
    except Exception as e:
        db.rollback()
        raise e

def get_all_payments(db: Session):
    return db.query(Payment).all()