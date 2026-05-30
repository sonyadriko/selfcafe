"""
Cashier routes for QR code scanning and payment processing.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.schemas.order import CashierScanRequest, CashierScanResponse, OrderItemResponse
from app.dependencies import get_current_user, require_role
from app.services.tracking import get_order_by_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/cashier", response_class=HTMLResponse)
async def cashier_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    payment_methods = db.query(PaymentMethod).filter(
        PaymentMethod.is_active == True
    ).order_by(PaymentMethod.name).all()
    return templates.TemplateResponse("cashier/dashboard.html", {
        "request": request,
        "user": current_user,
        "payment_methods": payment_methods
    })


@router.post("/api/cashier/scan")
async def scan_order(
    scan_data: CashierScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    """
    Scan QR code or enter tracking token to retrieve order.

    Returns order details for payment processing.
    """
    order = get_order_by_token(db, scan_data.tracking_token)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [
        OrderItemResponse(
            id=item.id,
            menu_id=item.menu_id,
            quantity=item.quantity,
            notes=item.notes,
            subtotal=item.subtotal,
            menu_name=item.menu.name if item.menu else None,
            menu_price=item.menu.price if item.menu else None
        )
        for item in order.items
    ]

    return CashierScanResponse(
        order_id=order.id,
        table_number=order.table_number,
        total_amount=order.total_amount,
        status=order.status,
        items=items
    )


class PayRequest(BaseModel):
    payment_method: Optional[str] = None

@router.put("/api/cashier/pay/{order_id}")
async def process_payment(
    order_id: int,
    pay_data: PayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be paid. Current status: {order.status.value}"
        )

    order.status = OrderStatus.PAID
    order.user_id = current_user.id
    if pay_data.payment_method:
        order.payment_method = pay_data.payment_method
    db.commit()

    return {
        "order_id": order.id,
        "status": order.status.value,
        "message": "Payment processed successfully"
    }


@router.put("/api/cashier/complete/{order_id}")
async def complete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    """
    Mark order as completed.

    Updates order status from PAID to COMPLETED.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be completed. Current status: {order.status.value}"
        )

    order.status = OrderStatus.COMPLETED
    db.commit()

    return {
        "order_id": order.id,
        "status": order.status.value,
        "message": "Order completed successfully"
    }


@router.get("/cashier/closing", response_class=HTMLResponse)
async def cashier_closing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir")),
    selected_date: Optional[str] = None
):
    try:
        from datetime import datetime
        target = datetime.strptime(selected_date, "%Y-%m-%d").date() if selected_date else date.today()
    except ValueError:
        target = date.today()

    orders = db.query(Order).filter(
        func.date(Order.created_at) == target,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED])
    ).order_by(Order.created_at).all()

    total_revenue = sum(float(o.total_amount) for o in orders)

    breakdown = {}
    for o in orders:
        key = o.payment_method or "Tidak Tercatat"
        breakdown[key] = breakdown.get(key, 0) + float(o.total_amount)

    return templates.TemplateResponse("cashier/closing.html", {
        "request": request,
        "user": current_user,
        "orders": orders,
        "total_revenue": total_revenue,
        "breakdown": breakdown,
        "selected_date": target.strftime("%Y-%m-%d"),
        "display_date": target.strftime("%d %B %Y"),
        "order_count": len(orders)
    })


@router.get("/api/cashier/orders")
async def list_active_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    def serialize(order):
        return {
            "id": order.id,
            "table_number": order.table_number,
            "total_amount": float(order.total_amount),
            "status": order.status.value,
            "created_at": order.created_at.isoformat(),
            "tracking_token": order.tracking_token,
            "item_count": len(order.items)
        }

    pending = db.query(Order).filter(
        Order.status == OrderStatus.PENDING
    ).order_by(Order.created_at.desc()).all()

    paid = db.query(Order).filter(
        Order.status == OrderStatus.PAID
    ).order_by(Order.created_at.desc()).all()

    return {
        "pending": [serialize(o) for o in pending],
        "paid": [serialize(o) for o in paid]
    }
