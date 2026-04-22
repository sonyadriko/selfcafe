# SelfCafe Ordering System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build web-based self-ordering system for coffee shop with FastAPI + MySQL + Jinja2

**Architecture:** Monolithic FastAPI app with Jinja2 templates, SQLAlchemy ORM, MySQL database, JWT authentication

**Tech Stack:** FastAPI, Uvicorn, MySQL, SQLAlchemy, Alembic, python-jose, bcrypt, Jinja2, Tailwind CSS

---

## PHASE 1: Project Setup

### Task 1: Initialize project structure

**Files:**
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `app/database.py`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `run.py`

**Step 1: Create requirements.txt**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pymysql==1.1.0
cryptography==41.0.7
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
jinja2==3.1.3
python-dotenv==1.0.0
pydantic[email]==2.5.3
pydantic-settings==2.1.0
```

**Step 2: Create .env.example**

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=selfcafe_db

# JWT
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# App
APP_NAME=SelfCafe Ordering
DEBUG=True
```

**Step 3: Create app/config.py**

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "selfcafe_db"

    # JWT
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # App
    APP_NAME: str = "SelfCafe Ordering"
    DEBUG: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Step 4: Create app/database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 5: Create app/main.py**

```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.config import settings
from app.database import engine, Base
from app.routes import auth, customer, admin, api

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(customer.router, prefix="/customer", tags=["customer"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(api.router, prefix="/api", tags=["api"])

@app.get("/")
async def root():
    return RedirectResponse(url="/customer")
```

**Step 6: Create run.py**

```python
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

**Step 7: Create empty __init__.py**

```bash
touch app/__init__.py
touch app/routes/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
```

**Step 8: Commit**

```bash
git add .
git commit -m "feat: initialize project structure and config"
```

---

## PHASE 2: Database Models

### Task 2: Create User model

**Files:**
- Create: `app/models/user.py`
- Create: `app/schemas/user.py`

**Step 1: Create app/models/user.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STAFF = "staff"
    KASIR = "kasir"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STAFF, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 2: Create app/schemas/user.py**

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole = UserRole.STAFF

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class LoginRequest(BaseModel):
    username: str
    password: str
```

**Step 3: Commit**

```bash
git add app/models/user.py app/schemas/user.py
git commit -m "feat: add User model and schemas"
```

---

### Task 3: Create Menu and Category models

**Files:**
- Create: `app/models/menu.py`
- Create: `app/schemas/menu.py`

**Step 1: Create app/models/menu.py**

```python
from sqlalchemy import Column, Integer, String, Decimal, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    menus = relationship("Menu", back_populates="category")

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    price = Column(Decimal(10, 2), nullable=False)
    image_url = Column(String(255))
    category_id = Column(Integer, ForeignKey("categories.id"))
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category", back_populates="menus")
```

**Step 2: Create app/schemas/menu.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MenuBase(BaseModel):
    name: str
    description: str | None = None
    price: Decimal = Field(gt=0)
    category_id: int
    stock: int = 0
    is_active: bool = True

class MenuCreate(MenuBase):
    image_url: str | None = None

class MenuUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: Decimal | None = None
    category_id: int | None = None
    stock: int | None = None
    is_active: bool | None = None
    image_url: str | None = None

class MenuResponse(MenuBase):
    id: int
    image_url: str | None
    created_at: datetime
    category: CategoryResponse | None = None

    class Config:
        from_attributes = True
```

**Step 3: Commit**

```bash
git add app/models/menu.py app/schemas/menu.py
git commit -m "feat: add Menu and Category models"
```

---

### Task 4: Create Order and OrderItem models

**Files:**
- Create: `app/models/order.py`
- Create: `app/schemas/order.py`

**Step 1: Create app/models/order.py**

```python
from sqlalchemy import Column, Integer, String, Decimal, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    table_number = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_amount = Column(Decimal(10, 2), default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(Decimal(10, 2), nullable=False)
    notes = Column(String(255))

    order = relationship("Order", back_populates="items")
```

**Step 2: Create app/schemas/order.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List
from app.models.order import OrderStatus

class OrderItemBase(BaseModel):
    menu_id: int
    quantity: int = Field(gt=0)
    notes: str | None = None

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(OrderItemBase):
    id: int
    subtotal: Decimal
    menu_name: str | None = None
    menu_price: Decimal | None = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    table_number: int = Field(gt=0)

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class OrderUpdate(BaseModel):
    status: OrderStatus

class OrderResponse(OrderBase):
    id: int
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
```

**Step 3: Commit**

```bash
git add app/models/order.py app/schemas/order.py
git commit -m "feat: add Order and OrderItem models"
```

---

### Task 5: Create Promo model

**Files:**
- Create: `app/models/promo.py`
- Create: `app/schemas/promo.py`

**Step 1: Create app/models/promo.py**

```python
from sqlalchemy import Column, Integer, String, Decimal, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base
import enum

class DiscountType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class Promo(Base):
    __tablename__ = "promos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(Integer, nullable=False)  # percent or fixed amount
    min_purchase = Column(Integer, default=0)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Step 2: Create app/schemas/promo.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime

class PromoBase(BaseModel):
    name: str
    discount_type: str  # 'percentage' or 'fixed'
    discount_value: int = Field(gt=0)
    min_purchase: int = 0

class PromoCreate(PromoBase):
    start_date: datetime | None = None
    end_date: datetime | None = None

class PromoUpdate(BaseModel):
    name: str | None = None
    discount_type: str | None = None
    discount_value: int | None = None
    min_purchase: int | None = None
    is_active: bool | None = None

class PromoResponse(PromoBase):
    id: int
    is_active: bool
    start_date: datetime | None
    end_date: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 3: Commit**

```bash
git add app/models/promo.py app/schemas/promo.py
git commit -m "feat: add Promo model"
```

---

### Task 6: Setup Alembic migrations

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`

**Step 1: Initialize Alembic**

```bash
cd /Users/sonyadriko/Projects/SelfCafe-Ordering-System
alembic init alembic
```

**Step 2: Edit alembic.ini**

Edit `sqlalchemy.url` line:
```ini
sqlalchemy.url = mysql+pymysql://root:password@localhost:3306/selfcafe_db
```

**Step 3: Edit alembic/env.py**

Add at top after imports:
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[0]))

from app.config import settings
```

Replace `config.set_main_option` line:
```python
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

Add in `run_migrations_online()` before `target_metadata`:
```python
from app.database import Base
from app.models import user, menu, order, promo
target_metadata = Base.metadata
```

**Step 4: Create first migration**

```bash
alembic revision --autogenerate -m "Initial migration"
```

**Step 5: Commit**

```bash
git add alembic.ini alembic/
git commit -m "feat: setup Alembic migrations"
```

---

## PHASE 3: Authentication

### Task 7: Create Auth service

**Files:**
- Create: `app/services/auth_service.py`

**Step 1: Create app/services/auth_service.py**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.schemas.user import TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return TokenData(username=username)
    except JWTError:
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
```

**Step 2: Commit**

```bash
git add app/services/auth_service.py
git commit -m "feat: add authentication service"
```

---

### Task 8: Create Auth routes

**Files:**
- Create: `app/routes/auth.py`

**Step 1: Create app/routes/auth.py**

```python
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.user import LoginRequest, Token
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("admin/login.html", {"request": request})

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "admin/login.html",
            {"request": request, "error": "Username atau password salah"}
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    response = RedirectResponse(url="/admin/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return response

@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login")
    response.delete_cookie("access_token")
    return response
```

**Step 2: Commit**

```bash
git add app/routes/auth.py
git commit -m "feat: add auth routes - login/logout"
```

---

### Task 9: Create auth dependency

**Files:**
- Create: `app/dependencies.py`

**Step 1: Create app/dependencies.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.models.user import User
from app.services.auth_service import verify_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    if token.startswith("Bearer "):
        token = token[7:]

    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

def require_role(*allowed_roles):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker
```

**Step 2: Commit**

```bash
git add app/dependencies.py
git commit -m "feat: add auth dependencies for protected routes"
```

---

## PHASE 4: Customer Interface

### Task 10: Create base template

**Files:**
- Create: `app/templates/base.html`

**Step 1: Create app/templates/base.html**

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SelfCafe Ordering{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { font-family: 'Inter', sans-serif; }
    </style>
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-50">
    {% block content %}{% endblock %}
    {% block scripts %}{% endblock %}
</body>
</html>
```

**Step 2: Commit**

```bash
git add app/templates/base.html
git commit -m "feat: add base HTML template with Tailwind"
```

---

### Task 11: Create customer index page

**Files:**
- Create: `app/templates/customer/index.html`
- Create: `app/routes/customer.py`

**Step 1: Create app/templates/customer/index.html**

```html
{% extends "base.html" %}

{% block title %}Menu - SelfCafe{% endblock %}

{% block content %}
<div class="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50">
    <!-- Header -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 py-4 flex justify-between items-center">
            <h1 class="text-2xl font-bold text-amber-800">☕ Sowan Kopi</h1>
            <div class="flex items-center gap-4">
                <span class="text-gray-600">Meja <span id="tableNumber" class="font-semibold text-amber-700">{{ table }}</span></span>
                <button onclick="openCart()" class="relative bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700">
                    🛒 <span id="cartCount">0</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Category Filter -->
    <div class="max-w-6xl mx-auto px-4 py-4">
        <div class="flex gap-2 overflow-x-auto pb-2" id="categoryFilters">
            <button onclick="filterCategory('all')" class="category-btn active px-4 py-2 rounded-full bg-amber-600 text-white whitespace-nowrap">Semua</button>
        </div>
    </div>

    <!-- Menu Grid -->
    <div class="max-w-6xl mx-auto px-4 pb-24">
        <div id="menuGrid" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <!-- Menu items will be loaded here -->
        </div>
    </div>

    <!-- Cart Modal -->
    <div id="cartModal" class="fixed inset-0 bg-black/50 z-50 hidden">
        <div class="absolute right-0 top-0 h-full w-full max-w-md bg-white shadow-xl">
            <div class="p-4 border-b flex justify-between items-center">
                <h2 class="text-xl font-bold">Keranjang</h2>
                <button onclick="closeCart()" class="text-gray-500 text-2xl">&times;</button>
            </div>
            <div id="cartItems" class="p-4 overflow-y-auto" style="max-height: calc(100vh - 200px);">
                <!-- Cart items here -->
            </div>
            <div class="absolute bottom-0 left-0 right-0 p-4 bg-white border-t">
                <div class="flex justify-between mb-4">
                    <span class="font-semibold">Total:</span>
                    <span id="cartTotal" class="font-bold text-xl">Rp 0</span>
                </div>
                <button onclick="placeOrder()" class="w-full bg-amber-600 text-white py-3 rounded-lg font-semibold hover:bg-amber-700">
                    Pesan Sekarang
                </button>
            </div>
        </div>
    </div>
</div>

<script>
let cart = [];
let tableNumber = {{ table }};

async function loadMenu() {
    const response = await fetch('/customer/menu');
    const data = await response.json();
    renderMenu(data.menus, data.categories);
}

function renderMenu(menus, categories) {
    // Render category filters
    const categoryFilters = document.getElementById('categoryFilters');
    categoryFilters.innerHTML = '<button onclick="filterCategory(\'all\')" class="category-btn active px-4 py-2 rounded-full bg-amber-600 text-white whitespace-nowrap">Semua</button>';
    categories.forEach(cat => {
        categoryFilters.innerHTML += `<button onclick="filterCategory('${cat.id}')" class="category-btn px-4 py-2 rounded-full bg-gray-200 text-gray-700 whitespace-nowrap">${cat.name}</button>`;
    });

    // Store menus for filtering
    window.allMenus = menus;

    // Render menu items
    filterCategory('all');
}

function filterCategory(categoryId) {
    const filtered = categoryId === 'all'
        ? window.allMenus
        : window.allMenus.filter(m => m.category_id === parseInt(categoryId));

    const menuGrid = document.getElementById('menuGrid');
    menuGrid.innerHTML = filtered.map(menu => `
        <div class="bg-white rounded-xl shadow-sm overflow-hidden hover:shadow-md transition">
            ${menu.image_url ? `<img src="${menu.image_url}" alt="${menu.name}" class="w-full h-32 object-cover">` : '<div class="w-full h-32 bg-gray-200 flex items-center justify-center text-gray-400">No Image</div>'}
            <div class="p-3">
                <h3 class="font-semibold text-gray-800 truncate">${menu.name}</h3>
                <p class="text-xs text-gray-500 truncate">${menu.description || ''}</p>
                <div class="flex justify-between items-center mt-2">
                    <span class="font-bold text-amber-700">Rp ${parseInt(menu.price).toLocaleString('id-ID')}</span>
                    <button onclick="addToCart(${menu.id})" class="bg-amber-600 text-white px-3 py-1 rounded-full text-sm hover:bg-amber-700">+ Tambah</button>
                </div>
            </div>
        </div>
    `).join('');

    // Update active button
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('bg-amber-600', 'text-white');
        btn.classList.add('bg-gray-200', 'text-gray-700');
    });
    event.target.classList.remove('bg-gray-200', 'text-gray-700');
    event.target.classList.add('bg-amber-600', 'text-white');
}

function addToCart(menuId) {
    const menu = window.allMenus.find(m => m.id === menuId);
    const existing = cart.find(item => item.menu_id === menuId);

    if (existing) {
        existing.quantity++;
    } else {
        cart.push({
            menu_id: menu.id,
            name: menu.name,
            price: menu.price,
            quantity: 1
        });
    }

    updateCartUI();
}

function updateCartUI() {
    document.getElementById('cartCount').textContent = cart.reduce((sum, item) => sum + item.quantity, 0);

    const cartItems = document.getElementById('cartItems');
    if (cart.length === 0) {
        cartItems.innerHTML = '<p class="text-gray-500 text-center">Keranjang kosong</p>';
    } else {
        cartItems.innerHTML = cart.map((item, index) => `
            <div class="flex justify-between items-center py-2 border-b">
                <div>
                    <p class="font-medium">${item.name}</p>
                    <p class="text-sm text-gray-500">Rp ${parseInt(item.price).toLocaleString('id-ID')}</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="updateQuantity(${index}, -1)" class="w-8 h-8 rounded-full bg-gray-200">-</button>
                    <span>${item.quantity}</span>
                    <button onclick="updateQuantity(${index}, 1)" class="w-8 h-8 rounded-full bg-gray-200">+</button>
                </div>
            </div>
        `).join('');
    }

    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.getElementById('cartTotal').textContent = `Rp ${total.toLocaleString('id-ID')}`;
}

function updateQuantity(index, delta) {
    cart[index].quantity += delta;
    if (cart[index].quantity <= 0) {
        cart.splice(index, 1);
    }
    updateCartUI();
}

function openCart() {
    document.getElementById('cartModal').classList.remove('hidden');
}

function closeCart() {
    document.getElementById('cartModal').classList.add('hidden');
}

async function placeOrder() {
    if (cart.length === 0) {
        alert('Keranjang kosong!');
        return;
    }

    const response = await fetch('/customer/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            table_number: tableNumber,
            items: cart.map(item => ({
                menu_id: item.menu_id,
                quantity: item.quantity
            }))
        })
    });

    if (response.ok) {
        const data = await response.json();
        cart = [];
        updateCartUI();
        closeCart();
        alert('Pesanan berhasil! Silakan tunggu di meja Anda.');
    } else {
        alert('Gagal membuat pesanan');
    }
}

// Load menu on page load
loadMenu();
</script>
{% endblock %}
```

**Step 2: Create app/routes/customer.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.menu import Menu, Category
from app.schemas.order import OrderCreate, OrderResponse
from app.models.order import Order, OrderItem
from datetime import datetime

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
    # Calculate total
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

    # Create order
    new_order = Order(
        table_number=order.table_number,
        total_amount=total,
        status="pending"
    )
    db.add(new_order)
    db.flush()

    # Create order items
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
```

**Step 3: Commit**

```bash
git add app/templates/customer/ app/routes/customer.py
git commit -m "feat: add customer ordering interface"
```

---

## PHASE 5: Admin Dashboard

### Task 12: Create admin login page

**Files:**
- Create: `app/templates/admin/login.html`

**Step 1: Create app/templates/admin/login.html**

```html
{% extends "base.html" %}

{% block title %}Login - Admin{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-amber-100 to-orange-100">
    <div class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-amber-800">☕ Sowan Kopi</h1>
            <p class="text-gray-600 mt-2">Admin Login</p>
        </div>

        {% if error %}
        <div class="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
            {{ error }}
        </div>
        {% endif %}

        <form method="post" action="/auth/login">
            <div class="mb-4">
                <label class="block text-gray-700 mb-2">Username</label>
                <input type="text" name="username" required
                    class="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500">
            </div>
            <div class="mb-6">
                <label class="block text-gray-700 mb-2">Password</label>
                <input type="password" name="password" required
                    class="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500">
            </div>
            <button type="submit"
                class="w-full bg-amber-600 text-white py-3 rounded-lg font-semibold hover:bg-amber-700">
                Login
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

**Step 2: Commit**

```bash
git add app/templates/admin/login.html
git commit -m "feat: add admin login page"
```

---

### Task 13: Create admin dashboard

**Files:**
- Create: `app/templates/admin/dashboard.html`
- Create: `app/routes/admin.py`

**Step 1: Create app/templates/admin/dashboard.html**

```html
{% extends "base.html" %}

{% block title %}Dashboard - Admin{% endblock %}

{% block content %}
<div class="min-h-screen bg-gray-100">
    <!-- Sidebar -->
    <div class="fixed left-0 top-0 h-full w-64 bg-amber-800 text-white">
        <div class="p-4 border-b border-amber-700">
            <h1 class="text-xl font-bold">☕ Sowan Kopi</h1>
            <p class="text-amber-200 text-sm">Admin Panel</p>
        </div>
        <nav class="p-4">
            <a href="/admin/dashboard" class="block py-2 px-4 rounded bg-amber-700 mb-2">Dashboard</a>
            <a href="/admin/orders" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Pesanan</a>
            <a href="/admin/menus" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Menu</a>
            <a href="/auth/logout" class="block py-2 px-4 rounded hover:bg-amber-700 mt-8">Logout</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="ml-64 p-8">
        <h2 class="text-2xl font-bold mb-6">Dashboard</h2>

        <!-- Stats -->
        <div class="grid grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <p class="text-gray-500 text-sm">Pesanan Pending</p>
                <p class="text-3xl font-bold text-amber-600">{{ stats.pending }}</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <p class="text-gray-500 text-sm">Pesanan Hari Ini</p>
                <p class="text-3xl font-bold text-blue-600">{{ stats.today }}</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <p class="text-gray-500 text-sm">Total Menu</p>
                <p class="text-3xl font-bold text-green-600">{{ stats.menus }}</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm">
                <p class="text-gray-500 text-sm">Pendapatan Hari Ini</p>
                <p class="text-3xl font-bold text-purple-600">Rp {{ stats.revenue|default(0)|int }}</p>
            </div>
        </div>

        <!-- Recent Orders -->
        <div class="bg-white rounded-xl shadow-sm p-6">
            <h3 class="text-lg font-bold mb-4">Pesanan Terbaru</h3>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="border-b">
                            <th class="text-left py-3 px-4">ID</th>
                            <th class="text-left py-3 px-4">Meja</th>
                            <th class="text-left py-3 px-4">Total</th>
                            <th class="text-left py-3 px-4">Status</th>
                            <th class="text-left py-3 px-4">Waktu</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for order in recent_orders %}
                        <tr class="border-b hover:bg-gray-50">
                            <td class="py-3 px-4">#{{ order.id }}</td>
                            <td class="py-3 px-4">{{ order.table_number }}</td>
                            <td class="py-3 px-4">Rp {{ order.total_amount|int }}</td>
                            <td class="py-3 px-4">
                                <span class="px-2 py-1 rounded text-xs
                                    {% if order.status == 'pending' %}bg-yellow-100 text-yellow-800
                                    {% elif order.status == 'paid' %}bg-green-100 text-green-800
                                    {% elif order.status == 'completed' %}bg-blue-100 text-blue-800
                                    {% else %}bg-red-100 text-red-800{% endif %}">
                                    {{ order.status|title }}
                                </span>
                            </td>
                            <td class="py-3 px-4 text-gray-500">{{ order.created_at.strftime('%H:%M') }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 2: Create app/routes/admin.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
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
    # Stats
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()

    today = date.today()
    today_orders = db.query(Order).filter(
        func.date(Order.created_at) == today
    ).all()
    today_count = len(today_orders)

    menus = db.query(Menu).filter(Menu.is_active == True).count()

    revenue = sum(o.total_amount for o in today_orders if o.status in [OrderStatus.PAID, OrderStatus.COMPLETED])

    # Recent orders
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

@router.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    db.commit()

    return {"success": True, "order_id": order_id, "status": status}

@router.get("/menus", response_class=HTMLResponse)
async def menus_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    menus = db.query(Menu).order_by(Menu.category_id).all()
    categories = db.query(Menu.category_id).distinct().all()
    return templates.TemplateResponse("admin/menus.html", {
        "request": request,
        "menus": menus
    })
```

**Step 3: Commit**

```bash
git add app/templates/admin/dashboard.html app/templates/admin/orders.html app/routes/admin.py
git commit -m "feat: add admin dashboard and orders page"
```

---

### Task 14: Create admin orders page

**Files:**
- Create: `app/templates/admin/orders.html`

**Step 1: Create app/templates/admin/orders.html**

```html
{% extends "base.html" %}

{% block title %}Pesanan - Admin{% endblock %}

{% block content %}
<div class="min-h-screen bg-gray-100">
    <!-- Sidebar -->
    <div class="fixed left-0 top-0 h-full w-64 bg-amber-800 text-white">
        <div class="p-4 border-b border-amber-700">
            <h1 class="text-xl font-bold">☕ Sowan Kopi</h1>
            <p class="text-amber-200 text-sm">Admin Panel</p>
        </div>
        <nav class="p-4">
            <a href="/admin/dashboard" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Dashboard</a>
            <a href="/admin/orders" class="block py-2 px-4 rounded bg-amber-700 mb-2">Pesanan</a>
            <a href="/admin/menus" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Menu</a>
            <a href="/auth/logout" class="block py-2 px-4 rounded hover:bg-amber-700 mt-8">Logout</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="ml-64 p-8">
        <h2 class="text-2xl font-bold mb-6">Daftar Pesanan</h2>

        <!-- Filter -->
        <div class="flex gap-4 mb-6">
            <button onclick="filterOrders('all')" class="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300">Semua</button>
            <button onclick="filterOrders('pending')" class="px-4 py-2 rounded-lg bg-yellow-200 hover:bg-yellow-300">Pending</button>
            <button onclick="filterOrders('paid')" class="px-4 py-2 rounded-lg bg-green-200 hover:bg-green-300">Paid</button>
            <button onclick="filterOrders('completed')" class="px-4 py-2 rounded-lg bg-blue-200 hover:bg-blue-300">Completed</button>
        </div>

        <!-- Orders Table -->
        <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <table class="w-full" id="ordersTable">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="text-left py-3 px-4">ID</th>
                        <th class="text-left py-3 px-4">Meja</th>
                        <th class="text-left py-3 px-4">Items</th>
                        <th class="text-left py-3 px-4">Total</th>
                        <th class="text-left py-3 px-4">Status</th>
                        <th class="text-left py-3 px-4">Waktu</th>
                        <th class="text-left py-3 px-4">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% for order in orders %}
                    <tr class="border-b hover:bg-gray-50" data-status="{{ order.status }}">
                        <td class="py-3 px-4 font-semibold">#{{ order.id }}</td>
                        <td class="py-3 px-4">{{ order.table_number }}</td>
                        <td class="py-3 px-4">
                            {% for item in order.items %}
                            <div class="text-sm">{{ item.quantity }}x {{ item.menu.name if item.menu else 'N/A' }}</div>
                            {% endfor %}
                        </td>
                        <td class="py-3 px-4 font-semibold">Rp {{ order.total_amount|int }}</td>
                        <td class="py-3 px-4">
                            <select onchange="updateStatus({{ order.id }}, this.value)" class="px-2 py-1 rounded border
                                {% if order.status == 'pending' %}bg-yellow-100
                                {% elif order.status == 'paid' %}bg-green-100
                                {% elif order.status == 'completed' %}bg-blue-100
                                {% else %}bg-red-100{% endif %}">
                                <option value="pending" {% if order.status == 'pending' %}selected{% endif %}>Pending</option>
                                <option value="paid" {% if order.status == 'paid' %}selected{% endif %}>Paid</option>
                                <option value="completed" {% if order.status == 'completed' %}selected{% endif %}>Completed</option>
                                <option value="cancelled" {% if order.status == 'cancelled' %}selected{% endif %}>Cancelled</option>
                            </select>
                        </td>
                        <td class="py-3 px-4 text-gray-500">{{ order.created_at.strftime('%H:%M') }}</td>
                        <td class="py-3 px-4">
                            <button onclick="viewDetails({{ order.id }})" class="text-blue-600 hover:underline">Detail</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
async function updateStatus(orderId, status) {
    const response = await fetch(`/admin/orders/${orderId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status })
    });

    if (response.ok) {
        location.reload();
    } else {
        alert('Gagal update status');
    }
}

function filterOrders(status) {
    const rows = document.querySelectorAll('#ordersTable tbody tr');
    rows.forEach(row => {
        if (status === 'all' || row.dataset.status === status) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
</script>
{% endblock %}
```

**Step 2: Commit**

```bash
git add app/templates/admin/orders.html
git commit -m "feat: add admin orders management page"
```

---

### Task 15: Create admin menus page

**Files:**
- Create: `app/templates/admin/menus.html`

**Step 1: Create app/templates/admin/menus.html**

```html
{% extends "base.html" %}

{% block title %}Menu Management - Admin{% endblock %}

{% block content %}
<div class="min-h-screen bg-gray-100">
    <!-- Sidebar -->
    <div class="fixed left-0 top-0 h-full w-64 bg-amber-800 text-white">
        <div class="p-4 border-b border-amber-700">
            <h1 class="text-xl font-bold">☕ Sowan Kopi</h1>
            <p class="text-amber-200 text-sm">Admin Panel</p>
        </div>
        <nav class="p-4">
            <a href="/admin/dashboard" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Dashboard</a>
            <a href="/admin/orders" class="block py-2 px-4 rounded hover:bg-amber-700 mb-2">Pesanan</a>
            <a href="/admin/menus" class="block py-2 px-4 rounded bg-amber-700 mb-2">Menu</a>
            <a href="/auth/logout" class="block py-2 px-4 rounded hover:bg-amber-700 mt-8">Logout</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="ml-64 p-8">
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold">Kelola Menu</h2>
            <button onclick="openAddModal()" class="bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700">+ Tambah Menu</button>
        </div>

        <!-- Menu Grid -->
        <div class="grid grid-cols-4 gap-6" id="menuGrid">
            {% for menu in menus %}
            <div class="bg-white rounded-xl shadow-sm overflow-hidden">
                {% if menu.image_url %}
                <img src="{{ menu.image_url }}" alt="{{ menu.name }}" class="w-full h-40 object-cover">
                {% else %}
                <div class="w-full h-40 bg-gray-200 flex items-center justify-center text-gray-400">No Image</div>
                {% endif %}
                <div class="p-4">
                    <h3 class="font-semibold text-lg">{{ menu.name }}</h3>
                    <p class="text-gray-500 text-sm mb-2">{{ menu.description or '-' }}</p>
                    <p class="font-bold text-amber-700">Rp {{ menu.price|int }}</p>
                    <p class="text-sm text-gray-500">Stok: {{ menu.stock }}</p>
                    <div class="flex gap-2 mt-3">
                        <button onclick="openEditModal({{ menu.id }})" class="flex-1 bg-blue-600 text-white py-2 rounded text-sm hover:bg-blue-700">Edit</button>
                        <button onclick="deleteMenu({{ menu.id }})" class="flex-1 bg-red-600 text-white py-2 rounded text-sm hover:bg-red-700">Hapus</button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Add/Edit Modal -->
    <div id="menuModal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
        <div class="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 id="modalTitle" class="text-xl font-bold mb-4">Tambah Menu</h2>
            <form id="menuForm">
                <input type="hidden" id="menuId">
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Nama Menu</label>
                    <input type="text" id="menuName" required class="w-full px-4 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Deskripsi</label>
                    <textarea id="menuDesc" class="w-full px-4 py-2 border rounded-lg"></textarea>
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Harga</label>
                    <input type="number" id="menuPrice" required class="w-full px-4 py-2 border rounded-lg">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Kategori ID</label>
                    <input type="number" id="menuCategory" required class="w-full px-4 py-2 border rounded-lg" value="1">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Stok</label>
                    <input type="number" id="menuStock" class="w-full px-4 py-2 border rounded-lg" value="0">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 mb-2">Image URL</label>
                    <input type="text" id="menuImage" class="w-full px-4 py-2 border rounded-lg">
                </div>
                <div class="flex gap-4">
                    <button type="submit" class="flex-1 bg-amber-600 text-white py-2 rounded-lg hover:bg-amber-700">Simpan</button>
                    <button type="button" onclick="closeModal()" class="flex-1 bg-gray-300 py-2 rounded-lg hover:bg-gray-400">Batal</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function openAddModal() {
    document.getElementById('modalTitle').textContent = 'Tambah Menu';
    document.getElementById('menuForm').reset();
    document.getElementById('menuId').value = '';
    document.getElementById('menuModal').classList.remove('hidden');
}

function openEditModal(menuId) {
    // Fetch menu data and populate form
    fetch(`/api/menus/${menuId}`)
        .then(r => r.json())
        .then(menu => {
            document.getElementById('modalTitle').textContent = 'Edit Menu';
            document.getElementById('menuId').value = menu.id;
            document.getElementById('menuName').value = menu.name;
            document.getElementById('menuDesc').value = menu.description || '';
            document.getElementById('menuPrice').value = menu.price;
            document.getElementById('menuCategory').value = menu.category_id;
            document.getElementById('menuStock').value = menu.stock;
            document.getElementById('menuImage').value = menu.image_url || '';
            document.getElementById('menuModal').classList.remove('hidden');
        });
}

function closeModal() {
    document.getElementById('menuModal').classList.add('hidden');
}

document.getElementById('menuForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const menuId = document.getElementById('menuId').value;
    const data = {
        name: document.getElementById('menuName').value,
        description: document.getElementById('menuDesc').value,
        price: parseFloat(document.getElementById('menuPrice').value),
        category_id: parseInt(document.getElementById('menuCategory').value),
        stock: parseInt(document.getElementById('menuStock').value),
        image_url: document.getElementById('menuImage').value || null
    };

    const url = menuId ? `/api/menus/${menuId}` : '/api/menus';
    const method = menuId ? 'PUT' : 'POST';

    const response = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (response.ok) {
        location.reload();
    } else {
        alert('Gagal menyimpan menu');
    }
});

async function deleteMenu(menuId) {
    if (confirm('Hapus menu ini?')) {
        const response = await fetch(`/api/menus/${menuId}`, { method: 'DELETE' });
        if (response.ok) {
            location.reload();
        } else {
            alert('Gagal menghapus menu');
        }
    }
}
</script>
{% endblock %}
```

**Step 2: Add menu API routes to app/routes/api.py**

Create `app/routes/api.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.menu import Menu
from app.schemas.menu import MenuCreate, MenuUpdate, MenuResponse
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
```

**Step 3: Commit**

```bash
git add app/templates/admin/menus.html app/routes/api.py
git commit -m "feat: add menu management with CRUD API"
```

---

## PHASE 6: Seed Data & Testing

### Task 16: Create seed data script

**Files:**
- Create: `scripts/seed_data.py`

**Step 1: Create scripts directory and seed script**

```bash
mkdir -p /Users/sonyadriko/Projects/SelfCafe-Ordering-System/scripts
```

```python
# scripts/seed_data.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[0]))

from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.menu import Category, Menu
from app.services.auth_service import get_password_hash

def seed():
    db = SessionLocal()

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Seed admin user
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Administrator",
            role=UserRole.ADMIN
        )
        db.add(admin)

    # Seed kasir user
    kasir = db.query(User).filter(User.username == "kasir").first()
    if not kasir:
        kasir = User(
            username="kasir",
            password_hash=get_password_hash("kasir123"),
            full_name="Kasir Utama",
            role=UserRole.KASIR
        )
        db.add(kasir)

    # Seed categories
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

    # Get categories
    coffee_cat = db.query(Category).filter(Category.name == "Coffee").first()
    food_cat = db.query(Category).filter(Category.name == "Food").first()
    snack_cat = db.query(Category).filter(Category.name == "Snack").first()

    # Seed menus
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
```

**Step 2: Commit**

```bash
git add scripts/seed_data.py
git commit -m "feat: add seed data script"
```

---

### Task 17: Create README

**Files:**
- Create: `README.md`

**Step 1: Create README.md**

```markdown
# SelfCafe Ordering System

Sistem pemesanan mandiri untuk coffee shop berbasis web.

## Tech Stack

- FastAPI
- MySQL
- SQLAlchemy ORM
- Jinja2 Templates
- Tailwind CSS

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure database

Copy `.env.example` to `.env` dan sesuaikan:

```bash
cp .env.example .env
```

### 3. Create database

```bash
mysql -u root -p
CREATE DATABASE selfcafe_db;
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Seed data

```bash
python scripts/seed_data.py
```

### 6. Run server

```bash
python run.py
```

Server berjalan di `http://localhost:8000`

## Default Users

- **Admin**: username `admin`, password `admin123`
- **Kasir**: username `kasir`, password `kasir123`

## Access

- **Customer**: `http://localhost:8000/customer?table=1`
- **Admin Login**: `http://localhost:8000/admin/login`
- **API Docs**: `http://localhost:8000/docs`

## Project Structure

```
app/
├── main.py           # FastAPI app
├── config.py         # Configuration
├── database.py       # DB connection
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── routes/           # API routes
├── services/         # Business logic
├── templates/        # Jinja2 templates
└── static/           # CSS, JS, images
```

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions"
```

---

## Summary Checklist

- [x] Project setup
- [x] Database models (User, Menu, Category, Order, OrderItem, Promo)
- [x] Authentication (JWT)
- [x] Customer ordering interface
- [x] Admin dashboard
- [x] Order management
- [x] Menu management
- [x] Seed data
- [x] Documentation

## Next Steps After Implementation

1. Run `alembic upgrade head` to create tables
2. Run `python scripts/seed_data.py` to populate initial data
3. Run `python run.py` to start server
4. Test customer flow at `http://localhost:8000/customer?table=1`
5. Test admin at `http://localhost:8000/admin/login` (admin/admin123)
