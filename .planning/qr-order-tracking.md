# QR Order Tracking System - Implementation Plan

## Overview
Customer places order → gets QR code → shows to cashier → cashier processes payment → customer tracks order status via QR code

## Current State
- Customer orders → PENDING status
- No way for customer to track order
- Cashier has no order reference
- No payment flow

## Target Flow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Customer   │     │   System    │     │   Cashier    │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
  Place Order              Generate QR          Scan QR
       │                   │                   │
       ├──────────────────→│                   │
       │              ┌──────↓──────┐          │
       │              │  Show QR    │          │
       │              │  + Tracking │          │
       │              │    Token    │          │
       │              └──────┬──────┘          │
       │                   │                   │
   Save QR                  │                   │
       │                   │                   │
       ├───────────────────┼───────────────────→
       │                   │              Process
       │                   │              Payment
       │                   │                   │
       ├───────────────────┼───────────────────→
       │                   │              Update:
       │                   │              PENDING→PAID
       │                   │                   │
   Scan QR ───────────────→┴─────────────────────→
       │                   │              Update:
   Check Status         │              PAID→COMPLETED
       │                   │                   │
   See:                 │                   │
   - Order details      │                   │
   - Items              │                   │
   - Status             │                   │
   - Total              │                   │
```

## Technical Changes

### 1. Database Schema
```python
# Add to Order model
tracking_token = Column(String(36), unique=True, nullable=False)  # UUID
```

### 2. New Dependencies
```bash
pip install qrcode[pil]
```

### 3. Backend Changes

#### 3.1 Generate Tracking Token
**File:** `app/services/tracking.py` (new)
- Generate UUID for tracking
- Validate token exists

#### 3.2 Update Order Creation
**File:** `app/routes/customer.py`
- Generate `tracking_token` on order creation
- Return QR code URL in response

#### 3.3 New API Endpoints
```
GET  /customer/qr/{token}        # Generate QR code image
GET  /customer/track/{token}     # Get order status by token
POST /api/cashier/scan          # Cashier: scan QR/retrieve order
PUT  /api/cashier/pay/{order_id} # Cashier: process payment
```

### 4. Frontend Changes

#### 4.1 New Pages
```
app/templates/customer/
├── order-success.html    # Show QR after order
└── track.html            # Order tracking page
```

#### 4.2 Update Customer Flow
- After order → show success page with QR
- QR contains tracking URL
- Customer can save/screenshot QR

### 5. Cashier Interface

#### 5.1 QR Scan/Entry
**Page:** `/cashier` (new)
- Input field: enter tracking token
- Or: scan QR code (optional, camera API)
- Show order details
- Process payment button

## Implementation Steps

### Phase 1: Backend Foundation
- [ ] Add `tracking_token` to Order model
- [ ] Create migration
- [ ] Add `qrcode` to requirements.txt
- [ ] Create tracking service
- [ ] Update order creation to generate token

### Phase 2: API Endpoints
- [ ] QR code generation endpoint
- [ ] Order tracking endpoint
- [ ] Cashier scan/retrieve endpoint
- [ ] Cashier payment endpoint

### Phase 3: Frontend - Customer
- [ ] Order success page with QR
- [ ] Order tracking page
- [ ] Update index.html flow

### Phase 4: Frontend - Cashier
- [ ] Cashier dashboard/page
- [ ] QR scan/entry interface
- [ ] Payment processing UI

### Phase 5: Testing & Polish
- [ ] End-to-end testing
- [ ] QR code generation
- [ ] Mobile responsiveness
- [ ] Error handling

## File Structure (New)
```
app/
├── services/
│   └── tracking.py          # Tracking token service
├── routes/
│   ├── cashier.py           # Cashier endpoints (new)
│   └── customer.py          # Updated with tracking
├── templates/
│   ├── customer/
│   │   ├── order-success.html # New
│   │   ├── track.html        # New
│   │   └── index.html        # Updated
│   └── cashier/
│       └── dashboard.html     # New (QR scan interface)
└── models/
    └── order.py              # Updated (add tracking_token)
```

## Tracking Token Format
- UUID v4 (36 characters)
- Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Stored in `orders.tracking_token`
- Unique per order

## QR Code URL Format
```
https://kopi.com/customer/track/{token}
                                    ↑
                            tracking token
```

## Security Considerations
- Token should be unguessable (UUID)
- No sensitive data in QR code (only token)
- Cashier authentication required for payment
- Rate limiting on QR generation
- Token expires after order completed + 24h (optional)

## Success Metrics
- [ ] Customer can retrieve order status via QR
- [ ] Cashier can retrieve order via token
- [ ] Payment updates order status correctly
- [ ] QR codes are scannable and readable
