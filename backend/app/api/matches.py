# backend/app/api/matches.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.crud import crud_match # Import CRUD mới tạo

router = APIRouter()

@router.get("/")
def list_matches(
    tournament_id: int = Query(None),
    db: Session = Depends(get_db)
):
    # ĐÃ REFACTOR: Gọi thẳng xuống CRUD để lấy data thô
    match_records = crud_match.get_list_matches(db, tournament_id=tournament_id)
    
    # Giữ nguyên logic ép kiểu thời gian (strftime) để tránh vỡ UI Frontend
    results = []
    for m, t, c in match_records:
        results.append({
            "id": m.id,
            "tournament": t.name if t else "N/A",
            "court": c.court_name if c else "N/A",
            "date": m.match_date.isoformat() if m.match_date else "N/A",
            "start": m.start_time.strftime("%H:%M") if m.start_time else "N/A",
            "end": m.end_time.strftime("%H:%M") if m.end_time else "N/A",
            "status": m.status
        })
    return results