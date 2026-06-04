from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base

class Order(Base):
    __tablename__ = "orders"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_name = Column(String(100))
    customer_email = Column(String(100))
    product_asin = Column(String(20))
    product_title = Column(Text)
    quantity = Column(Integer, default=1)
    total_price = Column(Float)
    currency = Column(String(10), default="USD")
    status = Column(String(50), default="Pending")  # Pending, Confirmed, Shipped, Delivered, Cancelled
    shipping_address = Column(Text)
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    delivery_date = Column(String(100), nullable=True)
