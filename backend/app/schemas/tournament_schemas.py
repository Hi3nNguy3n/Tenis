# backend/app/schemas/tournament_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class TournamentBase(BaseModel):
    name: str = Field(..., example="Saigon Tennis Open 2026")
    slug: str = Field(..., example="saigon-tennis-open-2026")
    category_type: str = Field(..., example="mens_singles")
    gender_division: str = Field(..., example="men")
    format_type: str = Field(..., example="knockout")
    draw_size: int = Field(..., example=64)
    registration_open_at: Optional[datetime] = None
    registration_close_at: Optional[datetime] = None
    start_date: date
    end_date: Optional[date] = None
    status: str = Field(default="draft", example="draft, open, ongoing, finished")
    location: Optional[str] = None
    surface_type: Optional[str] = None
    entry_fee: Optional[float] = None
    entry_fee_team: Optional[float] = None
    max_participants: Optional[int] = None

class TournamentCreate(TournamentBase):
    pass

class TournamentUpdate(BaseModel):
    # Khai báo tất cả là Optional để cho phép update từng phần
    name: Optional[str] = None
    slug: Optional[str] = None
    category_type: Optional[str] = None
    gender_division: Optional[str] = None
    format_type: Optional[str] = None
    draw_size: Optional[int] = None
    registration_open_at: Optional[datetime] = None
    registration_close_at: Optional[datetime] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    location: Optional[str] = None
    surface_type: Optional[str] = None
    entry_fee: Optional[float] = None
    entry_fee_team: Optional[float] = None
    max_participants: Optional[int] = None

class TournamentResponse(TournamentBase):
    id: int
    version: int
    current_participants: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnnouncementRequest(BaseModel):
    subject: str
    message: str
    scheduled_at: Optional[datetime] = None