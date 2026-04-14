# backend/app/crud/crud_tournament.py
from sqlalchemy.orm import Session
from app.models.models import Tournament
from app.schemas.tournament_schemas import TournamentCreate, TournamentUpdate

def create_tournament(db: Session, tournament: TournamentCreate):
    # Dùng model_dump() để truyền nhanh toàn bộ dữ liệu hợp lệ
    db_tournament = Tournament(**tournament.model_dump())
    db.add(db_tournament)
    db.commit()
    db.refresh(db_tournament)
    return db_tournament

def get_tournaments(db: Session, skip: int = 0, limit: int = 10, status: str = None):
    query = db.query(Tournament)
    if status:
        query = query.filter(Tournament.status == status)
    return query.offset(skip).limit(limit).all()

def get_tournament(db: Session, tournament_id: int):
    return db.query(Tournament).filter(Tournament.id == tournament_id).first()

def update_tournament(db: Session, db_tournament: Tournament, tournament_update: TournamentUpdate):
    update_data = tournament_update.model_dump(exclude_unset=True) 
    for key, value in update_data.items():
        setattr(db_tournament, key, value)
    
    db.commit()
    db.refresh(db_tournament)
    return db_tournament