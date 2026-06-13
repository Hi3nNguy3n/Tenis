from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import crud_challenge, crud_player
from app.schemas.challenge_schemas import ChallengeCreate, ChallengeUpdateStatus

from app.db.database import get_db 
from app.models.models import MatchChallenge, Player, User

router = APIRouter()

@router.post("", include_in_schema=False)
@router.post("/")
def send_challenge(
    obj_in: ChallengeCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    # 1. BẢO MẬT: Chặn Admin không được phép đi thách đấu
    if hasattr(current_user, 'role') and current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Tài khoản Admin không được phép tham gia sự kiện này!")

    player = crud_player.get_player_by_user_id(db, current_user.id)
    if not player: raise HTTPException(status_code=404, detail="Bạn chưa có hồ sơ VĐV")
    
    # 2. FIX BUG TESTER: Chặn thách đấu chính mình (Trả về lỗi 400)
    if player.id == obj_in.challenged_id:
        raise HTTPException(status_code=400, detail="Lỗi: Bạn không thể tự gửi lời mời thách đấu cho chính mình!")

    return crud_challenge.create_challenge(db, player.id, obj_in)

@router.get("/my-challenges")
def my_challenges(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    player = crud_player.get_player_by_user_id(db, current_user.id)
    return crud_challenge.get_challenges_by_user(db, player.id)

@router.patch("/{challenge_id}/respond")
def respond_challenge(
    challenge_id: int,
    data: ChallengeUpdateStatus,
    db: Session = Depends(deps.get_db)
):
    # SỬA TẠI ĐÂY: Bỏ 'waiting_payment', chuyển thẳng sang 'accepted'
    new_status = "accepted" if data.status == "accepted" else "rejected"
    return crud_challenge.update_challenge_status(db, challenge_id, new_status)

@router.get("/admin/pending-approvals")
def get_paid_challenges(db: Session = Depends(get_db)):
    # Lấy các kèo trạng thái 'paid' kèm thông tin VĐV để Admin gán sân
    # Hàm này tôi bốc tên ra luôn để Frontend hiển thị cho dễ
    challenges = db.query(MatchChallenge).filter(MatchChallenge.status == "accepted").all()
    
    results = []
    for c in challenges:
        # Tìm tên người thách
        p1 = db.query(User).join(Player).filter(Player.id == c.challenger_id).first()
        # Tìm tên người bị thách
        p2 = db.query(User).join(Player).filter(Player.id == c.challenged_id).first()
        
        # Tìm tên đồng đội của người thách (đấu đôi)
        p1_partner = None
        if c.challenger_partner_id:
            p1_partner = db.query(User).join(Player).filter(Player.id == c.challenger_partner_id).first()
            
        # Tìm tên đồng đội của người bị thách (đấu đôi)
        p2_partner = None
        if c.challenged_partner_id:
            p2_partner = db.query(User).join(Player).filter(Player.id == c.challenged_partner_id).first()
        
        c_display = f"{p1.full_name} & {p1_partner.full_name}" if p1 and p1_partner else (p1.full_name if p1 else "VĐV A")
        d_display = f"{p2.full_name} & {p2_partner.full_name}" if p2 and p2_partner else (p2.full_name if p2 else "VĐV B")
        
        results.append({
            "id": c.id,
            "challenger_name": c_display,
            "challenged_name": d_display,
            "side_a_id": c.challenger_id,
            "side_b_id": c.challenged_id,
            "side_a2_id": c.challenger_partner_id,
            "side_b2_id": c.challenged_partner_id,
            "match_type": c.match_type or "singles",
            "proposed_date": c.proposed_date.isoformat(),
            "notes": c.notes,
            "match_name": f"Kèo Thách Đấu: {c_display} vs {d_display}"
        })
    return results
