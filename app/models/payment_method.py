from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.database import Base

class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
