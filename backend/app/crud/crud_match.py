# backend/app/crud/crud_match.py
from sqlalchemy.orm import Session
from app.models.models import Match, Tournament, Court

def get_list_matches(db: Session, tournament_id: int = None):
    """
    Truy vấn danh sách trận đấu, join với Tournament và Court để lấy tên cụ thể.
    """
    query = db.query(Match, Tournament, Court).outerjoin(
        Tournament, Match.tournament_id == Tournament.id
    ).outerjoin(
        Court, Match.court_id == Court.id
    )
    
    if tournament_id:
        query = query.filter(Match.tournament_id == tournament_id)
        
    return query.all()