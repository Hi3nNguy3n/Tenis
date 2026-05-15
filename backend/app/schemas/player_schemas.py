# backend/app/schemas/player_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PlayerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=15)
    gender: Optional[str] = Field(None, description="nam, nu, khac")
    date_of_birth: Optional[date] = None
    province: Optional[str] = None       # Thêm trường này
    play_hand: Optional[str] = Field(None, description="right, left, both")
    skill_level: Optional[str] = None
    preferred_category: Optional[str] = None

    avatar_url: Optional[str] = None 
    is_active: Optional[bool] = None
class PlayerPublicResponse(BaseModel):
    id: int                # User ID
    player_id: int         # Player Profile ID
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    level: Optional[str] = None

    class Config:
        from_attributes = True

class UserSummary(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    province: Optional[str] = None

class PlayerProfileSummary(BaseModel):
    id: int
    rank: Optional[int] = None
    elo_points: int
    wins: int
    losses: int
    matches_played: int
    win_rate: float
    gender: Optional[str] = None
    play_hand: Optional[str] = None
    skill_level: Optional[str] = None
    preferred_category: Optional[str] = None

class PlayerProfileDetailResponse(BaseModel):
    user: UserSummary
    player_profile: PlayerProfileSummary

    class Config:
        from_attributes = True