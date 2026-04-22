from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/menus/{menu_id}")
async def get_menu(menu_id: int, db: Session = Depends(get_db)):
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return {
        "id": menu.id,
        "name": menu.name,
        "description": menu.description,
        "price": float(menu.price),
        "category_id": menu.category_id,
        "stock": menu.stock,
        "image_url": menu.image_url
    }

@router.post("/menus")
async def create_menu(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_menu = Menu(**menu.model_dump())
    db.add(new_menu)
    db.commit()
    db.refresh(new_menu)
    return {"success": True, "id": new_menu.id}

@router.put("/menus/{menu_id}")
async def update_menu(
    menu_id: int,
    menu: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    for field, value in menu.model_dump(exclude_unset=True).items():
        setattr(db_menu, field, value)

    db.commit()
    return {"success": True}

@router.delete("/menus/{menu_id}")
async def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu not found")

    db.delete(db_menu)
    db.commit()
    return {"success": True}
