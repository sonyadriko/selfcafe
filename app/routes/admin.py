from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
import qrcode
import io
from typing import Optional
from app.config import settings
from sqlalchemy import func, desc
from datetime import datetime, date
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.menu import Menu
from app.models.payment_method import PaymentMethod
from app.dependencies import get_current_user, require_role
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
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
    current_user: User = Depends(require_role("admin"))
):
    orders = db.query(Order).order_by(desc(Order.created_at)).all()
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.is_active == True
    ).order_by(PaymentMethod.name).all()
    return templates.TemplateResponse("admin/orders.html", {
        "request": request,
        "orders": orders,
        "payment_methods": payment_methods
    })

from pydantic import BaseModel, Field
from pydantic import ConfigDict


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra='allow')
    status: OrderStatus
    payment_method: str | None = Field(default=None)


@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    update_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = update_data.status
    if update_data.payment_method:
        order.payment_method = update_data.payment_method

    db.commit()
    db.refresh(order)

    return {"success": True, "order_id": order_id, "status": update_data.status.value}

@router.get("/menus", response_class=HTMLResponse)
async def menus_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    menus = db.query(Menu).order_by(Menu.category_id).all()
    return templates.TemplateResponse("admin/menus.html", {
        "request": request,
        "menus": menus
    })

@router.get("/tables", response_class=HTMLResponse)
async def tables_page(
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    num_tables = settings.NUM_TABLES
    base_url = f"{request.url.scheme}://{request.url.netloc}"

    tables = []
    for i in range(1, num_tables + 1):
        tables.append({
            "number": i,
            "qr_url": f"/admin/qr/table/{i}",
            "customer_url": f"{base_url}/customer?table={i}"
        })

    return templates.TemplateResponse("admin/tables.html", {
        "request": request,
        "tables": tables
    })

@router.get("/payment-methods", response_class=HTMLResponse)
async def payment_methods_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    methods = db.query(PaymentMethod).order_by(PaymentMethod.name).all()
    return templates.TemplateResponse("admin/payment_methods.html", {
        "request": request,
        "methods": methods
    })

class PaymentMethodCreate(BaseModel):
    name: str

@router.post("/payment-methods")
async def create_payment_method(
    data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    existing = db.query(PaymentMethod).filter(PaymentMethod.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Metode pembayaran sudah ada")
    method = PaymentMethod(name=data.name, is_active=True)
    db.add(method)
    db.commit()
    db.refresh(method)
    return {"id": method.id, "name": method.name, "is_active": method.is_active}

@router.put("/payment-methods/{method_id}")
async def update_payment_method(
    method_id: int,
    data: PaymentMethodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Metode tidak ditemukan")
    existing = db.query(PaymentMethod).filter(
        PaymentMethod.name == data.name, PaymentMethod.id != method_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nama sudah digunakan")
    method.name = data.name
    db.commit()
    return {"id": method.id, "name": method.name, "is_active": method.is_active}

@router.put("/payment-methods/{method_id}/toggle")
async def toggle_payment_method(
    method_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Metode tidak ditemukan")
    method.is_active = not method.is_active
    db.commit()
    return {"id": method.id, "is_active": method.is_active}

@router.delete("/payment-methods/{method_id}")
async def delete_payment_method(
    method_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Metode tidak ditemukan")
    db.delete(method)
    db.commit()
    return {"success": True}

@router.get("/qr/table/{table_number}")
async def generate_table_qr(
    table_number: int,
    request: Request,
    current_user: User = Depends(require_role("admin"))
):
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    customer_url = f"{base_url}/customer?table={table_number}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(customer_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
