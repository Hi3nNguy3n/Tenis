from sqlalchemy.orm import Session, aliased
from app.models.models import MatchChallenge, Player, User, Payment
from app.schemas.challenge_schemas import ChallengeCreate
from datetime import datetime

def create_challenge(db: Session, challenger_id: int, obj_in: ChallengeCreate):
    new_challenge = MatchChallenge(
        challenger_id=challenger_id,
        challenged_id=obj_in.challenged_id,
        challenger_partner_id=obj_in.challenger_partner_id,
        challenged_partner_id=obj_in.challenged_partner_id,
        match_type=obj_in.match_type or "singles",
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
    
    CP_Player = aliased(Player)
    CP_User = aliased(User)
    DP_Player = aliased(Player)
    DP_User = aliased(User)

    query = db.query(
        MatchChallenge,
        C_User.full_name.label("c_name"), C_User.phone.label("c_phone"), C_User.avatar_url.label("c_ava"),
        D_User.full_name.label("d_name"), D_User.phone.label("d_phone"), D_User.avatar_url.label("d_ava"),
        CP_User.full_name.label("cp_name"),
        DP_User.full_name.label("dp_name")
    ).join(C_Player, MatchChallenge.challenger_id == C_Player.id)\
     .join(C_User, C_Player.user_id == C_User.id)\
     .join(D_Player, MatchChallenge.challenged_id == D_Player.id)\
     .join(D_User, D_Player.user_id == D_User.id)\
     .outerjoin(CP_Player, MatchChallenge.challenger_partner_id == CP_Player.id)\
     .outerjoin(CP_User, CP_Player.user_id == CP_User.id)\
     .outerjoin(DP_Player, MatchChallenge.challenged_partner_id == DP_Player.id)\
     .outerjoin(DP_User, DP_Player.user_id == DP_User.id)\
     .filter(
         (MatchChallenge.challenger_id == player_id) | 
         (MatchChallenge.challenged_id == player_id) |
         (MatchChallenge.challenger_partner_id == player_id) |
         (MatchChallenge.challenged_partner_id == player_id)
     )
    
    results = []
    for row in query.all():
        chal, c_n, c_p, c_a, d_n, d_p, d_a, cp_n, dp_n = row
        is_me_challenger_side = (chal.challenger_id == player_id) or (chal.challenger_partner_id == player_id)
        
        challenger_display = f"{c_n} & {cp_n}" if cp_n else c_n
        challenged_display = f"{d_n} & {dp_n}" if dp_n else d_n
        
        results.append({
            "id": chal.id,
            "challenger_id": chal.challenger_id,
            "challenged_id": chal.challenged_id,
            "challenger_partner_id": chal.challenger_partner_id,
            "challenged_partner_id": chal.challenged_partner_id,
            "challenger_name": challenger_display,
            "challenged_name": challenged_display,
            "match_type": chal.match_type or "singles",
            "proposed_date": chal.proposed_date.isoformat(),
            "status": chal.status,
            "opponent_name": challenged_display if is_me_challenger_side else challenger_display,
            "opponent_phone": d_p if is_me_challenger_side else c_p,
            "opponent_avatar": d_a if is_me_challenger_side else c_a,
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