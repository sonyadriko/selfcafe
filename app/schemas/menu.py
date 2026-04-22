from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MenuBase(BaseModel):
    name: str
    description: str | None = None
    price: Decimal = Field(gt=0)
    category_id: int
    stock: int = 0
    is_active: bool = True

class MenuCreate(MenuBase):
    image_url: str | None = None

class MenuUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    category_id: int | None = None
    stock: int | None = None
    is_active: bool | None = None
    image_url: str | None = None

class MenuResponse(MenuBase):
    id: int
    image_url: str | None
    created_at: datetime
    category: CategoryResponse | None = None

    class Config:
        from_attributes = True
