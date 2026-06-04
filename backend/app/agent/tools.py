"""
Tool functions for LangGraph agent - search products and get order status.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from ..config import settings

# PostgreSQL engine (Products)
pg_engine = create_engine(settings.postgres_url)

# MySQL engine (Orders)
my_engine = create_engine(settings.mysql_url)


def search_products(query: str = "") -> str:
    """
    Search for products in the database by name/description.
    Returns formatted string with all matching products.
    """
    try:
        with pg_engine.connect() as conn:
            if query.strip():
                sql = text("""
                    SELECT id, asin, product_title, product_price, 
                           product_star_rating, product_num_ratings,
                           currency, is_best_seller, is_prime,
                           sales_volume, product_availability
                    FROM products 
                    WHERE product_title ILIKE :search OR asin ILIKE :search
                    ORDER BY product_star_rating DESC NULLS LAST
                    LIMIT 20
                """)
                result = conn.execute(sql, {"search": f"%{query}%"})
            else:
                sql = text(""")
                    SELECT id, asin, product_title, product_price, 
                           product_star_rating, product_num_ratings,
                           currency, is_best_seller, is_prime,
                           sales_volume, product_availability
                    FROM products 
                    ORDER BY product_star_rating DESC NULLS LAST
                    LIMIT 20
                """)
                result = conn.execute(sql)
            
            rows = result.fetchall()
            if not rows:
                return f"No products found matching '{query}'."
            
            output = f"Found {len(rows)} products matching '{query}':\n\n"
            for row in rows:
                rating = f"{row.product_star_rating}★" if row.product_star_rating else "N/A"
                reviews = f"({row.product_num_ratings} ratings)" if row.product_num_ratings else ""
                bestseller = "🏆 Best Seller! " if row.is_best_seller and row.is_best_seller.lower() == "true" else ""
                prime = "📦 Prime " if row.is_prime and row.is_prime.lower() == "true" else ""
                badge = f"{bestseller}{prime}".strip()
                badge_str = f" [{badge}]" if badge else ""
                
                output += f"• {row.product_title}{badge_str}\n"
                output += f"  Price: {row.product_price or 'N/A'} {row.currency or 'USD'}"
                output += f" | Rating: {rating} {reviews}\n"
                output += f"  ASIN: {row.asin} | ID: {row.id}\n\n"
            
            return output
    except Exception as e:
        return f"Error searching products: {str(e)}"


def get_order_status(order_id: int = None, email: str = None, user_query: str = None) -> str:
    """
    Get the status of an order by order ID or customer email.
    
    IMPLEMENTS AGENT-TO-AGENT PROTOCOL:
    Delegates to the dedicated Order Agent (order_agent.py) which has its own
    LangGraph graph with specialized system prompt, MySQL tools, and LLM formatting.
    The Order Agent independently processes the query and returns a friendly response.
    
    Args:
        order_id: Optional order ID number
        email: Optional customer email
        user_query: Original user question (passed to order agent for context)
    """
    # Build the query to pass to the order agent
    if user_query:
        agent_query = user_query
    elif order_id:
        agent_query = f"What is the status of order {order_id}?"
    elif email:
        agent_query = f"Show me all orders for {email}"
    else:
        return "Please provide an order ID or customer email."
    
    # Agent-to-Agent protocol: delegate to the Order Agent
    from .order_agent import run_order_agent
    result = run_order_agent(agent_query)
    
    return result["reply"]


def place_order(customer_name: str, customer_email: str, product_asin: str, 
                product_title: str, quantity: int, total_price: float,
                shipping_address: str) -> str:
    """
    Place a new order. Saves to the orders database.
    """
    try:
        with my_engine.connect() as conn:
            sql = text("""
                INSERT INTO orders (customer_name, customer_email, product_asin,
                                   product_title, quantity, total_price, 
                                   currency, status, shipping_address, delivery_date)
                VALUES (:name, :email, :asin, :title, :qty, :price,
                        :currency, :status, :address, :delivery)
            """)
            result = conn.execute(sql, {
                "name": customer_name,
                "email": customer_email,
                "asin": product_asin,
                "title": product_title,
                "qty": quantity,
                "price": total_price,
                "currency": "USD",
                "status": "Confirmed",
                "address": shipping_address,
                "delivery": "5-7 business days"
            })
            conn.commit()
            order_id = result.lastrowid
            
            return (
                f"Order #{order_id} placed successfully!\n\n"
                f"Customer: {customer_name}\n"
                f"Product: {product_title} (ASIN: {product_asin})\n"
                f"Quantity: {quantity}\n"
                f"Total: ${total_price:.2f}\n"
                f"Shipping: {shipping_address}\n"
                f"Delivery: 5-7 business days\n\n"
                f"Thank you for your order! You can check the status using your order ID."
            )
    except Exception as e:
        return f"Error placing order: {str(e)}"
