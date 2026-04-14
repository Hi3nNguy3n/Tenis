# backend/app/schemas/player_schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PlayerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=15)
    gender: Optional[str] = Field(None, description="nam, nu, khac")
    date_of_birth: Optional[date] = None