"""
Tracking service for QR code order tracking.

Generates and validates tracking tokens for orders.
"""
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models.order import Order


def generate_tracking_token() -> str:
    """Generate a unique tracking token (UUID v4)."""
    return str(uuid.uuid4())


def get_order_by_token(db: Session, token: str) -> Optional[Order]:
    """Retrieve order by tracking token."""
    return db.query(Order).filter(Order.tracking_token == token).first()


def validate_token(db: Session, token: str) -> bool:
    """Check if tracking token exists and is valid."""
    return db.query(Order).filter(Order.tracking_token == token).first() is not None
