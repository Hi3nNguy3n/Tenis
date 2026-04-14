# backend/app/crud/crud_player.py
from sqlalchemy.orm import Session
from app.models.models import Player

def get_player_by_user_id(db: Session, user_id: int):
    return db.query(Player).filter(Player.user_id == user_id).first()