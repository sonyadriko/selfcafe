from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate
from app.dependencies import get_current_user
from app.models.user import User
from app.services.upload import upload_service

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

    # Store old image URL for cleanup
    old_image_url = db_menu.image_url

    for field, value in menu.model_dump(exclude_unset=True).items():
        setattr(db_menu, field, value)

    db.commit()

    # Delete old image if replaced with new one
    if menu.image_url and old_image_url and menu.image_url != old_image_url:
        if not menu.image_url.startswith("http"):
            upload_service.delete_image(old_image_url)

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

    # Delete associated image file
    if db_menu.image_url and not db_menu.image_url.startswith("http"):
        upload_service.delete_image(db_menu.image_url)

    db.delete(db_menu)
    db.commit()
    return {"success": True}

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image file.

    Returns:
        {"url": "/static/uploads/uuid.jpg"}
    """
    image_url = await upload_service.upload_image(file)
    return {"url": image_url}
