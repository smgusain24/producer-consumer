from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship

from app.database.db import Base


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True, nullable=False)
    vendor_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    high_value = Column(Boolean, nullable=False)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sku = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="items")
