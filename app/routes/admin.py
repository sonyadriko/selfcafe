from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, date
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.menu import Menu
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()

    today = date.today()
    today_orders = db.query(Order).filter(
        func.date(Order.created_at) == today
    ).all()
    today_count = len(today_orders)

    menus = db.query(Menu).filter(Menu.is_active == True).count()

    revenue = sum(o.total_amount for o in today_orders if o.status in [OrderStatus.PAID, OrderStatus.COMPLETED])

    recent_orders = db.query(Order).order_by(desc(Order.created_at)).limit(10).all()

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": {
            "pending": pending,
            "today": today_count,
            "menus": menus,
            "revenue": int(revenue) if revenue else 0
        },
        "recent_orders": recent_orders
    })

@router.get("/orders", response_class=HTMLResponse)
async def orders_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).order_by(desc(Order.created_at)).all()
    return templates.TemplateResponse("admin/orders.html", {
        "request": request,
        "orders": orders
    })

from pydantic import BaseModel


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    update_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = update_data.status
    db.commit()

    return {"success": True, "order_id": order_id, "status": update_data.status.value}

@router.get("/menus", response_class=HTMLResponse)
async def menus_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    menus = db.query(Menu).order_by(Menu.category_id).all()
    return templates.TemplateResponse("admin/menus.html", {
        "request": request,
        "menus": menus
    })
