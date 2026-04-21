from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import crud_challenge, crud_player
from app.schemas.challenge_schemas import ChallengeCreate, ChallengeUpdateStatus

from app.db.database import get_db 
from app.models.models import MatchChallenge, Player, User

router = APIRouter()

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
    # Nếu chấp nhận thì chuyển sang chờ thanh toán
    new_status = "waiting_payment" if data.status == "accepted" else "rejected"
    return crud_challenge.update_challenge_status(db, challenge_id, new_status)

@router.get("/admin/pending-approvals")
def get_paid_challenges(db: Session = Depends(get_db)):
    # Lấy các kèo trạng thái 'paid' kèm thông tin VĐV để Admin gán sân
    # Hàm này tôi bốc tên ra luôn để Frontend hiển thị cho dễ
    challenges = db.query(MatchChallenge).filter(MatchChallenge.status == "paid").all()
    
    results = []
    for c in challenges:
        # Tìm tên người thách
        p1 = db.query(User).join(Player).filter(Player.id == c.challenger_id).first()
        # Tìm tên người bị thách
        p2 = db.query(User).join(Player).filter(Player.id == c.challenged_id).first()
        
        results.append({
            "id": c.id,
            "challenger_name": p1.full_name if p1 else "VĐV A",
            "challenged_name": p2.full_name if p2 else "VĐV B",
            "side_a_id": c.challenger_id,
            "side_b_id": c.challenged_id,
            "proposed_date": c.proposed_date.isoformat(),
            "notes": c.notes,
            "match_name": f"Kèo Thách Đấu: {p1.full_name if p1 else 'A'} vs {p2.full_name if p2 else 'B'}"
        })
    return results