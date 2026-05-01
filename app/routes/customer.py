from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from typing import Optional
import qrcode
import io
from app.database import get_db
from app.models.menu import Menu, Category
from app.schemas.order import OrderCreate, OrderTrackingResponse, OrderItemResponse
from app.models.order import Order, OrderItem
from app.services.tracking import generate_tracking_token, get_order_by_token

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def customer_home(request: Request, table: Optional[int] = 1):
    return templates.TemplateResponse("customer/index.html", {
        "request": request,
        "table": table
    })

@router.get("/menu")
async def get_menu(db: Session = Depends(get_db)):
    menus = db.query(Menu).filter(Menu.is_active == True).all()
    categories = db.query(Category).all()

    return {
        "menus": [
            {
                "id": m.id,
                "name": m.name,
                "description": m.description,
                "price": float(m.price),
                "image_url": m.image_url,
                "category_id": m.category_id,
                "stock": m.stock
            }
            for m in menus
        ],
        "categories": [
            {"id": c.id, "name": c.name}
            for c in categories
        ]
    }

@router.post("/order")
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    total = 0
    order_items = []

    for item in order.items:
        menu = db.query(Menu).filter(Menu.id == item.menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail=f"Menu {item.menu_id} not found")

        subtotal = float(menu.price) * item.quantity
        total += subtotal

        order_items.append({
            "menu_id": item.menu_id,
            "quantity": item.quantity,
            "subtotal": subtotal,
            "notes": item.notes
        })

    new_order = Order(
        table_number=order.table_number,
        total_amount=total,
        status="pending",
        tracking_token=generate_tracking_token()
    )
    db.add(new_order)
    db.flush()

    for item_data in order_items:
        order_item = OrderItem(
            order_id=new_order.id,
            **item_data
        )
        db.add(order_item)

    db.commit()

    return {
        "order_id": new_order.id,
        "table_number": new_order.table_number,
        "total_amount": float(new_order.total_amount),
        "status": new_order.status,
        "tracking_token": new_order.tracking_token
    }


@router.get("/order/success/{tracking_token}", response_class=HTMLResponse)
async def order_success(request: Request, tracking_token: str):
    """Order success page with QR code."""
    return templates.TemplateResponse("customer/order-success.html", {
        "request": request,
        "tracking_token": tracking_token
    })


@router.get("/track/{tracking_token}", response_class=HTMLResponse)
async def track_page(request: Request, tracking_token: str):
    """Order tracking page."""
    return templates.TemplateResponse("customer/track.html", {
        "request": request,
        "tracking_token": tracking_token
    })


@router.get("/api/track/{tracking_token}")
async def track_order(tracking_token: str, db: Session = Depends(get_db)):
    """API endpoint to get order status by tracking token."""
    order = get_order_by_token(db, tracking_token)

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

    return OrderTrackingResponse(
        id=order.id,
        table_number=order.table_number,
        total_amount=order.total_amount,
        status=order.status,
        created_at=order.created_at,
        items=items
    )


@router.get("/qr/{tracking_token}")
async def generate_qr(tracking_token: str, request: Request):
    """
    Generate QR code for order tracking.

    QR code contains the tracking URL.
    """
    from app.config import settings

    # Build tracking URL
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    tracking_url = f"{base_url}/customer/track/{tracking_token}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(tracking_url)
    qr.make(fit=True)

    # Create image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return Response(content=buf.read(), media_type="image/png")
