from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MarketingBannerBase(BaseModel):
    title: str = Field(..., max_length=200)
    subtitle: Optional[str] = Field(None, max_length=255)
    image_url: str = Field(..., max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    placement: str = Field(default="home_top", max_length=50)
    display_order: int = 0
    is_active: bool = True
    open_in_new_tab: bool = True
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class MarketingBannerCreate(MarketingBannerBase):
    pass


class MarketingBannerUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=255)
    image_url: Optional[str] = Field(None, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    placement: Optional[str] = Field(None, max_length=50)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    open_in_new_tab: Optional[bool] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class MarketingBannerResponse(MarketingBannerBase):
    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SponsorBase(BaseModel):
    name: str = Field(..., max_length=200)
    logo_url: str = Field(..., max_length=500)
    website_url: Optional[str] = Field(None, max_length=500)
    tier: str = Field(default="partner", max_length=50)
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class SponsorCreate(SponsorBase):
    pass


class SponsorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    logo_url: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=500)
    tier: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class SponsorResponse(SponsorBase):
    id: int
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
