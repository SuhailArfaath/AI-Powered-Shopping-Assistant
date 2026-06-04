import { NavLink } from 'react-router-dom'
import { ShoppingCart, Package, Bot } from 'lucide-react'

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="bg-blue-600 text-white p-2 rounded-lg">
          <ShoppingCart size={24} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-800">AI Shopping Cart</h1>
          <p className="text-xs text-gray-500">AI-Powered Shopping Assistant</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <NavLink
          to="/products"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              isActive
                ? 'bg-blue-100 text-blue-700 font-semibold'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          <Package size={18} />
          Products
        </NavLink>
        <NavLink
          to="/orders"
          className={({ isActive }) =>
            `flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              isActive
                ? 'bg-blue-100 text-blue-700 font-semibold'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          <Bot size={18} />
          Orders
        </NavLink>
      </div>
    </nav>
  )
}