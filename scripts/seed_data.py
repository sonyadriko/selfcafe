import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[0]))

from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.menu import Category, Menu
from app.services.auth_service import get_password_hash

def seed():
    db = SessionLocal()

    Base.metadata.create_all(bind=engine)

    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN
        )
        db.add(admin)

    kasir = db.query(User).filter(User.username == "kasir").first()
    if not kasir:
        kasir = User(
            username="kasir",
            password_hash=get_password_hash("kasir123"),
            full_name="Kasir Utama",
            role=UserRole.KASIR
        )
        db.add(kasir)

    categories = [
        {"name": "Coffee"},
        {"name": "Non-Coffee"},
        {"name": "Food"},
        {"name": "Snack"}
    ]

    for cat_data in categories:
        existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not existing:
            db.add(Category(**cat_data))

    db.commit()

    coffee_cat = db.query(Category).filter(Category.name == "Coffee").first()
    food_cat = db.query(Category).filter(Category.name == "Food").first()
    snack_cat = db.query(Category).filter(Category.name == "Snack").first()

    menus = [
        {"name": "Espresso", "description": "Single shot espresso", "price": 15000, "category_id": coffee_cat.id, "stock": 100},
        {"name": "Americano", "description": "Espresso with hot water", "price": 18000, "category_id": coffee_cat.id, "stock": 100},
        {"name": "Cappuccino", "description": "Espresso with steamed milk foam", "price": 25000, "category_id": coffee_cat.id, "stock": 100},
        {"name": "Latte", "description": "Espresso with steamed milk", "price": 28000, "category_id": coffee_cat.id, "stock": 100},
        {"name": "Nasi Goreng", "description": "Fried rice with egg", "price": 35000, "category_id": food_cat.id, "stock": 50},
        {"name": "Mie Goreng", "description": "Fried noodles", "price": 30000, "category_id": food_cat.id, "stock": 50},
        {"name": "French Fries", "description": "Crispy potato fries", "price": 20000, "category_id": snack_cat.id, "stock": 100},
        {"name": "Roti Bakar", "description": "Grilled bread with chocolate", "price": 18000, "category_id": snack_cat.id, "stock": 80},
    ]

    for menu_data in menus:
        existing = db.query(Menu).filter(Menu.name == menu_data["name"]).first()
        if not existing:
            db.add(Menu(**menu_data))

    db.commit()
    print("Seed data berhasil!")

if __name__ == "__main__":
    seed()
