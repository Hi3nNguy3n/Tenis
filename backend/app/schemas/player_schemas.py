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
    id: int
    full_name: str
    avatar_url: Optional[str] = None
    level: Optional[str] = None # Logic CRUD trên đã đổ skill_level vào đây

    class Config:
        from_attributes = True