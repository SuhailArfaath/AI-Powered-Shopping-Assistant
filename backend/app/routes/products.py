from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_pg_db
from ..models import Product
from ..schemas import ProductResponse, ProductListResponse

router = APIRouter(prefix="/api/products", tags=["Products"])

@router.get("", response_model=ProductListResponse)
def list_products(
    search: Optional[str] = Query(None, description="Search in product title"),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_pg_db),
):
    query = db.query(Product)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Product.product_title.ilike(search_term) |
            Product.asin.ilike(search_term)
        )
    
    if min_rating:
        query = query.filter(Product.product_star_rating >= min_rating)
    
    total = query.count()
    products = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return ProductListResponse(total=total, products=products)

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_pg_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
