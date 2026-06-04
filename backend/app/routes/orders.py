from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_my_db
from ..models_mysql import Order
from ..schemas import OrderResponse, OrderListResponse, OrderCreate

router = APIRouter(prefix="/api/orders", tags=["Orders"])

@router.get("", response_model=OrderListResponse)
def list_orders(db: Session = Depends(get_my_db)):
    orders = db.query(Order).order_by(Order.order_date.desc()).all()
    return OrderListResponse(total=len(orders), orders=orders)

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_my_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.get("/email/{email}", response_model=OrderListResponse)
def get_orders_by_email(email: str, db: Session = Depends(get_my_db)):
    orders = db.query(Order).filter(Order.customer_email == email).order_by(Order.order_date.desc()).all()
    return OrderListResponse(total=len(orders), orders=orders)

@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_my_db)):
    db_order = Order(
        customer_name=order.customer_name,
        customer_email=order.customer_email,
        product_asin=order.product_asin,
        product_title=order.product_title,
        quantity=order.quantity,
        total_price=order.total_price,
        currency=order.currency,
        status="Confirmed",
        shipping_address=order.shipping_address,
        delivery_date="5-7 business days"
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order
