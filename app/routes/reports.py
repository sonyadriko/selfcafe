from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.menu import Menu, Category
from app.models.order import OrderItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_daily_sales_data(db: Session, start_date: date, end_date: date) -> dict:
    """Query daily sales metrics for date range."""

    # Query orders in date range with paid/completed status
    orders = db.query(Order).filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED])
    ).all()

    if not orders:
        return {
            "total_revenue": Decimal("0.00"),
            "order_count": 0,
            "average_order_value": Decimal("0.00"),
            "date_range": {"start": start_date, "end": end_date}
        }

    total_revenue = sum(order.total_amount for order in orders)
    order_count = len(orders)
    average_order_value = total_revenue / order_count if order_count > 0 else Decimal("0.00")

    return {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "date_range": {"start": start_date, "end": end_date}
    }
