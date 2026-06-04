const API_BASE = '/api'

export interface Product {
  id: number
  asin: string
  product_title: string
  product_price: string | null
  product_original_price: string | null
  currency: string
  product_star_rating: number | null
  product_num_ratings: number | null
  product_url: string | null
  product_photo: string | null
  product_minimum_offer_price: string | null
  is_best_seller: string
  is_amazon_choice: string
  is_prime: string
  sales_volume: string | null
  product_availability: string | null
}

export interface ProductListResponse {
  total: number
  products: Product[]
}

export interface Order {
  id: number
  customer_name: string
  customer_email: string
  product_asin: string
  product_title: string
  quantity: number
  total_price: number
  currency: string
  status: string
  shipping_address: string
  order_date: string | null
  delivery_date: string | null
}

export interface OrderListResponse {
  total: number
  orders: Order[]
}

export interface OrderCreate {
  customer_name: string
  customer_email: string
  product_asin: string
  product_title: string
  quantity: number
  total_price: number
  currency: string
  shipping_address: string
}

export interface GuardrailInfo {
  name: string
  passed: boolean
}

export interface ChatResponse {
  reply: string
  session_id: string
  inbound_guardrails: GuardrailInfo[]
  outbound_guardrails: GuardrailInfo[]
  show_order_button: boolean
}

export interface ChatRequest {
  message: string
  session_id: string
}

async function apiRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const fullUrl = `${API_BASE}${url}`
  const res = await fetch(fullUrl, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })
  
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(`API Error ${res.status}: ${errorText}`)
  }
  
  return res.json()
}

export const api = {
  // Products
  getProducts: (search?: string, page = 1, pageSize = 20) => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    params.set('page', page.toString())
    params.set('page_size', pageSize.toString())
    return apiRequest<ProductListResponse>(`/products?${params}`)
  },

  getProduct: (id: number) => apiRequest<Product>(`/products/${id}`),

  // Orders
  getOrders: () => apiRequest<OrderListResponse>('/orders'),
  getOrder: (id: number) => apiRequest<Order>(`/orders/${id}`),
  getOrdersByEmail: (email: string) => apiRequest<OrderListResponse>(`/orders/email/${encodeURIComponent(email)}`),
  createOrder: (order: OrderCreate) => apiRequest<Order>('/orders', {
    method: 'POST',
    body: JSON.stringify(order),
  }),

  // Chat
  sendChat: (request: ChatRequest) => apiRequest<ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify(request),
  }),
}