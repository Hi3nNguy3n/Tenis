# backend/app/crud/crud_match.py
from sqlalchemy.orm import Session
from app.models.models import Match, Tournament, Court, TournamentCategory
from fastapi import HTTPException
from datetime import datetime

def get_list_matches(db: Session, tournament_id: int = None, category_id: int = None):
    """
    Truy vấn danh sách trận đấu, join với Tournament, Court và Category để lấy tên cụ thể.
    """
    query = db.query(Match, Tournament, Court, TournamentCategory).outerjoin(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    ).outerjoin(
        TournamentCategory, Match.tournament_category_id == TournamentCategory.id
    )
    
    if tournament_id == 0:
        # Lấy các trận không thuộc giải nào
        query = query.filter(Match.tournament_id.is_(None))
    elif tournament_id is not None:
        # Lấy các trận thuộc giải đấu cụ thể
        query = query.filter(Match.tournament_id == tournament_id)
        
    if category_id is not None:
        query = query.filter(Match.tournament_category_id == category_id)
        
    return query.all()

def create_manual_match(db, match_data):
    """Lưu trận đấu vào CSDL (Hỗ trợ cả đấu giải và giao hữu)"""
    
    if match_data.side_a_id == match_data.side_b_id:
        raise ValueError("VĐV A và VĐV B không được trùng nhau!")

    # === BƯỚC MỚI: GHÉP NGÀY VÀ GIỜ THÀNH TIMESTAMP ===
    final_start_time = None
    if match_data.match_date and match_data.start_time:
        # Nối ngày thi đấu và giờ thi đấu thành 1 biến datetime hoàn chỉnh
        final_start_time = datetime.combine(match_data.match_date, match_data.start_time)

    new_match = Match(
        tournament_id=match_data.tournament_id,
        court_id=match_data.court_id,
        stage_type="exhibition" if not match_data.tournament_id else "manual",
        round_code=match_data.match_name if not match_data.tournament_id else "Exhibition",        
        match_no=1,

        # Nếu là giải đấu, chúng ta vẫn gán side_a_registration_id 
        # CẢNH BÁO: Hiện tại match_data.side_a_id từ frontend gửi về đang là PLAYER ID
        # Chúng ta sẽ lưu nó vào player_a_id/player_b_id để an toàn cho việc tính ELO
        side_a_registration_id=None, # Tạm để None vì ID gửi về là Player ID
        side_b_registration_id=None,
        
        player_a_id=match_data.side_a_id,
        player_b_id=match_data.side_b_id,

        match_date=match_data.match_date,
        
        # === GÁN BIẾN VỪA GHÉP VÀO ĐÂY ===
        start_time=final_start_time, 
        
        best_of_sets=3,
        status="scheduled",
        elo_affected=True # LUÔN BẬT ĐỂ TÍNH ĐIỂM
    )
    
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return new_match

def cancel_match(db: Session, match_id: int):
    """Cập nhật trạng thái trận đấu thành canceled"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Không tìm thấy trận đấu")
    
    match.status = "canceled"
    db.commit()
    db.refresh(match)
    return match