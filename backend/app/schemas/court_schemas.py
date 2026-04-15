# backend/app/schemas/court_schemas.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CourtBase(BaseModel):
    court_name: str
    location_name: str
    surface_type: Optional[str] = "HARD"
    is_active: bool = True

class CourtCreate(CourtBase):
    pass

class CourtUpdate(BaseModel):
    court_name: Optional[str] = None
    location_name: Optional[str] = None
    surface_type: Optional[str] = None
    is_active: Optional[bool] = None

class CourtResponse(CourtBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
