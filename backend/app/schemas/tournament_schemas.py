# backend/app/schemas/tournament_schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class TournamentCategoryBase(BaseModel):
    name: str = Field(..., example="Đôi Nam 1275")
    category_type: str = Field(..., example="mens_doubles")
    max_points: Optional[int] = Field(None, example=1275)
    max_participants: Optional[int] = Field(None, example=32)

class TournamentCategoryCreate(TournamentCategoryBase):
    pass

class TournamentCategoryResponse(TournamentCategoryBase):
    id: int
    tournament_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    description: Optional[str] = None

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
    description: Optional[str] = None

class TournamentResponse(TournamentBase):
    id: int
    version: int
    current_participants: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    categories: List[TournamentCategoryResponse] = []

    class Config:
        from_attributes = True

class AnnouncementRequest(BaseModel):
    subject: str
    message: str
    scheduled_at: Optional[datetime] = None

class GenerateDrawRequest(BaseModel):
    category_id: int
    format_type: str = "knockout" # Hoặc "round_robin"
    num_groups: int = 1           # Số bảng đấu
    draw_size: Optional[int] = None # Kích thước nhánh đấu (8, 16, 32...)
    round_names: Optional[List[str]] = None
    
class AssignMatchPlayersRequest(BaseModel):
    side_a_registration_id: Optional[int] = None
    side_b_registration_id: Optional[int] = None

class MatchScheduleUpdate(BaseModel):
    court_id: int
    start_time: datetime
    referee_id: Optional[int] = None
    referee_name: Optional[str] = None
    referee_phone: Optional[str] = None

class MatchScoreUpdate(BaseModel):
    score: str        
    winner_side: str  
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    referee_id: Optional[int] = None
    referee_name: Optional[str] = None
    referee_phone: Optional[str] = None

class ManualMatchCreate(BaseModel):
    category_id: Optional[int] = None
    stage_type: str = "knockout"
    round_code: str = "Vong moi"
    match_no: Optional[int] = None
    side_a_registration_id: Optional[int] = None
    side_b_registration_id: Optional[int] = None
    status: str = "pending"
    court_id: Optional[int] = None
    start_time: Optional[datetime] = None
    referee_name: Optional[str] = None
    referee_phone: Optional[str] = None
    live_stream_url: Optional[str] = None
    next_match_id: Optional[int] = None
    source_match_ids: Optional[List[int]] = None

class AdminMatchUpdate(BaseModel):
    round_code: Optional[str] = None
    match_no: Optional[int] = None
    stage_type: Optional[str] = None
    side_a_registration_id: Optional[int] = None
    side_b_registration_id: Optional[int] = None
    status: Optional[str] = None
    score: Optional[str] = None
    winner_side: Optional[str] = None
    court_id: Optional[int] = None
    start_time: Optional[datetime] = None
    referee_name: Optional[str] = None
    referee_phone: Optional[str] = None
    live_stream_url: Optional[str] = None
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    next_match_id: Optional[int] = None
    advance_note: Optional[str] = None

class PlayoffRequest(BaseModel):
    category_id: int
    advancers_per_group: int = 2 # Mặc định lấy Top 2 mỗi bảng

class ValidateRegistrationRequest(BaseModel):
    category_id: int
    partner_player_id: Optional[int] = None
    partner_name: Optional[str] = None

class TournamentRegisterRequest(BaseModel):
    category_id: int
    notes: Optional[str] = None
    partners: List[dict] = []
    otp: str
