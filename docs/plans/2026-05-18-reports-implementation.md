# Reports Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Daily Sales Summary and Best Sellers reports to admin panel with date range filtering.

**Architecture:** Backend-heavy server-side rendering. New FastAPI router with SQLAlchemy queries, Jinja2 template with tabs, Flatpickr date picker, Chart.js visualization. Follows existing admin panel patterns.

**Tech Stack:** FastAPI, SQLAlchemy, Jinja2, Flatpickr 4.6.13, Chart.js 4.4.0

---

## Task 1: Create Reports Router

**Files:**
- Create: `app/routes/reports.py`
- Modify: `app/main.py:20-26` (add router import and include)

**Step 1: Create reports router file**

Create `app/routes/reports.py`:

```python
from fastapi import APIRouter, Depends, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.menu import Menu, Category
from app.models.order import OrderItem

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
```

**Step 2: Add router to main app**

Modify `app/main.py`, add import after line 20:

```python
from app.routes import auth, customer, admin, api, cashier, reports
```

Add router include after line 26:

```python
app.include_router(reports.router, prefix="/admin", tags=["reports"])
```

**Step 3: Verify imports work**

Run: `python -c "from app.routes import reports; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add app/routes/reports.py app/main.py
git commit -m "feat: add reports router skeleton"
```

---

## Task 2: Implement Daily Sales Query Function

**Files:**
- Modify: `app/routes/reports.py` (add function)

**Step 1: Add daily sales query function**

Add to `app/routes/reports.py`:

```python
def get_daily_sales_data(db: Session, start_date: date, end_date: date) -> dict:
    """Query daily sales metrics for date range."""

    # Query orders in date range with paid/completed status
    orders = db.query(Order).filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED])
    ).all()

    if not orders:
        return {
            "total_revenue": Decimal("0.00"),
            "order_count": 0,
            "average_order_value": Decimal("0.00"),
            "date_range": {"start": start_date, "end": end_date}
        }

    total_revenue = sum(order.total_amount for order in orders)
    order_count = len(orders)
    average_order_value = total_revenue / order_count if order_count > 0 else Decimal("0.00")

    return {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "date_range": {"start": start_date, "end": end_date}
    }
```

**Step 2: Test function manually**

Run Python shell:
```python
from app.database import SessionLocal
from app.routes.reports import get_daily_sales_data
from datetime import date

db = SessionLocal()
result = get_daily_sales_data(db, date.today(), date.today())
print(result)
db.close()
```

Expected: Dictionary with keys `total_revenue`, `order_count`, `average_order_value`, `date_range`

**Step 3: Commit**

```bash
git add app/routes/reports.py
git commit -m "feat: add daily sales query function"
```

---

## Task 3: Implement Best Sellers Query Function

**Files:**
- Modify: `app/routes/reports.py` (add function)

**Step 1: Add best sellers query function**

Add to `app/routes/reports.py`:

```python
def get_best_sellers_data(db: Session, start_date: date, end_date: date) -> list:
    """Query top 10 best selling menu items for date range."""

    # Join order_items with menus and orders, filter by date and status
    results = db.query(
        Menu.name.label("menu_name"),
        Category.name.label("category_name"),
        func.sum(OrderItem.quantity).label("quantity_sold"),
        func.sum(OrderItem.subtotal).label("total_revenue")
    ).join(
        OrderItem, Menu.id == OrderItem.menu_id
    ).join(
        Order, OrderItem.order_id == Order.id
    ).join(
        Category, Menu.category_id == Category.id
    ).filter(
        func.date(Order.created_at) >= start_date,
        func.date(Order.created_at) <= end_date,
        Order.status.in_([OrderStatus.PAID, OrderStatus.COMPLETED])
    ).group_by(
        Menu.id, Menu.name, Category.name
    ).order_by(
        desc("quantity_sold")
    ).limit(10).all()

    # Format results with rank
    best_sellers = []
    for rank, row in enumerate(results, start=1):
        best_sellers.append({
            "rank": rank,
            "menu_name": row.menu_name,
            "category_name": row.category_name,
            "quantity_sold": int(row.quantity_sold),
            "total_revenue": row.total_revenue
        })

    return best_sellers
```

**Step 2: Test function manually**

Run Python shell:
```python
from app.database import SessionLocal
from app.routes.reports import get_best_sellers_data
from datetime import date

db = SessionLocal()
result = get_best_sellers_data(db, date.today(), date.today())
print(result)
db.close()
```

Expected: List of dictionaries with rank, menu_name, category_name, quantity_sold, total_revenue

**Step 3: Commit**

```bash
git add app/routes/reports.py
git commit -m "feat: add best sellers query function"
```

---

## Task 4: Create Reports Page Endpoint

**Files:**
- Modify: `app/routes/reports.py` (add endpoint)

**Step 1: Add reports page endpoint**

Add to `app/routes/reports.py`:

```python
@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    tab: Optional[str] = Query("daily-sales"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reports page with daily sales and best sellers."""

    # Default to today if no dates provided
    if not start or not end:
        today = date.today()
        start_date = today
        end_date = today
    else:
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except ValueError:
            # Invalid date format, default to today
            today = date.today()
            start_date = today
            end_date = today

    # Validate date range
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Max 90 days range
    if (end_date - start_date).days > 90:
        end_date = start_date + timedelta(days=90)

    # Get data based on active tab
    daily_sales = None
    best_sellers = None

    if tab == "daily-sales":
        daily_sales = get_daily_sales_data(db, start_date, end_date)
    elif tab == "best-sellers":
        best_sellers = get_best_sellers_data(db, start_date, end_date)

    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "active_tab": tab,
        "daily_sales": daily_sales,
        "best_sellers": best_sellers
    })
```

**Step 2: Verify endpoint registered**

Run: `python -c "from app.main import app; print([r.path for r in app.routes if 'reports' in r.path])"`
Expected: `['/admin/reports']`

**Step 3: Commit**

```bash
git add app/routes/reports.py
git commit -m "feat: add reports page endpoint with date validation"
```

---

## Task 5: Create Reports Template

**Files:**
- Create: `app/templates/admin/reports.html`

**Step 1: Create reports template**

Create `app/templates/admin/reports.html`:

```html
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reports - SelfCafe Admin</title>
    <link rel="stylesheet" href="/static/css/design-system.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.css">
    <style>
        body {
            display: flex;
            margin: 0;
            background: #F3F0EE;
            font-family: Inter, sans-serif;
        }

        .main-content {
            margin-left: 280px;
            padding: 40px;
            width: calc(100% - 280px);
        }

        .page-header {
            margin-bottom: 32px;
        }

        .page-title {
            font-size: 36px;
            font-weight: 500;
            color: #141413;
            letter-spacing: -0.02em;
            margin: 0;
        }

        .tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 24px;
        }

        .tab-button {
            padding: 8px 24px;
            border-radius: 20px;
            border: 1.5px solid #141413;
            background: white;
            color: #141413;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
        }

        .tab-button.active {
            background: #141413;
            color: #F3F0EE;
        }

        .date-filter {
            background: white;
            padding: 24px;
            border-radius: 40px;
            margin-bottom: 24px;
            box-shadow: rgba(0,0,0,0.08) 0px 24px 48px;
        }

        .date-filter form {
            display: flex;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
        }

        .date-input-group {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .date-input-group label {
            font-size: 14px;
            font-weight: 500;
            color: #141413;
        }

        .date-input-group input {
            padding: 8px 16px;
            border: 1.5px solid #141413;
            border-radius: 20px;
            font-size: 16px;
            font-family: Inter, sans-serif;
        }

        .submit-button {
            padding: 8px 24px;
            border-radius: 20px;
            background: #141413;
            color: #F3F0EE;
            border: none;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            margin-top: 20px;
        }

        .report-card {
            background: white;
            padding: 32px;
            border-radius: 40px;
            box-shadow: rgba(0,0,0,0.08) 0px 24px 48px;
            margin-bottom: 24px;
        }

        .metrics-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }

        .metric-box {
            text-align: center;
        }

        .metric-value {
            font-size: 36px;
            font-weight: 500;
            color: #141413;
            margin: 0 0 8px 0;
        }

        .metric-label {
            font-size: 14px;
            font-weight: 450;
            color: #696969;
            margin: 0;
        }

        .table-container {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th {
            text-align: left;
            padding: 12px;
            font-size: 14px;
            font-weight: 700;
            color: #141413;
            border-bottom: 2px solid #F3F0EE;
        }

        td {
            padding: 12px;
            font-size: 16px;
            font-weight: 450;
            color: #141413;
            border-bottom: 1px solid #F3F0EE;
        }

        tr.top-3 {
            background: rgba(111, 78, 55, 0.05);
        }

        .empty-state {
            text-align: center;
            padding: 48px;
            color: #696969;
            font-size: 16px;
        }

        .chart-container {
            margin-top: 32px;
            height: 400px;
        }

        @media (max-width: 768px) {
            .main-content {
                margin-left: 0;
                width: 100%;
                padding: 20px;
            }

            .metrics-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    {% include "admin/sidebar.html" %}

    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Reports</h1>
        </div>

        <div class="tabs">
            <a href="/admin/reports?start={{ start_date }}&end={{ end_date }}&tab=daily-sales"
               class="tab-button {% if active_tab == 'daily-sales' %}active{% endif %}">
                Daily Sales
            </a>
            <a href="/admin/reports?start={{ start_date }}&end={{ end_date }}&tab=best-sellers"
               class="tab-button {% if active_tab == 'best-sellers' %}active{% endif %}">
                Best Sellers
            </a>
        </div>

        <div class="date-filter">
            <form method="get" action="/admin/reports">
                <input type="hidden" name="tab" value="{{ active_tab }}">

                <div class="date-input-group">
                    <label for="start">Start Date</label>
                    <input type="text" id="start" name="start" value="{{ start_date }}" required>
                </div>

                <div class="date-input-group">
                    <label for="end">End Date</label>
                    <input type="text" id="end" name="end" value="{{ end_date }}" required>
                </div>

                <button type="submit" class="submit-button">Apply Filter</button>
            </form>
        </div>

        {% if active_tab == 'daily-sales' and daily_sales %}
        <div class="report-card">
            <div class="metrics-row">
                <div class="metric-box">
                    <p class="metric-value">Rp {{ "{:,.0f}".format(daily_sales.total_revenue) }}</p>
                    <p class="metric-label">Total Revenue</p>
                </div>
                <div class="metric-box">
                    <p class="metric-value">{{ daily_sales.order_count }}</p>
                    <p class="metric-label">Order Count</p>
                </div>
                <div class="metric-box">
                    <p class="metric-value">Rp {{ "{:,.0f}".format(daily_sales.average_order_value) }}</p>
                    <p class="metric-label">Average Order Value</p>
                </div>
            </div>
        </div>
        {% endif %}

        {% if active_tab == 'best-sellers' and best_sellers %}
        <div class="report-card">
            {% if best_sellers|length > 0 %}
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Menu Name</th>
                            <th>Category</th>
                            <th>Quantity Sold</th>
                            <th>Revenue</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for item in best_sellers %}
                        <tr {% if item.rank <= 3 %}class="top-3"{% endif %}>
                            <td>{{ item.rank }}</td>
                            <td>{{ item.menu_name }}</td>
                            <td>{{ item.category_name }}</td>
                            <td>{{ item.quantity_sold }}</td>
                            <td>Rp {{ "{:,.0f}".format(item.total_revenue) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="chart-container">
                <canvas id="bestSellersChart"></canvas>
            </div>
            {% else %}
            <div class="empty-state">
                No data available for selected date range
            </div>
            {% endif %}
        </div>
        {% endif %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/flatpickr@4.6.13/dist/flatpickr.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script>
        // Initialize date pickers
        flatpickr("#start", {
            dateFormat: "Y-m-d",
            maxDate: "today"
        });

        flatpickr("#end", {
            dateFormat: "Y-m-d",
            maxDate: "today"
        });

        // Initialize chart for best sellers
        {% if active_tab == 'best-sellers' and best_sellers and best_sellers|length > 0 %}
        const ctx = document.getElementById('bestSellersChart');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [
                    {% for item in best_sellers %}
                    "{{ item.menu_name }}"{% if not loop.last %},{% endif %}
                    {% endfor %}
                ],
                datasets: [{
                    label: 'Quantity Sold',
                    data: [
                        {% for item in best_sellers %}
                        {{ item.quantity_sold }}{% if not loop.last %},{% endif %}
                        {% endfor %}
                    ],
                    backgroundColor: '#6F4E37',
                    borderRadius: 8
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
        {% endif %}
    </script>
</body>
</html>
```

**Step 2: Verify template syntax**

Run: `python -c "from jinja2 import Template; Template(open('app/templates/admin/reports.html').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add app/templates/admin/reports.html
git commit -m "feat: add reports template with tabs and charts"
```

---

## Task 6: Update Sidebar Navigation

**Files:**
- Modify: `app/templates/admin/sidebar.html`

**Step 1: Read current sidebar**

Run: `cat app/templates/admin/sidebar.html | grep -A 5 "nav-link"`

**Step 2: Add Reports menu item**

Add after the existing menu items (before closing `</nav>` or similar):

```html
<a href="/admin/reports" class="nav-link">
    <span class="nav-icon">📊</span>
    <span class="nav-text">Reports</span>
</a>
```

**Step 3: Test navigation**

Run server: `python run.py`
Visit: `http://localhost:8000/admin/dashboard`
Expected: See "Reports" link in sidebar

**Step 4: Commit**

```bash
git add app/templates/admin/sidebar.html
git commit -m "feat: add Reports menu item to admin sidebar"
```

---

## Task 7: Add Database Index for Performance

**Files:**
- Create: `alembic/versions/XXXX_add_orders_created_at_index.py`

**Step 1: Create migration**

Run: `alembic revision -m "add index on orders.created_at"`

**Step 2: Edit migration file**

Find the generated file in `alembic/versions/`, edit:

```python
def upgrade():
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])

def downgrade():
    op.drop_index('idx_orders_created_at', 'orders')
```

**Step 3: Apply migration**

Run: `alembic upgrade head`
Expected: Migration applied successfully

**Step 4: Verify index created**

Run: `mysql -u root -p selfcafe_db -e "SHOW INDEX FROM orders WHERE Key_name='idx_orders_created_at';"`
Expected: Index listed

**Step 5: Commit**

```bash
git add alembic/versions/*
git commit -m "perf: add index on orders.created_at for reports"
```

---

## Task 8: Manual Testing

**Files:**
- None (testing only)

**Step 1: Start server**

Run: `python run.py`

**Step 2: Test Daily Sales tab**

1. Visit: `http://localhost:8000/admin/reports`
2. Login as admin (admin/admin123)
3. Verify default shows today's data
4. Change date range, click Apply Filter
5. Verify metrics update correctly
6. Test edge cases:
   - Start date > end date (should swap)
   - Range > 90 days (should cap at 90)
   - No orders in range (should show Rp 0)

**Step 3: Test Best Sellers tab**

1. Click "Best Sellers" tab
2. Verify table shows top 10 items
3. Verify top 3 rows highlighted
4. Verify chart displays correctly
5. Test with different date ranges

**Step 4: Test responsive layout**

1. Resize browser to mobile width
2. Verify metrics stack vertically
3. Verify table scrolls horizontally

**Step 5: Document any issues**

Create file `docs/testing-notes.md` if issues found.

---

## Task 9: Final Commit and Cleanup

**Files:**
- All modified files

**Step 1: Check git status**

Run: `git status`
Expected: All changes committed

**Step 2: Run final verification**

Run: `python -c "from app.main import app; print('Routes:', len(app.routes))"`
Expected: Route count increased

**Step 3: Create final summary commit if needed**

If any loose changes:
```bash
git add .
git commit -m "chore: final cleanup for reports feature"
```

**Step 4: Verify all tests pass**

Run: `python run.py` and manually test all features

---

## Completion Checklist

- [ ] Reports router created and registered
- [ ] Daily sales query function implemented
- [ ] Best sellers query function implemented
- [ ] Reports page endpoint with date validation
- [ ] Reports template with tabs and charts
- [ ] Sidebar navigation updated
- [ ] Database index added for performance
- [ ] Manual testing completed
- [ ] All changes committed

## Notes

- No automated tests in this codebase yet (per CLAUDE.md)
- Manual testing required for all features
- Date picker uses Flatpickr CDN (no npm install needed)
- Chart.js uses CDN (no npm install needed)
- All styling follows Mastercard design system from design-system.css
