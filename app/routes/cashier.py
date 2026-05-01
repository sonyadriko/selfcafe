"""
Cashier routes for QR code scanning and payment processing.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User
from app.schemas.order import CashierScanRequest, CashierScanResponse, OrderItemResponse
from app.dependencies import get_current_user, require_role
from app.services.tracking import get_order_by_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/cashier", response_class=HTMLResponse)
async def cashier_dashboard(
    request: Request,
    current_user: User = Depends(require_role("admin", "kasir"))
):
    """Cashier dashboard for QR scanning."""
    return templates.TemplateResponse("cashier/dashboard.html", {
        "request": request,
        "user": current_user
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


@router.put("/api/cashier/pay/{order_id}")
async def process_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    """
    Process payment for an order.

    Updates order status from PENDING to PAID.
    """
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Order cannot be paid. Current status: {order.status.value}"
        )

    order.status = OrderStatus.PAID
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


@router.get("/api/cashier/orders")
async def list_pending_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "kasir"))
):
    """List all pending orders for cashier view."""
    orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).order_by(Order.created_at.desc()).all()

    return {
        "orders": [
            {
                "id": order.id,
                "table_number": order.table_number,
                "total_amount": float(order.total_amount),
                "status": order.status.value,
                "created_at": order.created_at.isoformat(),
                "tracking_token": order.tracking_token,
                "item_count": len(order.items)
            }
            for order in orders
        ]
    }
