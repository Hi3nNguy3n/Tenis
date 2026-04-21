# backend/app/crud/crud_payment.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from app.models.models import Registration, Payment, Tournament, Player, User
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

def get_all_payments_with_details(db: Session, tournament_id: int = None, search: str = None):
    query = db.query(Payment, Registration, Tournament, User).outerjoin(
        Registration, Payment.registration_id == Registration.id
    ).outerjoin(
        Tournament, Registration.tournament_id == Tournament.id
    ).outerjoin(
        Player, Registration.player_id == Player.id
    ).outerjoin(
        User, Player.user_id == User.id
    )
    
    if tournament_id == 0:
        # Lọc riêng các khoản thanh toán cho trận Giao hữu (nếu có sau này)
        query = query.filter(Registration.tournament_id.is_(None))
    elif tournament_id:
        query = query.filter(Registration.tournament_id == tournament_id)
        
    if search:
        search_str = f"%{search.lower()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_str),
                Payment.transaction_ref.ilike(search_str)
            )
        )
        
    return query.order_by(Payment.paid_at.desc()).all()