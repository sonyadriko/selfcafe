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
    tracking_token: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderTrackingResponse(BaseModel):
    """Response for order tracking by token."""
    id: int
    table_number: int
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class CashierScanRequest(BaseModel):
    """Request for cashier to scan/retrieve order."""
    tracking_token: str


class CashierScanResponse(BaseModel):
    """Response for cashier scan with order details."""
    order_id: int
    table_number: int
    total_amount: Decimal
    status: OrderStatus
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
