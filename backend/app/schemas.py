from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

# Product schemas
class ProductResponse(BaseModel):
    id: int
    asin: str
    product_title: str
    product_price: Optional[str] = None
    product_original_price: Optional[str] = None
    currency: Optional[str] = "USD"
    product_star_rating: Optional[float] = None
    product_num_ratings: Optional[int] = None
    product_url: Optional[str] = None
    product_photo: Optional[str] = None
    product_minimum_offer_price: Optional[str] = None
    is_best_seller: Optional[str] = "False"
    is_amazon_choice: Optional[str] = "False"
    is_prime: Optional[str] = "False"
    sales_volume: Optional[str] = None
    product_availability: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    total: int
    products: list[ProductResponse]

# Order schemas
class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    product_asin: str
    product_title: str
    quantity: int
    total_price: float
    currency: str
    status: str
    shipping_address: str
    order_date: Optional[datetime] = None
    delivery_date: Optional[str] = None
    
    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    product_asin: str
    product_title: str
    quantity: int = 1
    total_price: float
    currency: str = "USD"
    shipping_address: str

class OrderListResponse(BaseModel):
    total: int
    orders: list[OrderResponse]

# Chat schemas
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class GuardrailInfo(BaseModel):
    name: str
    passed: bool

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    inbound_guardrails: list[GuardrailInfo]
    outbound_guardrails: list[GuardrailInfo]
    show_order_button: bool = False
