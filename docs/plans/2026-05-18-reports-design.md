# Reports Feature Design

**Date:** 2026-05-18
**Feature:** Daily Sales Summary & Best Sellers Reports

## Overview

Add reporting functionality to admin panel for tracking sales performance and popular menu items. Two reports: Daily Sales Summary (revenue metrics) and Best Sellers (top 10 menu items by quantity sold).

## Requirements

### Daily Sales Summary
- Total revenue in date range
- Order count
- Average order value
- Date range filter (start/end date picker)

### Best Sellers Report
- Top 10 menu items by quantity sold
- Show: rank, menu name, category, quantity, revenue
- Date range filter (same as daily sales)

### UI Requirements
- New "Reports" page in admin panel
- Tab navigation between Daily Sales and Best Sellers
- Date range picker (Flatpickr)
- Mastercard design system styling
- Admin/Kasir role access only

## Architecture

### Backend

**New Route:** `app/routes/reports.py`

Endpoints:
- `GET /admin/reports` - Main reports page (HTML)
- Query params: `?start=YYYY-MM-DD&end=YYYY-MM-DD&tab=daily-sales|best-sellers`

**Database Queries:**

Daily Sales:
```sql
SELECT
    SUM(total_amount) as total_revenue,
    COUNT(*) as order_count,
    AVG(total_amount) as avg_order_value
FROM orders
WHERE created_at BETWEEN start_date AND end_date
AND status IN ('paid', 'completed')
```

Best Sellers:
```sql
SELECT
    m.name,
    c.name as category,
    SUM(oi.quantity) as quantity_sold,
    SUM(oi.subtotal) as total_revenue
FROM order_items oi
JOIN menus m ON oi.menu_id = m.id
JOIN categories c ON m.category_id = c.id
JOIN orders o ON oi.order_id = o.id
WHERE o.created_at BETWEEN start_date AND end_date
AND o.status IN ('paid', 'completed')
GROUP BY m.id
ORDER BY quantity_sold DESC
LIMIT 10
```

### Frontend

**Template:** `app/templates/admin/reports.html`

Structure:
- Tab navigation (Daily Sales / Best Sellers)
- Date range form (2 date inputs + submit button)
- Results section (conditional based on active tab)
- Chart.js visualization

**Sidebar Update:** Add "Reports" menu item in `app/templates/admin/sidebar.html`

### Data Structures

**Daily Sales Response:**
```python
{
    "total_revenue": Decimal,
    "order_count": int,
    "average_order_value": Decimal,
    "date_range": {
        "start": date,
        "end": date
    }
}
```

**Best Sellers Response:**
```python
[
    {
        "rank": int,
        "menu_name": str,
        "category_name": str,
        "quantity_sold": int,
        "total_revenue": Decimal
    },
    # ... top 10
]
```

## Components

### Reports Router (`app/routes/reports.py`)

Functions:
- `reports_page()` - Main handler, renders template with data
- `get_daily_sales(db, start_date, end_date)` - Query daily sales metrics
- `get_best_sellers(db, start_date, end_date)` - Query top 10 menu items

Authentication: `get_current_user` dependency (JWT)

### Template (`app/templates/admin/reports.html`)

Sections:
1. Header with page title
2. Tab navigation (pills)
3. Date range picker form
4. Daily Sales card (3 metric boxes + optional chart)
5. Best Sellers table + bar chart
6. Empty state messages

Dependencies:
- Flatpickr CSS/JS (date picker)
- Chart.js (visualizations)

## Error Handling

**Validation:**
- Start date <= end date (return 400 if invalid)
- Max range: 90 days (prevent expensive queries)
- Date format: YYYY-MM-DD (validate with Pydantic)

**Edge Cases:**
- No orders in range: display "No data available"
- Zero revenue: show "Rp 0"
- Database errors: catch exceptions, log, return 500

**Performance:**
- Add index on `orders.created_at` if missing
- Use SQLAlchemy aggregation functions (not Python loops)

## UI Design

### Layout
- Sidebar: existing Ink Black `#141413`
- Main content: Canvas Cream `#F3F0EE` background
- Cards: White with 40px radius (stadium shape)

### Daily Sales Card
- Three metric boxes in row
- Large number: 36px, weight 500, Ink Black
- Small label: 14px, weight 450, Slate Gray

### Best Sellers Table
- Headers: Rank | Menu Name | Category | Quantity | Revenue
- Top 3 rows: subtle Coffee Medium `#6F4E37` background
- Alternating row colors for readability

### Charts (Chart.js)
- Horizontal bar chart for best sellers
- Bar color: Coffee Medium `#6F4E37`
- Minimal styling, clean axes

### Responsive
- Desktop: side-by-side metrics
- Mobile: stacked metrics, horizontal scroll table

## Implementation Approach

**Backend-heavy with server-side rendering:**
- FastAPI endpoints return data + render Jinja2 templates
- Minimal JS (date picker + Chart.js only)
- Form submit triggers page reload with query params
- Consistent with existing admin pages architecture

**Why this approach:**
- Matches existing codebase patterns (all admin pages use Jinja2)
- Simple, fast to implement
- Sufficient for report requirements
- Can upgrade to API-first later if needed

## Dependencies

**Python packages (already installed):**
- FastAPI
- SQLAlchemy
- Jinja2

**Frontend libraries (CDN):**
- Flatpickr 4.6.13 (date picker)
- Chart.js 4.4.0 (charts)

## Testing Considerations

**Manual testing:**
- Date range validation (invalid dates, start > end, >90 days)
- Empty results (no orders in range)
- Large datasets (performance with many orders)
- Role permissions (admin/kasir can access, customer cannot)
- Responsive layout (mobile/tablet/desktop)

**Edge cases:**
- Orders with status 'pending' or 'cancelled' excluded from reports
- Decimal precision for currency (2 decimal places)
- Timezone handling (use server timezone consistently)

## Future Enhancements

Not in scope for initial implementation:
- Export to PDF/Excel
- Payment method breakdown
- Peak hours analysis
- Category performance comparison
- Month-over-month trends
- Real-time updates (WebSocket)

These can be added incrementally based on user feedback.
