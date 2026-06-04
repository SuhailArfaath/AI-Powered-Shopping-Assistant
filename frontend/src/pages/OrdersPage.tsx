import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Package, Search, Plus, Loader2, AlertCircle, CheckCircle, Truck, Clock, XCircle, User, Mail, MapPin, ShoppingCart } from 'lucide-react'
import { api, Order, OrderCreate, Product } from '../api/client'

const STATUS_ICONS: Record<string, React.ReactNode> = {
  'Delivered': <CheckCircle size={16} className="text-emerald-500" />,
  'Shipped': <Truck size={16} className="text-blue-500" />,
  'Confirmed': <CheckCircle size={16} className="text-blue-500" />,
  'Pending': <Clock size={16} className="text-amber-500" />,
  'Cancelled': <XCircle size={16} className="text-red-500" />,
}

const STATUS_COLORS: Record<string, string> = {
  'Delivered': 'bg-emerald-100 text-emerald-800',
  'Shipped': 'bg-blue-100 text-blue-800',
  'Confirmed': 'bg-blue-100 text-blue-800',
  'Pending': 'bg-amber-100 text-amber-800',
  'Cancelled': 'bg-red-100 text-red-800',
}

function OrderCard({ order }: { order: Order }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="text-xs text-gray-400 font-mono">Order #{order.id}</p>
          <h3 className="font-semibold text-gray-800 text-sm mt-1 line-clamp-1">{order.product_title}</h3>
        </div>
        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] || 'bg-gray-100 text-gray-800'}`}>
          {STATUS_ICONS[order.status] || null}
          {order.status}
        </span>
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <User size={14} className="text-gray-400" />
          <span>{order.customer_name}</span>
        </div>
        <div className="flex items-center gap-2">
          <Mail size={14} className="text-gray-400" />
          <span className="text-xs">{order.customer_email}</span>
        </div>
        <div className="flex items-center gap-2">
          <MapPin size={14} className="text-gray-400" />
          <span className="text-xs line-clamp-1">{order.shipping_address}</span>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <ShoppingCart size={14} className="text-gray-400" />
          <span>Qty: <strong>{order.quantity}</strong></span>
        </div>
        <div className="text-right">
          <p className="font-bold text-gray-800">{order.currency} ${order.total_price.toFixed(2)}</p>
          {order.delivery_date && (
            <p className="text-[10px] text-gray-400">{order.delivery_date}</p>
          )}
        </div>
      </div>
    </div>
  )
}

function CreateOrderModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<OrderCreate>({
    customer_name: '',
    customer_email: '',
    product_asin: '',
    product_title: '',
    quantity: 1,
    total_price: 0,
    currency: 'USD',
    shipping_address: '',
  })
  const [searchProduct, setSearchProduct] = useState('')
  const [showProductPicker, setShowProductPicker] = useState(false)

  const { data: productSearch } = useQuery({
    queryKey: ['products-search', searchProduct],
    queryFn: () => api.getProducts(searchProduct || undefined, 1, 10),
    enabled: showProductPicker && searchProduct.length > 0,
  })

  const mutation = useMutation({
    mutationFn: api.createOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      onClose()
      setForm({
        customer_name: '',
        customer_email: '',
        product_asin: '',
        product_title: '',
        quantity: 1,
        total_price: 0,
        currency: 'USD',
        shipping_address: '',
      })
    },
  })

  if (!isOpen) return null

  const handleProductSelect = (product: Product) => {
    const price = parseFloat(product.product_price?.replace('$', '') || '0')
    setForm({
      ...form,
      product_asin: product.asin,
      product_title: product.product_title,
      total_price: price * form.quantity,
    })
    setShowProductPicker(false)
  }

  const updateQuantity = (qty: number) => {
    const price = parseFloat(form.total_price.toString()) / Math.max(1, form.quantity)
    setForm({
      ...form,
      quantity: Math.max(1, qty),
      total_price: price * Math.max(1, qty),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <ShoppingCart size={20} className="text-blue-600" />
            Place New Order
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">&times;</button>
        </div>

        {/* Product Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Product</label>
          {form.product_title ? (
            <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
              <span className="text-sm text-blue-800 truncate">{form.product_title}</span>
              <button onClick={() => setForm({...form, product_asin: '', product_title: '', total_price: 0})} className="text-red-400 hover:text-red-600 text-xs ml-2">Change</button>
            </div>
          ) : (
            <div>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchProduct}
                  onChange={(e) => { setSearchProduct(e.target.value); setShowProductPicker(true) }}
                  placeholder="Search products..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onFocus={() => setShowProductPicker(true)}
                />
              </div>
              {showProductPicker && productSearch && productSearch.products.length > 0 && (
                <div className="mt-1 border border-gray-200 rounded-lg max-h-40 overflow-y-auto bg-white shadow">
                  {productSearch.products.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => handleProductSelect(p)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0"
                    >
                      <span className="line-clamp-1">{p.product_title}</span>
                      <span className="text-xs text-gray-400">${p.product_price} | {p.asin}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Customer Info */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              value={form.customer_name}
              onChange={(e) => setForm({...form, customer_name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={form.customer_email}
              onChange={(e) => setForm({...form, customer_email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="john@email.com"
            />
          </div>
        </div>

        {/* Quantity & Price */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
            <input
              type="number"
              min={1}
              value={form.quantity}
              onChange={(e) => updateQuantity(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Total ($)</label>
            <input
              type="number"
              step="0.01"
              value={form.total_price.toFixed(2)}
              onChange={(e) => setForm({...form, total_price: parseFloat(e.target.value) || 0})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Shipping */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">Shipping Address</label>
          <textarea
            value={form.shipping_address}
            onChange={(e) => setForm({...form, shipping_address: e.target.value})}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            placeholder="123 Main St, City, State ZIP"
          />
        </div>

        {/* Submit */}
        <button
          onClick={() => mutation.mutate()}
          disabled={!form.customer_name || !form.customer_email || !form.product_asin || !form.shipping_address || mutation.isPending}
          className="w-full bg-blue-600 text-white py-3 rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {mutation.isPending ? (
            <><Loader2 className="animate-spin" size={18} /> Placing Order...</>
          ) : (
            <><ShoppingCart size={18} /> Place Order</>
          )}
        </button>

        {mutation.isError && (
          <p className="text-red-500 text-sm mt-2 text-center">Error placing order. Please try again.</p>
        )}
      </div>
    </div>
  )
}

export default function OrdersPage() {
  const [emailFilter, setEmailFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [debouncedEmail, setDebouncedEmail] = useState('')

  const { data, isLoading, error } = useQuery({
    queryKey: ['orders', debouncedEmail],
    queryFn: () => debouncedEmail ? api.getOrdersByEmail(debouncedEmail) : api.getOrders(),
  })

  const handleEmailChange = (value: string) => {
    setEmailFilter(value)
    const timer = setTimeout(() => setDebouncedEmail(value), 400)
    return () => clearTimeout(timer)
  }

  return (
    <div>
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Package className="text-blue-600" size={28} />
            Orders
          </h2>
          <p className="text-gray-500 mt-1">View all orders or filter by email.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2.5 rounded-xl hover:bg-blue-700 transition-colors font-medium text-sm"
        >
          <Plus size={18} />
          New Order
        </button>
      </div>

      {/* Email Filter */}
      <div className="relative mb-6 max-w-md">
        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="text"
          value={emailFilter}
          onChange={(e) => handleEmailChange(e.target.value)}
          placeholder="Filter by email address..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          aria-label="Filter orders by email"
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-blue-600" size={40} />
          <span className="ml-3 text-gray-500">Loading orders...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center justify-center py-20">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center max-w-md">
            <AlertCircle size={40} className="text-red-500 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-800 mb-2">Connection Error</h3>
            <p className="text-red-600 text-sm">
              Unable to load orders. Please make sure the backend server is running.
            </p>
          </div>
        </div>
      )}

      {/* Orders */}
      {data && (
        <>
          <p className="text-sm text-gray-500 mb-4">
            Showing <span className="font-semibold">{data.orders.length}</span> order{data.orders.length !== 1 ? 's' : ''}
          </p>

          {data.orders.length === 0 ? (
            <div className="text-center py-16">
              <Package size={48} className="text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600">No orders found</h3>
              <p className="text-gray-400 text-sm mt-1">
                {debouncedEmail ? 'No orders found for this email.' : 'Create your first order!'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.orders.map((order) => (
                <OrderCard key={order.id} order={order} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Create Order Modal */}
      <CreateOrderModal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} />
    </div>
  )
}