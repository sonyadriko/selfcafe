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


def get_best_sellers_data(db: Session, start_date: date, end_date: date) -> list:
    """Query top 10 best selling menu items for date range."""

    # Join order_items with menus and orders, filter by date and status
    results = db.query(
        Menu.name.label("menu_name"),
        Category.name.label("category_name"),
        func.sum(OrderItem.quantity).label("quantity_sold"),
        func.sum(OrderItem.subtotal).label("total_revenue")
    ).join(
        OrderItem, Menu.id == OrderItem.menu_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Category, Menu.category_id == Category.id
    ).filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED])
    ).group_by(
        Menu.id, Menu.name, Category.name
    ).order_by(
        desc("quantity_sold")
    ).limit(10).all()

    # Format results with rank
    best_sellers = []
    for rank, row in enumerate(results, start=1):
        best_sellers.append({
            "rank": rank,
            "menu_name": row.menu_name,
            "category_name": row.category_name,
            "quantity_sold": int(row.quantity_sold),
            "total_revenue": row.total_revenue
        })

    return best_sellers


@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    tab: Optional[str] = Query("daily-sales"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reports page with daily sales and best sellers."""

    # Default to today if no dates provided
    if not start or not end:
        today = date.today()
        start_date = today
        end_date = today
    else:
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except ValueError:
            # Invalid date format, default to today
            today = date.today()
            start_date = today
            end_date = today

    # Validate date range
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Max 90 days range
    if (end_date - start_date).days > 90:
        end_date = start_date + timedelta(days=90)

    # Get data based on active tab
    daily_sales = None
    best_sellers = None

    if tab == "daily-sales":
        daily_sales = get_daily_sales_data(db, start_date, end_date)
    elif tab == "best-sellers":
        best_sellers = get_best_sellers_data(db, start_date, end_date)

    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "active_tab": tab,
        "daily_sales": daily_sales,
        "best_sellers": best_sellers
    })
