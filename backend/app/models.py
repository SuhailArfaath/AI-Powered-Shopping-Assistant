from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

# PostgreSQL Models

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asin = Column(String(20), unique=True, index=True)
    product_title = Column(Text)
    product_price = Column(String(50))
    product_original_price = Column(String(50), nullable=True)
    currency = Column(String(10), default="USD")
    product_star_rating = Column(Float, nullable=True)
    product_num_ratings = Column(Integer, nullable=True)
    product_url = Column(Text)
    product_photo = Column(Text)
    product_num_offers = Column(Integer, nullable=True)
    product_minimum_offer_price = Column(String(50), nullable=True)
    is_best_seller = Column(String(10), default="False")
    is_amazon_choice = Column(String(10), default="False")
    is_prime = Column(String(10), default="False")
    climate_pledge_friendly = Column(String(10), default="False")
    sales_volume = Column(String(100), nullable=True)
    delivery = Column(Text, nullable=True)
    has_variations = Column(String(10), default="False")
    product_availability = Column(Text, nullable=True)
    unit_price = Column(String(50), nullable=True)
    unit_count = Column(String(50), nullable=True)


class ChatHistory(Base):
    __tablename__ = "chat_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True)
    role = Column(String(20))  # 'human', 'ai', 'system'
    message = Column(Text)
    inbound_guardrail_hit = Column(String(200), nullable=True)
    outbound_guardrail_hit = Column(String(200), nullable=True)
    guardrail_action = Column(String(50), nullable=True)  # 'passed', 'blocked'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
