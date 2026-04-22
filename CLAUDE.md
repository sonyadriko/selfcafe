# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SelfCafe Ordering System is a web-based self-ordering system for coffee shops (Sowan Kopi). Built with FastAPI + MySQL + Jinja2, following a Waterfall development model as documented in the thesis.

**Core flow:** Customer scans QR code → browses menu → places order → Kasir confirms payment → Order completed.

## Development Commands

### Server
```bash
python run.py                    # Start development server (uvicorn)
uvicorn app.main:app --reload  # Alternative with hot reload
```

### Database
```bash
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head             # Apply migrations
alembic downgrade -1             # Rollback last migration
```

### Seed Data
```bash
PYTHONPATH=. python3 scripts/seed_data.py  # Populate initial data
```

### Docker
```bash
docker-compose up --build        # Build and start all services
docker-compose exec db mysql -u root -p  # Access MySQL shell
docker-compose exec app alembic upgrade head  # Run migrations in container
docker-compose exec app python scripts/seed_data.py  # Seed in container
```

### Testing (if pytest is configured)
```bash
pytest                            # Run all tests
pytest tests/test_customer.py    # Run specific test file
pytest -v                         # Verbose output
```

## Architecture

### Layer Structure
```
routes/ (FastAPI routers) → services/ (business logic) → models/ (SQLAlchemy) → database/
                            ↓
                         schemas/ (Pydantic validation)
```

### Key Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app, includes all routers, mounts static/templates |
| `app/config.py` | Pydantic Settings with environment variable support |
| `app/database.py` | SQLAlchemy engine, SessionLocal, get_db() dependency |
| `app/dependencies.py` | Auth: get_current_user (JWT), require_role() helper |
| `app/services/auth_service.py` | Password hashing (bcrypt), JWT token creation/verification |

### Routes Organization

- **auth** (`/auth/*`) - Login page, POST login (sets JWT cookie), logout
- **customer** (`/customer/*`) - Ordering interface, menu API, order creation
- **admin** (`/admin/*`) - Dashboard, orders list, menu management (all JWT protected)
- **api** (`/api/*`) - JSON API for menu CRUD (JWT protected)

### Models (SQLAlchemy)

- **User** - Admin/Staff/Kasir roles with bcrypt password hashing
- **Category/Menu** - Menu items with categories, stock tracking
- **Order/OrderItem** - Orders with status (pending/paid/completed/cancelled)
- **Promo** - Discounts (percentage/fixed) with date ranges

### Authentication Flow

1. User POSTs to `/auth/login` with username/password
2. `authenticate_user()` verifies credentials via bcrypt
3. `create_access_token()` generates JWT (60min expiry)
4. Response sets `access_token` cookie (httponly)
5. Protected routes use `get_current_user` dependency (validates JWT via HTTPBearer)
6. `require_role("admin", "kasir")` for role-based access

### Design System

**Mastercard-inspired design** - see `design.md` for full specification.

**Key colors (all in `app/static/css/design-system.css`):**
- Canvas Cream `#F3F0EE` - default background
- Ink Black `#141413` - primary text, CTAs
- Coffee Medium `#6F4E37` - brand accent (add button)
- Signal Orange `#CF4500` - consent/alert actions only

**Typography:**
- Font: Inter (substitute for proprietary MarkForMC)
- Weights: 450 (body), 500 (headlines), 700 (eyebrow/labels)
- Letter-spacing: -2% on headlines for tight editorial feel

**Components:**
- Pill buttons: 20px radius (primary/secondary), 24px (signal), 999px (full pill)
- Cards: 40px radius stadium shapes, soft shadows `rgba(0,0,0,0.08) 0px 24px 48px`
- Sidebar: Ink black background, 280px width fixed
- Modal: White card with header/body/footer structure

### Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Kasir | kasir | kasir123 |

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=selfcafe_db
SECRET_KEY=change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_NAME=SelfCafe Ordering
DEBUG=True
```

## Project Context

This is a thesis project implementing a self-ordering system following Waterfall methodology. The scope is intentionally focused: ordering and transaction recording only. It does NOT include accounting, HPP calculation, or financial reconciliation.

The design system follows Mastercard's visual language as specified in `design.md` - warm cream backgrounds, pill-shaped elements, soft shadows, and Inter typography.
