#!/usr/bin/env python3
"""Update payment_method for existing orders."""
import sys
sys.path.insert(0, '/Users/sonyadriko/Projects/SelfCafe-Ordering-System')

from app.database import SessionLocal
from app.models.order import Order

db = SessionLocal()
try:
    updated = db.query(Order).filter(
        Order.status.in_(['paid', 'completed']),
        Order.payment_method.is_(None)
    ).update({Order.payment_method: 'cash'})
    db.commit()
    print(f'Updated {updated} orders with payment_method="cash"')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
