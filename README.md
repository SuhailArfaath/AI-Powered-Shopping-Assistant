<div align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React"/>
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/LangGraph-1E3A5F?style=for-the-badge&logo=langchain&logoColor=white" alt="LangGraph"/>
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
</div>

<br/>

<h1 align="center">
  🛒 AI-Assisted Shopping Cart
</h1>

<p align="center">
  <em>An intelligent, full-stack e-commerce platform powered by a multi-agent AI chatbot with dual-database architecture and real-time guardrails.</em>
</p>

<p align="center">
  <strong>React + TypeScript</strong> •
  <strong>FastAPI</strong> •
  <strong>LangGraph</strong> •
  <strong>PostgreSQL + MySQL</strong> •
  <strong>Docker Compose</strong>
</p>

<br/>

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Database Design](#-database-design)
- [Agent-to-Agent Protocol](#-agent-to-agent-protocol)
- [AI Guardrails](#-ai-guardrails)
- [API Reference](#-api-reference)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)

---

## 🎯 Project Overview

**AI-Assisted Shopping Cart** is a full-stack e-commerce application that seamlessly integrates:

- A **beautiful React frontend** with product browsing, order management, and a fixed AI chatbot panel
- A **multi-agent AI chatbot** (LangGraph) that answers product questions, manages orders, and checks status — all connected to live databases
- **Two database engines** — PostgreSQL for products and chat history, MySQL for orders — demonstrating polyglot persistence
- **Agent-to-Agent orchestration** where the main shopping agent delegates order queries to a dedicated Order Agent
- **Inbound & outbound content guardrails** that protect both users and internal data

The result is a smooth, conversational shopping experience where customers can search products, place orders, and track deliveries — all through natural language.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                     │
│  ┌─────────────────────────────────────┬────────────────────────┐ │
│  │        Main Content Panel           │   Chatbot Panel        │ │
│  │                                     │   (Fixed Right Side)   │ │
│  │  ┌──────────────────────────────┐   │   ┌────────────────┐  │ │
│  │  │   Products Page              │   │   │  💬 Messages   │  │ │
│  │  │   • Search / Filter          │   │   │  🛡️ Guardrails │  │ │
│  │  │   • Product Cards            │   │   │  🔘 Order Btn  │  │ │
│  │  └──────────────────────────────┘   │   └────────────────┘  │ │
│  │  ┌──────────────────────────────┐   │                        │ │
│  │  │   Orders Page                │   │   Fixed across pages   │ │
│  │  │   • Order History Table      │   │                        │ │
│  │  │   • Loading / Error States   │   │                        │ │
│  │  └──────────────────────────────┘   │                        │ │
│  └─────────────────────────────────────┴────────────────────────┘ │
└──────────────────────┬───────────────────────────────────────────┘
                       │ HTTP (REST API)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                              │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  /api/products│  │ /api/orders  │  │ /api/chat              │  │
│  │  (PostgreSQL) │  │  (MySQL)     │  │   ┌────────────────┐  │  │
│  └──────┬───────┘  └──────┬───────┘  │   │  LangGraph      │  │  │
│         │                 │           │   │  Shopping Agent │  │  │
│         ▼                 ▼           │   │  ┌──────────┐   │  │  │
│  ┌──────────┐      ┌──────────┐      │   │  │Greeting  │   │  │  │
│  │PostgreSQL │      │  MySQL   │      │   │  │Search    │   │  │  │
│  │Products   │      │ Orders   │      │   │  │Collect   │   │  │  │
│  │ChatHistory│      │          │      │   │  │Confirm   │   │  │  │
│  └──────────┘      └──────────┘      │   │  │OrderStatu├─┐ │  │  │
│                                       │   │  └──────────┘ │ │  │  │
│                                       │   └────────────────┘ │  │  │
│                                       └──────────────────────┴──┘  │
│                                                  │ Agent-to-Agent  │
│                                                  ▼ Protocol        │
│                                         ┌───────────────────────┐  │
│                                         │   ORDER AGENT         │  │
│                                         │   (Separate LangGraph) │  │
│                                         │   ┌───────────────┐   │  │
│                                         │   │ Extract Node  │   │  │
│                                         │   │ Query Node    │───┼──┼──► MySQL
│                                         │   │ Format Node   │   │  │
│                                         │   └───────────────┘   │  │
│                                         └───────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User types a message** in the chatbot panel → frontend sends `POST /api/chat`
2. **Inbound guardrails** scan the user's message for harmful content
3. **Main Shopping Agent** (LangGraph) classifies intent and routes:
   - **Search products** → calls `search_products()` → PostgreSQL
   - **Place order** → multi-turn collection → calls `place_order()` → MySQL
   - **Check order status** → **Agent-to-Agent Protocol** → Order Agent → MySQL
4. **Outbound guardrails** scan the AI response for safety/quality issues
5. **Response + guardrail status + session** stored in PostgreSQL `chat_history`
6. **Frontend renders** the response with green/red guardrail badges

---

## ✨ Features

### 🔍 Product Browsing
- Search products by name, brand, or ASIN
- View product details: price, rating, reviews, availability
- Best-seller and Prime badges
- Paginated results with min/max price and rating filters

### 🛒 Order Management
- Place orders through natural language conversation
- Multi-step order form: product selection, quantity, customer info, shipping
- Order summary with total cost before confirmation
- Order history table with statuses: Pending → Confirmed → Shipped → Delivered
- Cancel pending transactions

### 🤖 AI Chatbot (Fixed Right Panel)
- **Persistent across pages** — stays open while navigating products/orders
- Natural language understanding for all shopping tasks
- Tool-calling architecture: searches products, checks orders, places orders
- Context-aware multi-turn conversations
- **Greeting node** welcomes users and guides them
- **Order session tracking** remembers partial order details across messages

### 🛡️ AI Guardrails
- **Inbound** (9 categories): violence, sexual harassment, self-harm, attack, hate, unfairness, equal opportunity, vulnerability, insult
- **Outbound** (4 categories): fluency, legal, groundedness, relevance
- **Visual indicators** — green PASS badges or red BLOCKED badge per category
- Guardrail hits return a generic fallback message without exposing internals
- All guardrail activity logged in chat history

---

## 🧰 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript + Vite | Fast, type-safe UI |
| **Styling** | Tailwind CSS | Utility-first responsive design |
| **State** | Zustand | Lightweight store for chat state |
| **Icons** | Lucide React | Clean SVG icon library |
| **Backend** | Python 3.11 + FastAPI | Async REST API server |
| **AI Framework** | LangGraph + LangChain | Stateful agent graph orchestration |
| **LLM Provider** | OpenRouter (GPT-4o-mini) | Model-agnostic AI inference |
| **Products DB** | PostgreSQL 16 | Product catalog + chat history |
| **Orders DB** | MySQL 8.0 | Order transactions |
| **ORM** | SQLAlchemy | Database-agnostic query layer |
| **Containerization** | Docker Compose | Multi-service orchestration |

---

## 💾 Database Design

### PostgreSQL — `ai_shop` (Products + Chat History)

```
┌────────────────────────────────────────────────────────────────┐
│                         products                                 │
├────────────────────────────────────────────────────────────────┤
│ id              │ INTEGER (PK)                                   │
│ asin            │ VARCHAR(20) (UNIQUE)                           │
│ product_title   │ TEXT                                            │
│ product_price   │ VARCHAR(50)                                    │
│ currency        │ VARCHAR(10)  DEFAULT 'USD'                     │
│ product_star_rating │ DOUBLE PRECISION                           │
│ product_num_ratings  │ INTEGER                                   │
│ product_url     │ TEXT                                            │
│ product_photo   │ TEXT                                            │
│ is_best_seller  │ VARCHAR(10)  DEFAULT 'False'                   │
│ is_prime        │ VARCHAR(10)  DEFAULT 'False'                   │
│ sales_volume    │ VARCHAR(100)                                   │
│ product_availability │ TEXT                                      │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                       chat_history                               │
├────────────────────────────────────────────────────────────────┤
│ id              │ INTEGER (PK)                                   │
│ session_id      │ VARCHAR(100) (INDEXED)                         │
│ role            │ VARCHAR(20)  ('human' / 'ai')                  │
│ message         │ TEXT                                            │
│ inbound_guardrail_hit  │ VARCHAR(200) (nullable)                  │
│ outbound_guardrail_hit │ VARCHAR(200) (nullable)                  │
│ guardrail_action │ VARCHAR(50)  ('passed' / 'blocked')           │
│ created_at      │ TIMESTAMP  DEFAULT NOW()                       │
└────────────────────────────────────────────────────────────────┘
```

### MySQL — `ai_orders` (Orders)

```
┌────────────────────────────────────────────────────────────────┐
│                         orders                                    │
├────────────────────────────────────────────────────────────────┤
│ id              │ INTEGER (PK, AUTO_INCREMENT)                    │
│ customer_name   │ VARCHAR(100)                                    │
│ customer_email  │ VARCHAR(100)                                    │
│ product_asin    │ VARCHAR(20)                                     │
│ product_title   │ TEXT                                            │
│ quantity        │ INTEGER  DEFAULT 1                              │
│ total_price     │ FLOAT                                           │
│ currency        │ VARCHAR(10)  DEFAULT 'USD'                      │
│ status          │ VARCHAR(50)  DEFAULT 'Pending'                  │
│ shipping_address │ TEXT                                           │
│ order_date      │ TIMESTAMP  DEFAULT CURRENT_TIMESTAMP            │
│ delivery_date   │ VARCHAR(100)                                    │
└────────────────────────────────────────────────────────────────┘
```

### Why Two Databases?

| Database | Data | Reasoning |
|----------|------|-----------|
| **PostgreSQL** | Products, Chat History | Rich JSON support, full-text search (`ILIKE`), robust for catalog data |
| **MySQL** | Orders | ACID-compliant transactions, mature replication for order processing |
| **Integration** | Agent-to-Agent Protocol | The LLM chatbot seamlessly bridges both databases through tool-calling |

---

## 🤝 Agent-to-Agent Protocol

The project implements a true **Agent-to-Agent orchestration** pattern for order queries:

### How It Works

```
User: "What is the status of order 1234?"

┌──────────────────────────────────────────────┐
│        MAIN SHOPPING AGENT (LangGraph)         │
│                                                │
│  1. classify_intent() → "order_status"         │
│  2. order_status_node() runs                   │
│  3. tools.get_order_status(order_id=1234)      │
│     │                                          │
│     │  ─── Agent-to-Agent Protocol ──────▶     │
│     ▼                                          │
┌──────────────────────────────────────────────┐ │
│          ORDER AGENT (Separate LangGraph)      │ │
│                                                │ │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  │ │
│  │  Extract  │──▶│  Query   │──▶│  Format  │  │ │
│  │  Node     │   │  Node    │   │  Node    │  │ │
│  └──────────┘   └────┬─────┘   └──────────┘  │ │
│                       │                        │ │
│                       ▼                        │ │
│                  ┌──────────┐                  │ │
│                  │  MySQL   │                  │ │
│                  │  Orders  │                  │ │
│                  └──────────┘                  │ │
└────────────────────────────────────────────────┘ │
│  4. Returns structured JSON + friendly text      │
└──────────────────────────────────────────────────┘
```

### Why Separate Agents?

| Aspect | Main Agent | Order Agent |
|--------|-----------|-------------|
| **Role** | General shopping assistant | Order specialist |
| **Data source** | PostgreSQL (Products) | MySQL (Orders) |
| **System prompt** | Product + order + greeting | Orders-only focus |
| **Tools** | search_products, place_order | query_order_by_id, query_orders_by_email |
| **LLM context** | Full shopping context | Pure order context |
| **Error handling** | Generic fallback | Detailed "not found" with suggestions |

This separation brings **modularity**, **specialization**, and **security** — the Order Agent never has access to product data, and the Main Agent never directly touches MySQL.

---

## 🛡️ AI Guardrails

### Inbound Guardrails (User → AI)

| Category | What it catches |
|----------|----------------|
| 🔴 Violence | Kill, murder, weapon, assault |
| 🔴 Sexual Harassment | Explicit content, NSFW language |
| 🔴 Self-Harm | Suicide, self-harm references |
| 🔴 Attack | Doxxing, hacking, malware |
| 🔴 Hate | Racism, discrimination, hate speech |
| 🔴 Unfairness | Cheating, scams, manipulation |
| 🔴 Equal Opportunity | Unequal treatment, discrimination |
| 🔴 Vulnerability | Exploitation of vulnerable groups |
| 🔴 Insult | Personal attacks, abusive language |

### Outbound Guardrails (AI → User)

| Category | What it checks |
|----------|---------------|
| 🟢 Fluency | Complete sentences, readable text |
| 🟢 Legal | No medical/legal advice |
| 🟢 Groundedness | Response backed by database data |
| 🟢 Relevance | On-topic shopping conversation |

### Visual Feedback

Every chatbot response shows colored badges:

```
┌─────────────────────────────────────────────┐
│  🛡️ Inbound:  violence✅ sexual_harassment✅  │
│  hate✅ insult✅ unfairness✅                    │
│  🛡️ Outbound: fluency✅ relevance✅             │
│  groundedness✅ legal✅                        │
└─────────────────────────────────────────────┘
```

If a guardrail is **hit**, the badge turns red with a pulse animation, and the chatbot responds with a generic fallback message — never exposing internal system details.

---

## 📡 API Reference

### Health

```
GET /api/health
→ { "status": "ok", "service": "AI-shopping-cart" }
```

### Products (PostgreSQL)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/products` | List products (search, price/rating filters, pagination) |
| `GET` | `/api/products/{id}` | Get single product by ID |

**Query Parameters** (`GET /api/products`):
| Param | Type | Description |
|-------|------|-------------|
| `search` | string | Search in product title / ASIN |
| `min_price` | float | Minimum price filter |
| `max_price` | float | Maximum price filter |
| `min_rating` | float | Minimum star rating filter |
| `page` | int | Page number (default: 1) |
| `page_size` | int | Items per page (default: 20, max: 100) |

### Orders (MySQL)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/orders` | List all orders |
| `GET` | `/api/orders/{id}` | Get order by ID |
| `GET` | `/api/orders/email/{email}` | Get orders by customer email |
| `POST` | `/api/orders` | Create a new order |

### Chat (AI + Guardrails)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to AI chatbot |

**Request Body**:
```json
{
  "message": "What Nike t-shirts are available?",
  "session_id": "user-session-123"
}
```

**Response**:
```json
{
  "reply": "Here are the Nike t-shirts I found...",
  "session_id": "user-session-123",
  "inbound_guardrails": [
    { "name": "violence", "passed": true },
    { "name": "hate", "passed": true }
  ],
  "outbound_guardrails": [
    { "name": "fluency", "passed": true },
    { "name": "relevance", "passed": true }
  ],
  "show_order_button": false
}
```

---

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- OpenRouter API key (for LLM features)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/AI-shopping-cart.git
cd AI-shopping-cart

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENROUTER_API_KEY

# 3. Launch all services
docker compose up -d --build

# 4. Access the application
# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

The startup script automatically:
1. Creates PostgreSQL and MySQL databases
2. Seeds 500+ products from Amazon catalog into PostgreSQL
3. Initializes orders table in MySQL
4. Starts the FastAPI server with hot-reload
5. Launches the Vite dev server

### Verify It Works

```bash
# Health check
curl http://localhost:8000/api/health

# List products
curl http://localhost:8000/api/products?search=nike

# Chat with AI
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order 1?"}'
```

---

## 🔐 Environment Variables

Create `backend/.env`:

```env
# Required: OpenRouter API key for LLM features
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional: Override the default model
OPENROUTER_MODEL=openai/gpt-4o-mini

# Database URLs (defaults work with Docker Compose)
POSTGRES_URL=postgresql://ai:aisearch123@postgres:5432/ai_shop
MYSQL_URL=mysql+pymysql://ai:aisearch123@mysql:3306/ai_orders
```

> ⚠️ **Security**: The `.env` file is excluded from git via `.gitignore`. Never commit API keys or database passwords.

---

## 📁 Project Structure

```
ai-shopping-cart/
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py          # Main LangGraph agent (greeting, search, order flow)
│   │   │   ├── order_agent.py    # Order Agent (Agent-to-Agent protocol)
│   │   │   ├── tools.py          # Tool functions (search_products, place_order)
│   │   │   └── guardrails.py     # Inbound/outbound guardrail definitions
│   │   ├── routes/
│   │   │   ├── products.py       # Product REST endpoints
│   │   │   ├── orders.py         # Order REST endpoints
│   │   │   └── chat.py           # Chat endpoint (guardrails → graph → response)
│   │   ├── config.py             # Environment & settings
│   │   ├── database.py           # SQLAlchemy engine setup (PG + MySQL)
│   │   ├── models.py             # PostgreSQL models (Product, ChatHistory)
│   │   ├── models_mysql.py       # MySQL model (Order)
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── seed.py               # Database seeder (500+ products)
│   │   └── main.py               # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatPanel.tsx     # Fixed chatbot UI with guardrail badges
│   │   │   ├── Layout.tsx        # App shell with sidebar layout
│   │   │   └── Navbar.tsx        # Navigation bar
│   │   ├── pages/
│   │   │   ├── ProductsPage.tsx  # Product search & browse
│   │   │   └── OrdersPage.tsx    # Order history table
│   │   ├── api/
│   │   │   └── client.ts         # API client (products, orders, chat)
│   │   ├── store/
│   │   │   └── chatStore.ts      # Zustand chat state
│   │   ├── App.tsx               # Root component with routing
│   │   └── main.tsx              # Entry point
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml            # Orchestrates all 4 services
├── amazon_product.csv            # Product seed data
├── .gitignore
└── README.md
```

---

## 📸 Screenshots

### Product Search Page
```
┌────────────────────────────────────────────────────────────┐
│  🔍 [Search products...]        🛒 AI-Assisted Shopping   │
│                                                             │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Moto G Play 2023   │  │ Samsung Galaxy A03s │            │
│  │ ⭐ 4.3 ★★★★★       │  │ ⭐ 4.1 ★★★★☆        │            │
│  │ $99.99  🏆 Best    │  │ $49.88  📦 Prime     │            │
│  └────────────────────┘  └────────────────────┘            │
│  ┌────────────────────┐  ┌────────────────────┐            │
│  │ Apple AirTag       │  │ Amazon Echo Dot     │            │
│  │ ⭐ 4.7 ★★★★★       │  │ ⭐ 4.6 ★★★★★        │            │
│  │ $24.99  📦 Prime   │  │ $49.99  🏆 Best     │            │
│  └────────────────────┘  └────────────────────┘            │
└────────────────────────────────────────────────────────────┘
```

### AI Chatbot in Action
```
┌────────────────────────────────────────────────────┐
│  💬 AI Shopping Assistant                      🔒 │
├────────────────────────────────────────────────────┤
│                                                    │
│  🤖 Hello! Welcome to AI Shopping Cart! 😊         │
│  I can help you:                                   │
│  • 🔍 Search for products                         │
│  • 🛒 Place orders                                │
│  • 📦 Check order status                          │
│                                                    │
│  How can I assist you today?                       │
│                                                    │
│  ─────────────────────────────────────             │
│  🧑 What Nike t-shirts are available?              │
│  ─────────────────────────────────────             │
│  🤖 Let me search for that!                        │
│                                                    │
│  Found 6 products matching 'nike t-shirt':         │
│  • Nike Men's Dri-FIT Tee ... $24.99 ★★★★☆       │
│  • Nike Sportswear Club Tee ... $17.99 ★★★★☆     │
│                                                    │
│  🛡️ Inbound: ✅✅✅✅✅✅✅✅✅                       │
│  🛡️ Outbound: ✅✅✅✅                              │
│                                                    │
│  [Type your message...]                    [Send]  │
└────────────────────────────────────────────────────┘
```

### Chat History Persistence
```
postgres=# SELECT role, message, guardrail_action FROM chat_history;
 role  |              message              | guardrail_action
-------+-----------------------------------+------------------
 human | What Nike t-shirts are available?  | passed
 ai    | Found 6 products matching...       | passed
 human | What is the status of order 1?    | passed
 ai    | Order #1 — Delivered...           | passed
(4 rows)
```

---

## 🧪 Testing

### Manual Test Flows

```bash
# Test product search
curl -s http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me Samsung phones"}'

# Test order status
curl -s http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the status of order 1?"}'

# Test delivery question
curl -s http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "When will my order 1 get delivered?"}'

# Test place order flow
curl -s http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to order B0CHH6X6H2 3 quantities"}'
```

---

## 🛠️ Built With

| Tool | Version |
|------|---------|
| React | 18.x |
| TypeScript | 5.x |
| Vite | 5.x |
| Tailwind CSS | 3.x |
| Python | 3.11 |
| FastAPI | 0.110+ |
| LangGraph | latest |
| LangChain | latest |
| SQLAlchemy | 2.x |
| PostgreSQL | 16 (Alpine) |
| MySQL | 8.0 |
| Docker | 24+ |

---

## 📄 License

This project is built for demonstration and educational purposes.

---

<p align="center">
  Made with ❤️ using React, FastAPI, LangGraph & Docker
</p>

<p align="center">
  <a href="#-table-of-contents">↑ Back to top</a>
</p>