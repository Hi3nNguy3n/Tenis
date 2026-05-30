# backend/app/schemas/player_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
# backend/app/schemas/player_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PlayerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=15)
    gender: Optional[str] = Field(None, description="male, female, other")
    date_of_birth: Optional[date] = None
    admin_notes: Optional[str] = None
    province: Optional[str] = None       # Thêm trường này
    play_hand: Optional[str] = Field(None, description="right, left, both")
    skill_level: Optional[str] = None
    preferred_category: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=3000)
    height_cm: Optional[int] = Field(None, ge=80, le=250)
    weight_kg: Optional[int] = Field(None, ge=25, le=250)
    aces: Optional[int] = Field(None, ge=0)
    double_faults: Optional[int] = Field(None, ge=0)
    first_serve_pct: Optional[float] = Field(None, ge=0, le=100)
    first_serve_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    second_serve_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    break_points_faced: Optional[int] = Field(None, ge=0)
    break_points_saved_pct: Optional[float] = Field(None, ge=0, le=100)
    service_games_played: Optional[int] = Field(None, ge=0)
    service_games_won_pct: Optional[float] = Field(None, ge=0, le=100)
    total_service_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    first_serve_return_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    second_serve_return_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    break_points_opportunities: Optional[int] = Field(None, ge=0)
    break_points_converted_pct: Optional[float] = Field(None, ge=0, le=100)
    return_games_played: Optional[int] = Field(None, ge=0)
    return_games_won_pct: Optional[float] = Field(None, ge=0, le=100)
    return_points_won_pct: Optional[float] = Field(None, ge=0, le=100)
    total_points_won_pct: Optional[float] = Field(None, ge=0, le=100)

    avatar_url: Optional[str] = None 
    is_active: Optional[bool] = None
    elo_points: Optional[int] = None
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
    date_of_birth: Optional[date] = None

class PlayerProfileSummary(BaseModel):
    id: int
    rank: Optional[int] = None
    elo_points: int
    wins: int
    losses: int
    matches_played: int
    win_rate: float
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    admin_notes: Optional[str] = None
    play_hand: Optional[str] = None
    skill_level: Optional[str] = None
    preferred_category: Optional[str] = None
    bio: Optional[str] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    aces: int = 0
    double_faults: int = 0
    first_serve_pct: float = 0
    first_serve_points_won_pct: float = 0
    second_serve_points_won_pct: float = 0
    break_points_faced: int = 0
    break_points_saved_pct: float = 0
    service_games_played: int = 0
    service_games_won_pct: float = 0
    total_service_points_won_pct: float = 0
    first_serve_return_points_won_pct: float = 0
    second_serve_return_points_won_pct: float = 0
    break_points_opportunities: int = 0
    break_points_converted_pct: float = 0
    return_games_played: int = 0
    return_games_won_pct: float = 0
    return_points_won_pct: float = 0
    total_points_won_pct: float = 0

class PlayerProfileDetailResponse(BaseModel):
    user: UserSummary
    player_profile: PlayerProfileSummary

    class Config:
        from_attributes = True
