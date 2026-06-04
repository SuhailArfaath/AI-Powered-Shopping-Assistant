"""
Seed script to load product data from CSV and create sample orders.
"""
import csv
import re
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://ai:aishop123@localhost:5432/ai_shop")
MYSQL_URL = os.getenv("MYSQL_URL", "mysql+pymysql://ai:aishop123@localhost:3307/ai_orders")

def clean_price(price_str: str) -> str:
    if not price_str or price_str.strip() == "":
        return None
    price_str = price_str.replace("$", "").replace(",", "").strip()
    return price_str

def clean_float(val: str) -> float:
    if not val or val.strip() == "" or val.strip() == "-":
        return None
    try:
        return float(val.replace("$", "").replace(",", ""))
    except:
        return None

def clean_int(val: str) -> int:
    if not val or val.strip() == "" or val.strip() == "-":
        return None
    try:
        return int(float(val))
    except:
        return None

def seed_products():
    """Load products from CSV into PostgreSQL."""
    print("Seeding products into PostgreSQL...")
    
    # Try various CSV paths
    csv_paths = [
        "/app/amazon_product.csv",
        "/data/amazon_product.csv",
        "D:/AI Projects/amazon_product.csv",
        "D:\\AI Projects\\amazon_product.csv",
    ]
    
    # Also check mounted volume
    for p in ["/host_data/amazon_product.csv", "/data/amazon_product.csv", "/app/amazon_product.csv"]:
        if os.path.exists(p):
            csv_paths.insert(0, p)
    
    csv_path = None
    for p in csv_paths:
        if os.path.exists(p):
            csv_path = p
            print(f"Found CSV at: {p}")
            break
    
    if not csv_path:
        print("ERROR: Could not find amazon_product.csv. Checked paths:")
        for p in csv_paths:
            print(f"  - {p} (exists: {os.path.exists(p)})")
        return False
    
    engine = create_engine(POSTGRES_URL)
    
    # Create products table
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                asin VARCHAR(20) UNIQUE,
                product_title TEXT,
                product_price VARCHAR(50),
                product_original_price VARCHAR(50),
                currency VARCHAR(10) DEFAULT 'USD',
                product_star_rating FLOAT,
                product_num_ratings INTEGER,
                product_url TEXT,
                product_photo TEXT,
                product_num_offers INTEGER,
                product_minimum_offer_price VARCHAR(50),
                is_best_seller VARCHAR(10) DEFAULT 'False',
                is_amazon_choice VARCHAR(10) DEFAULT 'False',
                is_prime VARCHAR(10) DEFAULT 'False',
                climate_pledge_friendly VARCHAR(10) DEFAULT 'False',
                sales_volume VARCHAR(100),
                delivery TEXT,
                has_variations VARCHAR(10) DEFAULT 'False',
                product_availability TEXT,
                unit_price VARCHAR(50),
                unit_count VARCHAR(50)
            )
        """))
        conn.commit()
    
    with engine.connect() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM products"))
        conn.commit()
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        
        with engine.connect() as conn:
            trans = conn.begin()
            
            for row in reader:
                asin = row.get("asin", "").strip()
                if not asin:
                    continue
                
                try:
                    conn.execute(
                        text("""
                            INSERT INTO products (
                                asin, product_title, product_price, product_original_price,
                                currency, product_star_rating, product_num_ratings,
                                product_url, product_photo, product_num_offers,
                                product_minimum_offer_price, is_best_seller, is_amazon_choice,
                                is_prime, climate_pledge_friendly, sales_volume,
                                delivery, has_variations, product_availability,
                                unit_price, unit_count
                            ) VALUES (
                                :asin, :title, :price, :orig_price,
                                :currency, :rating, :num_ratings,
                                :url, :photo, :num_offers,
                                :min_offer, :best_seller, :amazon_choice,
                                :prime, :climate, :sales_vol,
                                :delivery, :variations, :availability,
                                :unit_price, :unit_count
                            )
                        """),
                        {
                            "asin": asin,
                            "title": row.get("product_title", "").strip(),
                            "price": clean_price(row.get("product_price", "")),
                            "orig_price": clean_price(row.get("product_original_price", "")),
                            "currency": row.get("currency", "USD").strip(),
                            "rating": clean_float(row.get("product_star_rating", "")),
                            "num_ratings": clean_int(row.get("product_num_ratings", "")),
                            "url": row.get("product_url", "").strip(),
                            "photo": row.get("product_photo", "").strip(),
                            "num_offers": clean_int(row.get("product_num_offers", "")),
                            "min_offer": clean_price(row.get("product_minimum_offer_price", "")),
                            "best_seller": row.get("is_best_seller", "False").strip(),
                            "amazon_choice": row.get("is_amazon_choice", "False").strip(),
                            "prime": row.get("is_prime", "False").strip(),
                            "climate": row.get("climate_pledge_friendly", "False").strip(),
                            "sales_vol": row.get("sales_volume", "").strip(),
                            "delivery": row.get("delivery", "").strip(),
                            "variations": row.get("has_variations", "False").strip(),
                            "availability": row.get("product_availability", "").strip(),
                            "unit_price": row.get("unit_price", "").strip(),
                            "unit_count": row.get("unit_count", "").strip(),
                        }
                    )
                    count += 1
                except Exception as e:
                    print(f"Error inserting row {asin}: {e}")
            
            trans.commit()
    
    print(f"✅ Loaded {count} products into PostgreSQL")
    return True


def seed_orders():
    """Create sample orders in MySQL."""
    print("Seeding orders into MySQL...")
    
    engine = create_engine(MYSQL_URL)
    
    # Create orders table
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER AUTO_INCREMENT PRIMARY KEY,
                customer_name VARCHAR(100),
                customer_email VARCHAR(100),
                product_asin VARCHAR(20),
                product_title TEXT,
                quantity INTEGER DEFAULT 1,
                total_price FLOAT,
                currency VARCHAR(10) DEFAULT 'USD',
                status VARCHAR(50) DEFAULT 'Pending',
                shipping_address TEXT,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_date VARCHAR(100)
            )
        """))
        conn.commit()
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM orders"))
        conn.commit()
    
    sample_orders = [
        {
            "customer_name": "John Smith",
            "customer_email": "john.smith@email.com",
            "product_asin": "B0BQ118F2T",
            "product_title": "Moto G Play 2023 3-Day Battery Unlocked Made for US 3/32GB 16MP Camera Navy Blue",
            "quantity": 1,
            "total_price": 99.99,
            "status": "Delivered",
            "shipping_address": "123 Oak Street, Apt 4B, New York, NY 10001",
            "delivery_date": "Delivered on Aug 10, 2024"
        },
        {
            "customer_name": "Sarah Johnson",
            "customer_email": "sarah.j@email.com",
            "product_asin": "B0CN1QSH8Q",
            "product_title": "SAMSUNG Galaxy A15 5G A Series Cell Phone, 128GB Unlocked Android Smartphone",
            "quantity": 2,
            "total_price": 399.98,
            "status": "Shipped",
            "shipping_address": "456 Pine Road, Suite 200, Los Angeles, CA 90001",
            "delivery_date": "Expected delivery: Aug 15-18, 2024"
        },
        {
            "customer_name": "Mike Chen",
            "customer_email": "mike.chen@email.com",
            "product_asin": "B0CWXNS552",
            "product_title": "Apple AirTag",
            "quantity": 3,
            "total_price": 71.97,
            "status": "Confirmed",
            "shipping_address": "789 Maple Drive, Chicago, IL 60601",
            "delivery_date": "5-7 business days"
        },
        {
            "customer_name": "Emma Wilson",
            "customer_email": "emma.w@email.com",
            "product_asin": "B0D1XD1ZV3",
            "product_title": "Apple AirPods Pro (2nd Generation) Wireless Ear Buds with USB-C Charging",
            "quantity": 1,
            "total_price": 179.99,
            "status": "Pending",
            "shipping_address": "321 Elm Street, Austin, TX 73301",
            "delivery_date": "5-7 business days"
        },
        {
            "customer_name": "Alex Rivera",
            "customer_email": "alex.r@email.com",
            "product_asin": "B0BZ9XNBRB",
            "product_title": "Google Pixel 7a - Unlocked Android Cell Phone",
            "quantity": 1,
            "total_price": 335.00,
            "status": "Shipped",
            "shipping_address": "654 Birch Lane, Seattle, WA 98101",
            "delivery_date": "Expected delivery: Aug 13-16, 2024"
        },
        {
            "customer_name": "John Smith",
            "customer_email": "john.smith@email.com",
            "product_asin": "B0CRB1VZ46",
            "product_title": "Amazon Basics Multipurpose Scissors",
            "quantity": 2,
            "total_price": 4.78,
            "status": "Delivered",
            "shipping_address": "123 Oak Street, Apt 4B, New York, NY 10001",
            "delivery_date": "Delivered on Aug 5, 2024"
        }
    ]
    
    with engine.connect() as conn:
        trans = conn.begin()
        for order in sample_orders:
            conn.execute(
                text("""
                    INSERT INTO orders (customer_name, customer_email, product_asin,
                                       product_title, quantity, total_price, currency,
                                       status, shipping_address, delivery_date)
                    VALUES (:name, :email, :asin, :title, :qty, :price, 
                            'USD', :status, :address, :delivery)
                """),
                {
                    "name": order["customer_name"],
                    "email": order["customer_email"],
                    "asin": order["product_asin"],
                    "title": order["product_title"],
                    "qty": order["quantity"],
                    "price": order["total_price"],
                    "status": order["status"],
                    "address": order["shipping_address"],
                    "delivery": order["delivery_date"]
                }
            )
        trans.commit()
    
    print(f"✅ Created {len(sample_orders)} sample orders in MySQL")
    return True


def create_chat_history_table():
    """Create chat_history table in PostgreSQL."""
    print("Creating chat_history table in PostgreSQL...")
    
    engine = create_engine(POSTGRES_URL)
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100),
                role VARCHAR(20),
                message TEXT,
                inbound_guardrail_hit VARCHAR(200),
                outbound_guardrail_hit VARCHAR(200),
                guardrail_action VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
    
    print("✅ chat_history table created")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("AI Shopping Cart - Database Seed Script")
    print("=" * 60)
    
    create_chat_history_table()
    seed_products()
    seed_orders()
    
    print("\n" + "=" * 60)
    print("🎉 Seeding complete!")
    print("=" * 60)