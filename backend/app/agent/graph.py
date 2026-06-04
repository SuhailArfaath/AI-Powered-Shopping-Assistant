"""
LangGraph agent for the AI Shopping Cart chatbot.
Implements a state graph with greeting, search, multi-step order collection, and order status nodes.
"""
import json
from typing import TypedDict, Annotated, Optional, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..config import settings
from .guardrails import check_inbound_guardrails, check_outbound_guardrails, GUARDRAIL_CATEGORIES_INBOUND, GUARDRAIL_CATEGORIES_OUTBOUND
import re

# Import tool functions directly
from .tools import search_products, get_order_status, place_order


# ============================================================
# In-memory order session tracker (keyed by session_id)
# ============================================================
order_sessions: dict = {}


def get_order_session(session_id: str) -> dict:
    """Get or create an order session."""
    if session_id not in order_sessions:
        order_sessions[session_id] = {
            "asin": None,
            "product_title": None,
            "product_price": None,
            "name": None,
            "email": None,
            "quantity": None,
            "shipping_address": None,
            "step": "start",  # start, collecting, confirm, done
        }
    return order_sessions[session_id]


def clear_order_session(session_id: str):
    """Clear an order session after completion or cancellation."""
    if session_id in order_sessions:
        del order_sessions[session_id]


# ============================================================
# State definition
# ============================================================

class AgentState(TypedDict):
    messages: list
    user_input: str
    reply: str
    session_id: str
    inbound_guardrail_hit: Optional[str]
    outbound_guardrail_hit: Optional[str]
    inbound_guardrails: list
    outbound_guardrails: list
    context_used: bool
    next_node: str
    show_order_button: bool  # If True, frontend renders a Place Order button


# ============================================================
# LLM Setup
# ============================================================

if settings.openrouter_api_key:
    llm = ChatOpenAI(
        model=settings.openrouter_model or "openai/gpt-4o-mini",
        openai_api_key=settings.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        default_headers={
            "HTTP-Referer": "https://AI-shopping-cart.local",
            "X-Title": "AI Shopping Cart"
        }
    )
else:
    llm = None


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are AI Shopping Assistant for an AI-powered shopping cart application.
Your role is to help customers with:
1. Searching and learning about available products
2. Placing orders  
3. Checking order status

CRITICAL: You MUST ALWAYS respond in English ONLY. Never respond in any other language.

IMPORTANT:
- Keep responses concise and friendly
- If the user asks about products, search using relevant keywords
- Never make up product information - always use the search tool
- Never make up order information - always use the order status tool

Greeting format: "Hello! Welcome to AI Shopping Cart! 😊 I can help you:
• 🔍 Search for products and learn about them
• 🛒 Place orders
• 📦 Check your order status

How can I assist you today?"""


# ============================================================
# Intent Classification
# ============================================================

def classify_intent(user_input: str) -> str:
    """Classify the user's intent based on their input."""
    input_lower = user_input.lower().strip()

    # Check for cancel
    if input_lower in ["cancel", "cancel order", "cancel transaction", "no cancel"]:
        return "cancel_order"

    # Check for CONFIRM_ORDER signal
    if input_lower in ["confirm order", "place order", "confirm", "yes place it", "place it"]:
        return "confirm_order"

    # Check for ASIN (Amazon Standard Identification Number)
    asin_match = re.search(r'\bB[A-Z0-9]{9}\b', user_input)
    if asin_match:
        if any(w in input_lower for w in ["order", "buy", "purchase", "want", "quantity", "qty"]):
            return "place_order"
        return "search_products"

    # Order placement related
    if any(word in input_lower for word in ["buy", "purchase", "order now", "checkout", "cart", "add to"]):
        return "place_order"
    if re.search(r'\b(order)\s+(a|an|the|this|that)\b', input_lower):
        return "place_order"
    if re.search(r'\b(order|place)\s+(my\s+)?(order|product|item)\b', input_lower):
        return "place_order"
    if re.search(r'\b(want|like|wish|would)\s+.*\b(to\s+)?order\b', input_lower):
        return "place_order"

    # Order status related
    if any(word in input_lower for word in ["status", "delivery", "delivered", "shipped", "track"]):
        return "order_status"
    if re.search(r'\b(order)\s*(#|number|id|no)?\s*(\d{1,5})\b', input_lower):
        return "order_status"
    # Check for email-based order lookup
    if re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', user_input) and any(w in input_lower for w in ["order", "orders", "status", "delivery", "purchase"]):
        return "order_status"
    # Check for order-related queries without specific number
    if re.search(r'\b(orders?|purchase)\b', input_lower) and not re.search(r'\b(product|search|find|show|list|have|tell|about|brand)\b', input_lower):
        return "order_status"

    # Product search related
    if any(word in input_lower for word in [
        "product", "search", "find", "show", "list", "available", "what", "price",
        "cheap", "expensive", "brand", "tell", "about", "have", "describe",
        "phone", "laptop", "tv", "book", "shirt", "shoe",
        "moto", "galaxy", "pixel", "airtag", "airpods", "kindle", "echo",
    ]):
        return "search_products"

    brand_pattern = r'\b(motorola|samsung|apple|google|nike|amazon|bounty|hanes|vtech|bold|total by verizon|tracfone|peacock|netflix|disney)\b'
    if re.search(brand_pattern, input_lower):
        return "search_products"

    # If there's a name/email/address pattern, it might be providing order details
    if re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', user_input):
        return "place_order"
    if re.search(r'\b(name|address|ship)\s*(is|:)\s*', input_lower):
        return "place_order"

    # Greeting
    if any(word in input_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
        return "greeting"

    return "greeting"


# ============================================================
# Node 1: Greeting & Intent Classification
# ============================================================

def greeting_node(state: AgentState) -> AgentState:
    """First node: greet user and understand their request."""
    user_input = state["user_input"]
    session_id = state["session_id"]
    intent = classify_intent(user_input)

    # Check if there's an active order session (user providing more details)
    order_session = get_order_session(session_id)
    if order_session["step"] == "collecting":
        # User is in the middle of providing order details
        state["next_node"] = "collect_details"
        state["reply"] = ""
        return state

    if llm:
        try:
            response = llm.invoke([
                SystemMessage(content=f"{SYSTEM_PROMPT}\n\nUser asked: {user_input}\nDetected intent: {intent}\nProvide a warm greeting and helpful response."),
                HumanMessage(content=user_input)
            ])
            state["reply"] = response.content
        except:
            state["reply"] = _get_fallback_response(intent, user_input)
    else:
        state["reply"] = _get_fallback_response(intent, user_input)

    if intent == "search_products":
        state["next_node"] = "search"
    elif intent == "order_status":
        state["next_node"] = "order_status"
    elif intent in ("place_order", "confirm_order"):
        state["next_node"] = intent
    elif intent == "cancel_order":
        # Clear any pending order and respond
        clear_order_session(session_id)
        state["reply"] = "✅ Order transaction has been cancelled. No worries! Let me know if you need anything else. 😊"
        state["context_used"] = True
        state["next_node"] = "end"
    else:
        state["next_node"] = "end"

    return state


def _get_fallback_response(intent: str, user_input: str) -> str:
    """Fallback responses when LLM is not available."""
    if intent == "search_products":
        keywords = []
        for word in ["nike", "adidas", "samsung", "apple", "google", "motorola", "bounty", "hanes", "amazon basics"]:
            if word in user_input.lower():
                keywords.append(word)
        search_query = " ".join(keywords) if keywords else re.sub(r'[?|!|.]', '', user_input).strip()
        result = search_products(search_query)
        return f"Let me search for that! {result}"
    elif intent == "order_status":
        order_match = re.search(r'(\d+)', user_input)
        oid = order_match.group(1) if order_match else None
        if oid:
            result = get_order_status(order_id=int(oid), user_query=user_input)
            return result
        return "I'd be happy to check your order status! Could you please provide your **order ID** or the **email address** you used?"
    elif intent in ("place_order", "confirm_order"):
        return (
            "I'd be happy to help you place an order! 🛒\n\n"
            "To get started, I need a few details:\n"
            "1. **Which product** would you like to order? (Tell me the name or ASIN)\n"
            "2. **Quantity** - how many do you need?\n"
            "3. **Your name** and **email address**\n"
            "4. **Shipping address**\n\n"
            "Feel free to provide any of these details and I'll guide you through the rest!"
        )
    else:
        return (
            "Hello! Welcome to **AI Shopping Cart**! 😊\n\n"
            "I can help you:\n"
            "• 🔍 **Search for products** - Just tell me what you're looking for!\n"
            "• 🛒 **Place orders** - Choose a product and I'll guide you\n"
            "• 📦 **Check order status** - Provide your order ID or email\n\n"
            "What would you like to do today?"
        )


# ============================================================
# Node 2: Search Products
# ============================================================

def search_node(state: AgentState) -> AgentState:
    """Node: Search products based on user query."""
    user_input = state["user_input"]

    common_words = ["about", "what", "tell", "me", "show", "find", "search", "looking", "for", "the", "is", "are",
                    "any", "some", "available", "can", "you", "do", "have", "does", "please", "i", "a", "an", "want", "need"]
    words = user_input.lower().split()
    keywords = [w for w in words if w not in common_words]
    search_query = " ".join(keywords[:8])

    result = search_products(search_query)
    state["context_used"] = True

    if llm:
        try:
            response = llm.invoke([
                SystemMessage(content=f"You are a helpful shopping assistant. Based on these product search results, give the user a friendly summary.\n\nSearch results for '{search_query}':\n{result}\n\nBe concise and highlight the best options. Include prices and ratings.\n\nIf they want to order, tell them they can say 'I want to order [product name or ASIN]'."),
                HumanMessage(content=user_input)
            ])
            state["reply"] = response.content
        except:
            state["reply"] = f"Here are the products I found matching your search:\n\n{result}\n\nWould you like more details on any of these, or would you like to place an order?"
    else:
        state["reply"] = f"Here are the products I found matching your search:\n\n{result}\n\nWould you like more details on any of these, or would you like to place an order?"

    state["next_node"] = "end"
    return state


# ============================================================
# Node 3: Multi-step Order Details Collection
# ============================================================

def collect_details_node(state: AgentState) -> AgentState:
    """
    Node: Collect order details step by step across multiple messages.
    Tracks state in order_sessions dict keyed by session_id.
    When all details are collected, shows order summary with button.
    """
    user_input = state["user_input"]
    session_id = state["session_id"]
    order = get_order_session(session_id)

    # Set step to collecting
    order["step"] = "collecting"

    # --- Extract details from current message ---

    # ASIN
    asin_match = re.search(r'\b(B[A-Z0-9]{9})\b', user_input)
    if asin_match and not order["asin"]:
        asin = asin_match.group(1)
        order["asin"] = asin
        # Look up product details
        product_info = search_products(asin)
        price_match = re.search(r'Price:\s*\$?([\d.]+)', product_info)
        title_match = re.search(r'•\s*(.+?)\n', product_info)
        if title_match:
            order["product_title"] = title_match.group(1).strip()
        if price_match:
            order["product_price"] = float(price_match.group(1))

    # Name
    name_match = re.search(r'(?:name is|my name is|called|I am|I\'m|name:)\s+([A-Za-z\s]{2,40})', user_input, re.IGNORECASE)
    if name_match and not order["name"]:
        order["name"] = name_match.group(1).strip()
    # Also catch "Name: XYZ" or "name is XYZ" patterns
    if not order["name"]:
        name_match2 = re.search(r'\bname\s*(?::|=|is)\s*([A-Za-z\s]{2,40})', user_input, re.IGNORECASE)
        if name_match2:
            order["name"] = name_match2.group(1).strip()

    # Email
    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', user_input)
    if email_match and not order["email"]:
        order["email"] = email_match.group(0)

    # Quantity
    qty_match = re.search(r'(\d+)\s*(?:quantity|qty|of|items?|units?|pieces?|quantities)', user_input, re.IGNORECASE)
    if qty_match and not order["quantity"]:
        order["quantity"] = int(qty_match.group(1))
    # Also match "qty: X" or "quantity X" patterns
    if not order["quantity"]:
        qty_match2 = re.search(r'\b(qty|quantity)\s*(?::|=|is|#)?\s*(\d+)', user_input, re.IGNORECASE)
        if qty_match2:
            order["quantity"] = int(qty_match2.group(2))
    # Default quantity
    if not order["quantity"]:
        order["quantity"] = 1

    # Shipping address
    addr_match = re.search(r'(?:address|ship to|deliver to|shipping)\s*(?::|is|=)?\s*(.{10,120})', user_input, re.IGNORECASE)
    if addr_match and not order["shipping_address"]:
        order["shipping_address"] = addr_match.group(1).strip()
    # Also catch plain address-like patterns (number + street)
    if not order["shipping_address"]:
        addr_match2 = re.search(r'\b\d{1,5}\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way|Circle|Cir| colony | nagar | layout)\b', user_input, re.IGNORECASE)
        if addr_match2:
            # Get more context - up to 3 words after the street name
            full_match = re.search(r'(\d{1,5}\s+[A-Za-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Way).{0,60})', user_input, re.IGNORECASE)
            if full_match:
                order["shipping_address"] = full_match.group(1).strip()

    # --- Determine what's missing ---
    missing = []
    if not order["name"]:
        missing.append("your full name")
    if not order["email"]:
        missing.append("your email address")
    if not order["asin"]:
        missing.append("the product ASIN or name")
    if not order["shipping_address"]:
        missing.append("your shipping address")

    # --- If ASIN is set but product title/price are not, look them up ---
    if order["asin"] and (not order["product_title"] or not order["product_price"]):
        product_info = search_products(order["asin"])
        price_match2 = re.search(r'Price:\s*\$?([\d.]+)', product_info)
        if price_match2 and not order["product_price"]:
            order["product_price"] = float(price_match2.group(1))

    # --- Build response ---
    if not missing:
        # All details collected! Show summary with total
        unit_price = order["product_price"] or 29.99
        qty = order["quantity"] or 1
        total = unit_price * qty

        summary = (
            f"📋 **Order Summary**\n\n"
            f"| Detail | Value |\n"
            f"|---|---|\n"
            f"| **Product** | {order['product_title'] or 'ASIN: ' + order['asin']} |\n"
            f"| **ASIN** | {order['asin']} |\n"
            f"| **Unit Price** | ${unit_price:.2f} |\n"
            f"| **Quantity** | {qty} |\n"
            f"| **Total** | **${total:.2f}** |\n"
            f"| **Customer** | {order['name']} ({order['email']}) |\n"
            f"| **Shipping** | {order['shipping_address']} |\n\n"
            f"Click **Place Order** to confirm or **Cancel** to cancel this transaction."
        )

        order["step"] = "confirm"
        state["reply"] = summary
        state["context_used"] = True
        state["show_order_button"] = True
    else:
        # Show what we have and ask for ALL missing details at once
        collected = []
        if order["name"]:
            collected.append(f"✅ Name: {order['name']}")
        if order["email"]:
            collected.append(f"✅ Email: {order['email']}")
        if order["asin"]:
            product_name = order['product_title'] or order['asin']
            qty_text = f" x{order['quantity']}" if order.get('quantity') else ""
            collected.append(f"✅ Product: {product_name}{qty_text}")
        if order.get("quantity"):
            collected.append(f"✅ Quantity: {order['quantity']}")
        if order["shipping_address"]:
            collected.append(f"✅ Shipping: {order['shipping_address']}")

        collected_text = "\n".join(collected) if collected else "No details yet."
        state["reply"] = (
            f"Great! Let me help you place this order. 🛒\n\n"
            f"**Collected so far:**\n{collected_text}\n\n"
            f"**I still need these details:**\n"
            + "\n".join(f"• ❌ {m}" for m in missing) +
            f"\n\nPlease provide all the missing details together in your next message.\n"
            f"For example: 'My name is John, john@email.com, 123 Main Street, New York'"
        )
        state["context_used"] = True
        state["show_order_button"] = False

    state["next_node"] = "end"
    return state


# ============================================================
# Node 3b: Confirm & Place Order
# ============================================================

def confirm_order_node(state: AgentState) -> AgentState:
    """Node: Confirm and place the order into the database."""
    session_id = state["session_id"]
    order = get_order_session(session_id)

    if order["step"] != "confirm" or not all([order.get("asin"), order.get("name"), order.get("email")]):
        state["reply"] = (
            "I don't have a complete order to confirm. Let's start over!\n\n"
            "Tell me which product you'd like to order (name or ASIN), and I'll guide you through the details."
        )
        state["context_used"] = False
        state["next_node"] = "end"
        return state

    unit_price = order["product_price"] or 29.99
    qty = order["quantity"] or 1
    total = unit_price * qty
    shipping = order["shipping_address"] or "123 Main Street, New York, NY 10001"
    product_title = order["product_title"] or f"Product ASIN: {order['asin']}"

    try:
        result = place_order(
            order["name"],
            order["email"],
            order["asin"],
            product_title,
            qty,
            total,
            shipping
        )
        state["reply"] = (
            f"✅ **Order Placed Successfully!**\n\n"
            f"{result}\n\n"
            f"Is there anything else I can help you with? 😊"
        )
        state["context_used"] = True
        # Clear the session
        clear_order_session(session_id)
    except Exception as e:
        state["reply"] = f"⚠️ Sorry, there was an error placing your order: {str(e)}. Please try again."
        state["context_used"] = False

    state["next_node"] = "end"
    return state


# ============================================================
# Node 4: Order Status
# ============================================================

def order_status_node(state: AgentState) -> AgentState:
    """Node: Check order status."""
    user_input = state["user_input"]

    order_id_match = re.search(r'(?:order|#|id)?\s*(\d{1,5})', user_input)
    email_match = re.search(r'[\w.-]+@[\w.-]+\.\w{2,}', user_input)

    if order_id_match:
        oid = int(order_id_match.group(1))
        if 1 <= oid <= 99999:
            result = get_order_status(order_id=oid, user_query=user_input)
            state["reply"] = result
            state["context_used"] = True
        else:
            state["reply"] = "I couldn't find that order ID. Could you please double-check the order number?"
            state["context_used"] = False
    elif email_match:
        email = email_match.group(0)
        result = get_order_status(email=email, user_query=user_input)
        state["reply"] = result
        state["context_used"] = True
    else:
        state["reply"] = (
            "To check your order status, I need either:\n\n"
            "• **Order ID** - e.g., 'order 1234'\n"
            "• **Email address** - the one you used to place the order\n\n"
            "Could you please provide one of these? 😊"
        )
        state["context_used"] = False

    state["next_node"] = "end"
    return state


# ============================================================
# Router logic
# ============================================================

def router(state: AgentState) -> str:
    """Route to the next node."""
    return state.get("next_node", "end")


# ============================================================
# Build the graph
# ============================================================

def build_graph():
    """Build and compile the LangGraph state graph."""
    workflow = StateGraph(AgentState)

    workflow.add_node("greeting", greeting_node)
    workflow.add_node("search", search_node)
    workflow.add_node("collect_details", collect_details_node)
    workflow.add_node("confirm_order", confirm_order_node)
    workflow.add_node("order_status", order_status_node)

    workflow.set_entry_point("greeting")

    workflow.add_conditional_edges(
        "greeting",
        router,
        {
            "search": "search",
            "place_order": "collect_details",
            "confirm_order": "confirm_order",
            "collect_details": "collect_details",
            "order_status": "order_status",
            "end": END
        }
    )

    workflow.add_edge("search", END)
    workflow.add_edge("collect_details", END)
    workflow.add_edge("confirm_order", END)
    workflow.add_edge("order_status", END)

    return workflow.compile()


# ============================================================
# Agent runner
# ============================================================

_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_agent(user_input: str, session_id: str = "default") -> dict:
    """
    Main entry point for the agent.
    Runs inbound guardrails, the agent graph, then outbound guardrails.
    """
    # Step 1: Inbound guardrails
    inbound_results, inbound_hit = check_inbound_guardrails(user_input)

    if inbound_hit:
        return {
            "reply": f"⚠️ I couldn't process this request because the **{inbound_hit}** guardrail was triggered. Please rephrase your message in a respectful and appropriate manner.",
            "session_id": session_id,
            "inbound_guardrail_hit": inbound_hit,
            "outbound_guardrail_hit": None,
            "inbound_guardrails": inbound_results,
            "outbound_guardrails": [{"name": c, "passed": True} for c in ["fluency", "legal", "groundedness", "relevance", "personally_identifiable_information"]]
        }

    # Step 2: Run agent
    try:
        graph = get_graph()
        initial_state = AgentState(
            messages=[],
            user_input=user_input,
            reply="",
            session_id=session_id,
            inbound_guardrail_hit=None,
            outbound_guardrail_hit=None,
            inbound_guardrails=[],
            outbound_guardrails=[],
            context_used=False,
            next_node="greeting",
            show_order_button=False
        )

        result = graph.invoke(initial_state)
        reply = result.get("reply", "I'm not sure how to help with that. Could you try asking differently?")
        context_used = result.get("context_used", False)
        show_button = result.get("show_order_button", False)
    except Exception as e:
        reply = f"I encountered an error processing your request. Please try again."
        context_used = False
        show_button = False

    # Step 3: Outbound guardrails
    outbound_results, outbound_hit = check_outbound_guardrails(reply, context_used)

    if outbound_hit:
        reply = f"⚠️ I could not provide a complete response because the **{outbound_hit}** guardrail was triggered. Please try asking your question in a different way."

    return {
        "reply": reply,
        "session_id": session_id,
        "inbound_guardrail_hit": inbound_hit,
        "outbound_guardrail_hit": outbound_hit,
        "inbound_guardrails": inbound_results,
        "outbound_guardrails": outbound_results,
        "show_order_button": show_button,
    }