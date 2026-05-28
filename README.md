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

> **Note:** `bcrypt` dipinned ke versi `3.2.2` karena `passlib 1.7.4` tidak kompatibel dengan `bcrypt >= 4.0` (akan muncul error `ValueError: password cannot be longer than 72 bytes`).

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
# selfcafe
