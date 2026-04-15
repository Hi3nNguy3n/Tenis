# backend/app/crud/crud_court.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.models.models import Court
from app.schemas.court_schemas import CourtCreate, CourtUpdate

def get_courts(
    db: Session, 
    search: Optional[str] = None, 
    status: Optional[str] = None, 
    skip: int = 0, 
    limit: int = 100
):
    query = db.query(Court)
    if search:
        query = query.filter(or_(
            Court.court_name.ilike(f"%{search}%"),
            Court.location_name.ilike(f"%{search}%")
        ))
    if status:
        if status == 'AVAILABLE':
            query = query.filter(Court.is_active == True)
        elif status == 'UNAVAILABLE':
            query = query.filter(Court.is_active == False)
            
    return query.offset(skip).limit(limit).all()

def create_court(db: Session, court: CourtCreate):
    db_court = Court(**court.model_dump())
    db.add(db_court)
    db.commit()
    db.refresh(db_court)
    return db_court

def update_court(db: Session, court_id: int, court_update: CourtUpdate):
    db_court = db.query(Court).filter(Court.id == court_id).first()
    if not db_court:
        return None
    
    update_data = court_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_court, key, value)
    
    db.commit()
    db.refresh(db_court)
    return db_court

def delete_court(db: Session, court_id: int):
    db_court = db.query(Court).filter(Court.id == court_id).first()
    if db_court:
        db.delete(db_court)
        db.commit()
    return db_court