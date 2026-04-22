from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.menu import Menu, Category
from app.schemas.order import OrderCreate
from app.models.order import Order, OrderItem

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
        status="pending"
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
        "status": new_order.status
    }
