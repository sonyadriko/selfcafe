from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List
from app.models.order import OrderStatus

class OrderItemBase(BaseModel):
    menu_id: int
    quantity: int = Field(gt=0)
    notes: str | None = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    subtotal: Decimal
    menu_name: str | None = None
    menu_price: Decimal | None = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    table_number: int = Field(gt=0)

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: OrderStatus

class OrderResponse(OrderBase):
    id: int
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
