from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import pg_engine, my_engine, Base
from .models import Product, ChatHistory
from .models_mysql import Order
from .routes import products, orders, chat

app = FastAPI(title="AI Shopping Cart API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=pg_engine)
    Base.metadata.create_all(bind=my_engine)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(chat.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI-shopping-cart"}
