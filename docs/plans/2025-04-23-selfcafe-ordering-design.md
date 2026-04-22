# SelfCafe Ordering System - Design Document

**Date**: 2025-04-23
**Project**: Sowan Kopi Self-Ordering System
**Model**: Waterfall

## 1. Overview

Web-based self-ordering system for Sowan Kopi coffee shop. Customers scan QR code at table, browse menu, place orders. Cashier confirms payment. Staff manages menu and monitors orders.

## 2. Users

| Role | Description |
|------|-------------|
| Pelanggan | Scan QR, browse menu, place orders |
| Kasir | View pending orders, confirm payments |
| Staff/Admin | Manage menu, promos, view all orders |

## 3. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Routes/Endpoints                       │  │
│  │  /customer/*  → Pesan, view menu, QR scan          │  │
│  │  /admin/*     → Manage menu, promo, users          │  │
│  │  /api/*       → JSON API untuk mobile/extension    │  │
│  │  /auth/*      → Login, logout, JWT refresh         │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Services Layer                         │  │
│  │  OrderService, MenuService, AuthService            │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Templates (Jinja2)                     │  │
│  │  customer/, admin/, auth/, components/             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │      MySQL Database   │
              │  users, menus, orders,│
              │  order_items, promos  │
              └───────────────────────┘
```

## 4. Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI + Uvicorn |
| Database | MySQL + SQLAlchemy (ORM) |
| Auth | JWT (python-jose) |
| Templates | Jinja2 |
| Styling | Tailwind CSS (CDN) |
| Migrations | Alembic |
| Password Hashing | bcrypt |

## 5. Database Schema

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │     menus       │     │    orders       │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ id (PK)         │     │ id (PK)         │
│ username        │     │ name            │     │ table_number    │
│ password_hash   │     │ description     │     │ user_id (FK)    │◄────┐
│ full_name       │     │ price           │     │ total_amount    │     │
│ role            │     │ image_url       │     │ status          │     │
│ created_at      │     │ category_id     │     │ created_at      │     │
└─────────────────┘     │ stock           │     │ updated_at      │     │
                        │ is_active       │     └─────────────────┘     │
                        │ created_at      │              │               │
                        └─────────────────┘              │               │
                                │                        │               │
┌─────────────────┐     ┌─────────────────┐              │               │
│   categories    │     │  order_items    │◄─────────────┘               │
├─────────────────┤     ├─────────────────┘                              │
│ id (PK)         │     │ id (PK)         │                              │
│ name            │     │ order_id (FK)   │                              │
└─────────────────┘     │ menu_id (FK)    │◄─────────────────────────────┘
                        │ quantity        │
                        │ subtotal        │
                        │ notes           │
                        └─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│     promos      │     │   settings      │
├─────────────────┤     ├─────────────────┤
│ id (PK)         │     │ key (PK)        │
│ name            │     │ value           │
│ discount_type   │     └─────────────────┘
│ discount_value  │
│ min_purchase    │
│ start_date      │
│ end_date        │
│ is_active       │
└─────────────────┘
```

**Roles**: `admin`, `staff`, `kasir`
**Order Status**: `pending`, `paid`, `completed`, `cancelled`

## 6. Core Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/` | Redirect ke `/customer` | - |
| GET | `/customer` | Halaman pesan (scan QR) | - |
| GET | `/customer/menu` | List menu JSON | - |
| POST | `/customer/order` | Buat order | - |
| GET | `/admin/login` | Login page | - |
| POST | `/auth/login` | Login, return JWT | - |
| GET | `/admin/dashboard` | Dashboard admin | JWT |
| GET | `/admin/orders` | List semua orders | JWT |
| PUT | `/admin/orders/{id}/status` | Update status | JWT |
| GET | `/admin/menus` | Manage menu | JWT |
| POST | `/admin/menus` | Tambah menu | JWT |
| PUT | `/admin/menus/{id}` | Edit menu | JWT |
| DELETE | `/admin/menus/{id}` | Hapus menu | JWT |

## 7. User Flows

### Pelanggan Flow
1. Scan QR di meja → `/customer?table=X`
2. Pilih menu, masuk keranjang
3. Submit order → status `pending`
4. Tunggu di meja, kasir konfirmasi bayar
5. Status berubah jadi `paid` → `completed`

### Kasir Flow
1. Login `/admin/login`
2. Lihat list order pending
3. Hitung total, terima pembayaran
4. Update status → `paid`

### Admin Flow
1. Login `/admin/login`
2. Kelola menu (CRUD)
3. Atur promo
4. Monitor orders
5. Laporan sederhana

## 8. Project Structure

```
selfcafe-ordering/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app init
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── menu.py
│   │   ├── order.py
│   │   └── promo.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── menu.py
│   │   └── order.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── customer.py
│   │   ├── admin.py
│   │   └── api.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── order_service.py
│   │   └── menu_service.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── customer/
│   │   │   ├── index.html
│   │   │   └── cart.html
│   │   └── admin/
│   │       ├── login.html
│   │       ├── dashboard.html
│   │       ├── orders.html
│   │       └── menus.html
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── alembic/                  # Database migrations
├── tests/
├── requirements.txt
├── .env
└── run.py
```

## 9. Security

- Password hashing dengan bcrypt
- JWT token untuk authentication
- Role-based access control
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration for API endpoints

## 10. Success Criteria

- Pelanggan bisa scan QR dan pesan mandiri
- Kasir bisa view dan konfirmasi pembayaran
- Admin bisa kelola menu dan promo
- Status order ter-track dengan benar
- Sistem responsive (mobile-friendly)

## 11. Out of Scope

- Sistem akuntansi lengkap
- Perhitungan HPP
- Rekonsiliasi laporan keuangan
- Payment gateway integration
- Mobile native app
