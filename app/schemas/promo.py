from pydantic import BaseModel, Field
from datetime import datetime

class PromoBase(BaseModel):
    name: str
    discount_type: str  # 'percentage' or 'fixed'
    discount_value: int = Field(gt=0)
    min_purchase: int = 0

class PromoCreate(PromoBase):
    start_date: datetime | None = None
    end_date: datetime | None = None

class PromoUpdate(BaseModel):
    name: str | None = None
    discount_type: str | None = None
    discount_value: int | None = None
    min_purchase: int | None = None
    is_active: bool | None = None

class PromoResponse(PromoBase):
    id: int
    is_active: bool
    start_date: datetime | None
    end_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
