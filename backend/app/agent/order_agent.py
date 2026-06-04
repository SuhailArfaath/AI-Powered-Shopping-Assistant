"""
Order Agent — A separate LangGraph agent dedicated to MySQL order queries.
Implements the Agent-to-Agent protocol: the main shopping agent delegates
order-related questions to this agent, which processes them independently
and returns structured results.

This agent has its own:
- State definition
- System prompt (specialized for orders)
- Tools (MySQL queries only)
- LangGraph graph
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy import create_engine, text
from ..config import settings
import re
import json


# ============================================================
# MySQL engine (Orders only)
# ============================================================
my_engine = create_engine(settings.mysql_url)


# ============================================================
# Order Agent State
# ============================================================

class OrderAgentState(TypedDict):
    """State for the order agent."""
    user_query: str
    extracted_order_id: Optional[int]
    extracted_email: Optional[str]
    raw_data: Optional[str]
    reply: str
    error: Optional[str]
    query_type: str


# ============================================================
# LLM Setup
# ============================================================

if settings.openrouter_api_key:
    order_llm = ChatOpenAI(
        model=settings.openrouter_model or "openai/gpt-4o-mini",
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        default_headers={
            "HTTP-Referer": "https://AI-shopping-cart.local",
            "X-Title": "AI Shopping Cart - Order Agent"
        }
    )
else:
    order_llm = None


# ============================================================
# Order Agent System Prompt
# ============================================================

ORDER_AGENT_SYSTEM_PROMPT = """You are an Order Status Specialist Agent for the AI Shopping Cart application.
Your sole responsibility is to query and explain order information from the orders database.

CRITICAL RULES:
- You ONLY have access to the ORDERS database (MySQL). You cannot search products.
- Never make up order information. Always use the data returned from the database.
- Answer in plain, friendly English. Be concise.
- If no orders are found, explain what you searched for and suggest alternatives.
- If there is an error querying the database, report it.
- Always respond in English ONLY.

The orders table has these columns:
- id (order number)
- customer_name
- customer_email
- product_title
- product_asin
- quantity
- total_price
- currency (default: USD)
- status (Pending, Confirmed, Shipped, Delivered, Cancelled)
- shipping_address
- order_date
- delivery_date

When explaining order status:
- Include the order ID, current status, product, expected delivery
- Use emojis to make it friendly
"""


# ============================================================
# Order Agent Tools (direct MySQL queries)
# ============================================================

def query_order_by_id(order_id: int) -> str:
    """Query MySQL orders table by order ID. Returns JSON string of order rows."""
    try:
        with my_engine.connect() as conn:
            sql = text("""
                SELECT id, customer_name, customer_email, product_asin,
                       product_title, quantity, total_price, currency,
                       status, shipping_address, order_date, delivery_date
                FROM orders
                WHERE id = :oid
            """)
            result = conn.execute(sql, {"oid": order_id})
            rows = result.fetchall()
            if not rows:
                return json.dumps({
                    "found": False,
                    "message": f"Order #{order_id} not found.",
                    "searched_by": "order_id",
                    "search_value": order_id
                })

            orders = []
            for row in rows:
                orders.append({
                    "id": row.id,
                    "customer_name": row.customer_name,
                    "customer_email": row.customer_email,
                    "product_asin": row.product_asin,
                    "product_title": row.product_title,
                    "quantity": row.quantity,
                    "total_price": float(row.total_price) if row.total_price else 0,
                    "currency": row.currency or "USD",
                    "status": row.status or "Pending",
                    "shipping_address": row.shipping_address,
                    "order_date": str(row.order_date) if row.order_date else "N/A",
                    "delivery_date": row.delivery_date or "Not yet available",
                })
            return json.dumps({"found": True, "count": len(orders), "orders": orders})
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})


def query_orders_by_email(email: str) -> str:
    """Query MySQL orders table by customer email. Returns JSON string of order rows."""
    try:
        with my_engine.connect() as conn:
            sql = text("""
                SELECT id, customer_name, customer_email, product_asin,
                       product_title, quantity, total_price, currency,
                       status, shipping_address, order_date, delivery_date
                FROM orders
                WHERE customer_email = :email
                ORDER BY order_date DESC
            """)
            result = conn.execute(sql, {"email": email})
            rows = result.fetchall()
            if not rows:
                return json.dumps({
                    "found": False,
                    "message": f"No orders found for email '{email}'.",
                    "searched_by": "email",
                    "search_value": email
                })

            orders = []
            for row in rows:
                orders.append({
                    "id": row.id,
                    "customer_name": row.customer_name,
                    "customer_email": row.customer_email,
                    "product_asin": row.product_asin,
                    "product_title": row.product_title,
                    "quantity": row.quantity,
                    "total_price": float(row.total_price) if row.total_price else 0,
                    "currency": row.currency or "USD",
                    "status": row.status or "Pending",
                    "shipping_address": row.shipping_address,
                    "order_date": str(row.order_date) if row.order_date else "N/A",
                    "delivery_date": row.delivery_date or "Not yet available",
                })
            return json.dumps({"found": True, "count": len(orders), "orders": orders})
    except Exception as e:
        return json.dumps({"found": False, "error": str(e)})


# ============================================================
# Node 1: Extract intent and parameters
# ============================================================

def extract_node(state: OrderAgentState) -> OrderAgentState:
    """First node: extract order ID, email, or determine query type from user input."""
    user_query = state["user_query"]
    input_lower = user_query.lower().strip()

    # Extract order ID (numbers 1-99999)
    order_id_match = re.search(r'(?:order|#|id|no|number)\s*[#:;\-]?\s*(\d{1,5})', user_query, re.IGNORECASE)
    if order_id_match:
        oid = int(order_id_match.group(1))
        if 1 <= oid <= 99999:
            state["extracted_order_id"] = oid

    # Extract email
    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', user_query)
    if email_match:
        state["extracted_email"] = email_match.group(0)

    # Determine query type
    delivery_keywords = ["delivery", "delivered", "shipped", "shipping", "arrive", "when", "date", "estimated", "eta", "reach"]
    status_keywords = ["status", "update", "progress", "track", "where", "current", "pending", "confirmed"]
    all_keywords = ["all", "every", "list", "show all", "all orders", "history", "previous", "past"]

    is_delivery = any(w in input_lower for w in delivery_keywords)
    is_status = any(w in input_lower for w in status_keywords)
    is_all = any(w in input_lower for w in all_keywords)

    if is_all:
        state["query_type"] = "all_orders"
    elif is_delivery or is_status or state["extracted_order_id"] or state["extracted_email"]:
        state["query_type"] = "order_status"
    else:
        state["query_type"] = "order_status"

    return state


# ============================================================
# Node 2: Query MySQL database
# ============================================================

def query_node(state: OrderAgentState) -> OrderAgentState:
    """Second node: execute the actual MySQL query and get raw data."""
    try:
        if state["extracted_order_id"]:
            state["raw_data"] = query_order_by_id(state["extracted_order_id"])
        elif state["extracted_email"]:
            state["raw_data"] = query_orders_by_email(state["extracted_email"])
        elif state["query_type"] == "all_orders":
            try:
                with my_engine.connect() as conn:
                    sql = text("""
                        SELECT id, customer_name, customer_email, product_asin,
                               product_title, quantity, total_price, currency,
                               status, shipping_address, order_date, delivery_date
                        FROM orders
                        ORDER BY order_date DESC
                        LIMIT 20
                    """)
                    result = conn.execute(sql)
                    rows = result.fetchall()
                    if not rows:
                        state["raw_data"] = json.dumps({"found": False, "message": "No orders found in the database."})
                    else:
                        orders = []
                        for row in rows:
                            orders.append({
                                "id": row.id,
                                "customer_name": row.customer_name,
                                "customer_email": row.customer_email,
                                "product_title": row.product_title,
                                "quantity": row.quantity,
                                "total_price": float(row.total_price) if row.total_price else 0,
                                "currency": row.currency or "USD",
                                "status": row.status or "Pending",
                                "order_date": str(row.order_date) if row.order_date else "N/A",
                                "delivery_date": row.delivery_date or "Not yet available",
                            })
                        state["raw_data"] = json.dumps({"found": True, "count": len(orders), "orders": orders})
            except Exception as e:
                state["raw_data"] = json.dumps({"found": False, "error": str(e)})
        else:
            state["raw_data"] = json.dumps({
                "found": False,
                "message": "I couldn't find an order ID or email in your question."
            })
    except Exception as e:
        state["raw_data"] = json.dumps({"found": False, "error": str(e)})

    return state


# ============================================================
# Node 3: Format response via LLM
# ============================================================

def format_node(state: OrderAgentState) -> OrderAgentState:
    """Third node: use LLM to format the raw DB data into a friendly response."""
    raw_data = state["raw_data"]
    user_query = state["user_query"]

    if not raw_data:
        state["reply"] = "I'm sorry, I couldn't retrieve order information at this time. Please try again later or contact customer support for assistance."
        return state

    try:
        data = json.loads(raw_data)
    except:
        state["reply"] = "I encountered an error processing the order data. Please try again or contact customer support for help."
        return state

    if data.get("error"):
        state["reply"] = "I'm having trouble connecting to the orders database right now. Error: {}. Please try again in a few moments.".format(data['error'])
        return state

    if not data.get("found"):
        searched_by = data.get("searched_by", "")
        search_value = data.get("search_value", "")

        if searched_by == "order_id":
            state["reply"] = (
                "I searched for **Order #{}** in our database, but unfortunately I couldn't find any matching order.\n\n"
                "Here are a few things to check:\n"
                "- Double-check the order number - it might have a different format\n"
                "- If you just placed the order, it may take a moment to appear\n"
                "- Try searching by the email address you used instead\n\n"
                "If you need further help, feel free to ask!"
            ).format(search_value)
        elif searched_by == "email":
            state["reply"] = (
                "I searched for orders associated with **{}** but didn't find any records.\n\n"
                "A few possibilities:\n"
                "- You may have used a different email address to place the order\n"
                "- If you haven't placed an order yet, I can help you with that!\n"
                "- Try searching by your order ID instead\n\n"
                "Let me know how else I can assist!"
            ).format(search_value)
        else:
            state["reply"] = (
                "I looked into the database but couldn't find the order information you're looking for.\n\n"
                "Could you please provide more details? I can search by:\n"
                "- **Order ID** - e.g., 'Check order 1234'\n"
                "- **Email address** - e.g., 'Show orders for john@email.com'\n\n"
                "I'm here to help!"
            )
        return state

    # Use LLM to generate a friendly response from the raw data
    if order_llm:
        try:
            response = order_llm.invoke([
                SystemMessage(content=ORDER_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=(
                    "The user asked: '{}'\n\n"
                    "Here is the raw order data from the database:\n{}\n\n"
                    "Please provide a friendly, concise response to the user explaining their order status. "
                    "Include the order ID, status, product details, and delivery date if available. "
                    "Use emojis to make it friendly. If they asked about delivery, focus on delivery details."
                ).format(user_query, json.dumps(data, indent=2)))
            ])
            state["reply"] = response.content
        except Exception:
            state["reply"] = _format_orders_fallback(data, user_query)
    else:
        state["reply"] = _format_orders_fallback(data, user_query)

    return state


def _format_orders_fallback(data: dict, user_query: str) -> str:
    """Fallback formatter when LLM is unavailable."""
    orders = data.get("orders", [])
    output_parts = []

    for order in orders:
        status_emoji = {
            "Confirmed": "OK",
            "Shipped": "BOX",
            "Delivered": "PARTY",
            "Cancelled": "NO",
            "Pending": "CLOCK",
        }.get(order.get("status", ""), "CLIPBOARD")

        delivery = order.get("delivery_date", "Not yet available")

        output_parts.append(
            "* Order #{} - {}\n"
            "  Product: {} x {}\n"
            "  Total: {} ${:.2f}\n"
            "  Order Date: {}\n"
            "  Delivery: {}\n"
            "  Shipping: {}\n"
        ).format(
            order['id'], order['status'],
            order['product_title'], order['quantity'],
            order['currency'], order['total_price'],
            order.get('order_date', 'N/A'),
            delivery,
            order.get('shipping_address', 'N/A'),
        )

    output = "Order Information\n\n" + "\n".join(output_parts)

    if any(w in user_query.lower() for w in ["delivery", "delivered", "arrive", "when", "eta"]):
        main_order = orders[0]
        output += "\nDelivery Status: {}".format(main_order.get('delivery_date', 'Not yet available'))

    return output


# ============================================================
# Build the Order Agent graph
# ============================================================

def build_order_graph():
    """Build the Order Agent's LangGraph state graph."""
    workflow = StateGraph(OrderAgentState)

    workflow.add_node("extract", extract_node)
    workflow.add_node("query", query_node)
    workflow.add_node("format", format_node)

    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "query")
    workflow.add_edge("query", "format")
    workflow.add_edge("format", END)

    return workflow.compile()


# ============================================================
# Order Agent Runner (the main entry point)
# ============================================================

_compiled_order_graph = None


def get_order_graph():
    """Get or build the compiled order agent graph."""
    global _compiled_order_graph
    if _compiled_order_graph is None:
        _compiled_order_graph = build_order_graph()
    return _compiled_order_graph


def run_order_agent(user_query: str) -> dict:
    """
    Main entry point for the Order Agent.
    Called by the main shopping agent's tool layer (Agent-to-Agent protocol).

    Args:
        user_query: The user's question about orders

    Returns:
        dict with 'reply' (friendly response), 'raw_data' (JSON), 'has_data' (bool)
    """
    try:
        graph = get_order_graph()
        initial_state: OrderAgentState = {
            "user_query": user_query,
            "extracted_order_id": None,
            "extracted_email": None,
            "raw_data": None,
            "reply": "",
            "error": None,
            "query_type": "order_status",
        }

        result = graph.invoke(initial_state)
        reply = result.get("reply", "I'm sorry, I couldn't find order information for you. Please try searching with your order ID or email address.")
        raw_data = result.get("raw_data", "{}")

        has_data = False
        try:
            data = json.loads(raw_data) if raw_data else {}
            has_data = data.get("found", False)
        except:
            pass

        return {
            "reply": reply,
            "raw_data": raw_data,
            "has_data": has_data,
            "order_agent_used": True,
        }
    except Exception as e:
        return {
            "reply": "The order agent encountered an error: {}. Please try again or contact customer support for assistance.".format(str(e)),
            "raw_data": "{}",
            "has_data": False,
            "order_agent_used": True,
        }
