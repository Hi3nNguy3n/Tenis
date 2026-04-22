# backend/app/crud/crud_court.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.models.models import Court
from app.schemas.court_schemas import CourtCreate, CourtUpdate
from fastapi import HTTPException

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
    # Chuẩn hóa dữ liệu: Xóa khoảng trắng thừa 2 đầu
    c_name = court.court_name.strip()
    l_name = court.location_name.strip()

    # KIỂM TRA TRÙNG LẶP: Cùng tên sân & cùng địa điểm
    existing_court = db.query(Court).filter(
        Court.court_name.ilike(c_name), # Dùng ilike để không phân biệt hoa thường
        Court.location_name.ilike(l_name)
    ).first()

    if existing_court:
        raise HTTPException(status_code=400, detail=f"Sân '{c_name}' tại '{l_name}' đã tồn tại trong hệ thống!")

    # Gán lại dữ liệu đã chuẩn hóa
    court.court_name = c_name
    court.location_name = l_name

    db_court = Court(**court.model_dump())
    db.add(db_court)
    db.commit()
    db.refresh(db_court)
    return db_court

def update_court(db: Session, court_id: int, court_update: CourtUpdate):
    db_court = db.query(Court).filter(Court.id == court_id).first()
    if not db_court:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thi đấu")
    
    # Lấy dữ liệu mới (nếu có gửi lên), nếu không thì dùng dữ liệu cũ
    new_c_name = court_update.court_name.strip() if court_update.court_name else db_court.court_name
    new_l_name = court_update.location_name.strip() if court_update.location_name else db_court.location_name

    # KIỂM TRA TRÙNG LẶP (Loại trừ chính nó)
    existing_court = db.query(Court).filter(
        Court.court_name.ilike(new_c_name),
        Court.location_name.ilike(new_l_name),
        Court.id != court_id
    ).first()

    if existing_court:
        raise HTTPException(status_code=400, detail=f"Sân '{new_c_name}' tại '{new_l_name}' đã bị trùng với một sân khác!")
    
    update_data = court_update.model_dump(exclude_unset=True)
    
    # Cập nhật lại chuỗi đã xóa khoảng trắng vào dict update
    if 'court_name' in update_data: update_data['court_name'] = new_c_name
    if 'location_name' in update_data: update_data['location_name'] = new_l_name

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