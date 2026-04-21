from sqlalchemy.orm import Session, aliased
from app.models.models import MatchChallenge, Player, User, Payment
from app.schemas.challenge_schemas import ChallengeCreate
from datetime import datetime

def create_challenge(db: Session, challenger_id: int, obj_in: ChallengeCreate):
    new_challenge = MatchChallenge(
        challenger_id=challenger_id,
        challenged_id=obj_in.challenged_id,
        proposed_date=obj_in.proposed_date,
        notes=obj_in.notes,
        status="pending",
        fee_amount=200000 
    )
    db.add(new_challenge)
    db.commit()
    db.refresh(new_challenge)
    return new_challenge

def get_challenges_by_user(db: Session, player_id: int):
    C_Player = aliased(Player)
    C_User = aliased(User)
    D_Player = aliased(Player)
    D_User = aliased(User)

    query = db.query(
        MatchChallenge,
        C_User.full_name.label("c_name"), C_User.phone.label("c_phone"), C_User.avatar_url.label("c_ava"),
        D_User.full_name.label("d_name"), D_User.phone.label("d_phone"), D_User.avatar_url.label("d_ava")
    ).join(C_Player, MatchChallenge.challenger_id == C_Player.id)\
     .join(C_User, C_Player.user_id == C_User.id)\
     .join(D_Player, MatchChallenge.challenged_id == D_Player.id)\
     .join(D_User, D_Player.user_id == D_User.id)\
     .filter((MatchChallenge.challenger_id == player_id) | (MatchChallenge.challenged_id == player_id))
    
    results = []
    for row in query.all():
        chal, c_n, c_p, c_a, d_n, d_p, d_a = row
        is_me_challenger = chal.challenger_id == player_id
        results.append({
            "id": chal.id,
            "challenger_id": chal.challenger_id,
            "challenged_id": chal.challenged_id,
            "proposed_date": chal.proposed_date.isoformat(),
            "status": chal.status,
            "opponent_name": d_n if is_me_challenger else c_n,
            "opponent_phone": d_p if is_me_challenger else c_p,
            "opponent_avatar": d_a if is_me_challenger else c_a,
            "notes": chal.notes
        })
    return results

# HÀM QUAN TRỌNG ĐANG THIẾU ĐÂY:
def confirm_challenge_payment(db: Session, challenge_id: int):
    challenge = db.query(MatchChallenge).filter(MatchChallenge.id == challenge_id).first()
    if challenge:
        challenge.status = "paid"
        new_pay = Payment(
            challenge_id=challenge.id,
            amount=challenge.fee_amount,
            currency="VND",
            payment_method="VNPAY",
            status="completed",
            paid_at=datetime.utcnow(),
            transaction_ref=f"CHALLENGE_{challenge_id}_{datetime.utcnow().timestamp()}"
        )
        db.add(new_pay)
        db.commit()
        db.refresh(challenge)
        return challenge
    return None

def update_challenge_status(db: Session, challenge_id: int, status: str):
    challenge = db.query(MatchChallenge).filter(MatchChallenge.id == challenge_id).first()
    if challenge:
        challenge.status = status
        db.commit()
    return challenge