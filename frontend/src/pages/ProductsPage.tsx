import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Star, Package, ShoppingCart, AlertCircle, Loader2, ChevronLeft, ChevronRight } from 'lucide-react'
import { api, Product } from '../api/client'

function StarRating({ rating }: { rating: number | null }) {
  if (!rating) return <span className="text-gray-400 text-sm">No ratings</span>
  const full = Math.floor(rating)
  const stars = []
  for (let i = 0; i < 5; i++) {
    stars.push(
      <Star
        key={i}
        size={14}
        className={i < full ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}
      />
    )
  }
  return (
    <div className="flex items-center gap-1">
      {stars}
      <span className="text-gray-500 text-xs ml-1">{rating.toFixed(1)}</span>
    </div>
  )
}

function ProductCard({ product }: { product: Product }) {
  const isBestSeller = product.is_best_seller === 'True'
  const isPrime = product.is_prime === 'True'

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all hover:border-blue-300 group">
      {/* Image */}
      <div className="h-48 bg-gray-100 flex items-center justify-center p-4 overflow-hidden">
        {product.product_photo ? (
          <img
            src={product.product_photo}
            alt={product.product_title}
            className="h-full object-contain group-hover:scale-105 transition-transform"
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://via.placeholder.com/200?text=No+Image'
            }}
          />
        ) : (
          <Package size={48} className="text-gray-300" />
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {isBestSeller && (
          <span className="inline-block bg-amber-100 text-amber-800 text-[10px] font-semibold px-2 py-0.5 rounded-full mb-2">
            🏆 Best Seller
          </span>
        )}
        {isPrime && (
          <span className="inline-block bg-blue-100 text-blue-700 text-[10px] font-semibold px-2 py-0.5 rounded-full mb-2 ml-1">
            📦 Prime
          </span>
        )}

        <h3 className="font-semibold text-gray-800 text-sm line-clamp-2 mb-2 min-h-[2.5rem]">
          {product.product_title}
        </h3>

        <StarRating rating={product.product_star_rating} />
        {product.product_num_ratings && (
          <p className="text-xs text-gray-400 mt-0.5">
            {product.product_num_ratings.toLocaleString()} ratings
          </p>
        )}

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-xl font-bold text-gray-800">
            {product.product_price || 'N/A'}
          </span>
          {product.product_original_price && product.product_original_price !== product.product_price && (
            <span className="text-sm text-gray-400 line-through">
              {product.product_original_price}
            </span>
          )}
        </div>

        {product.sales_volume && (
          <p className="text-xs text-gray-500 mt-1">{product.sales_volume}</p>
        )}

        {product.product_availability && (
          <p className="text-xs text-emerald-600 mt-1 font-medium">
            {product.product_availability}
          </p>
        )}

        <p className="text-[10px] text-gray-400 mt-2 font-mono">ASIN: {product.asin}</p>
      </div>
    </div>
  )
}

export default function ProductsPage() {
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, error } = useQuery({
    queryKey: ['products', debouncedSearch, page],
    queryFn: () => api.getProducts(debouncedSearch || undefined, page),
  })

  const handleSearchChange = (value: string) => {
    setSearch(value)
    setPage(1)
    // Debounce search
    const timer = setTimeout(() => setDebouncedSearch(value), 400)
    return () => clearTimeout(timer)
  }

  return (
    <div>
      {/* Page Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Package className="text-blue-600" size={28} />
          Products Catalog
        </h2>
        <p className="text-gray-500 mt-1">
          Browse our product catalog. Click on products to see details or ask the AI assistant for recommendations.
        </p>
      </div>

      {/* Search Bar */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          value={search}
          onChange={(e) => handleSearchChange(e.target.value)}
          placeholder="Search products by name, brand, or keyword..."
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          aria-label="Search products"
        />
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-blue-600" size={40} />
          <span className="ml-3 text-gray-500">Loading products...</span>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="flex items-center justify-center py-20">
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center max-w-md">
            <AlertCircle size={40} className="text-red-500 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-800 mb-2">Connection Error</h3>
            <p className="text-red-600 text-sm">
              Unable to load products. Please make sure the backend server is running.
            </p>
          </div>
        </div>
      )}

      {/* Products Grid */}
      {data && (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-500">
              Showing <span className="font-semibold text-gray-700">{data.products.length}</span> of{' '}
              <span className="font-semibold text-gray-700">{data.total}</span> products
            </p>
          </div>

          {data.products.length === 0 ? (
            <div className="text-center py-16">
              <Package size={48} className="text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-600">No products found</h3>
              <p className="text-gray-400 text-sm mt-1">
                Try a different search term or browse all products.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {data.products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          {/* Pagination */}
          {data.total > 20 && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft size={16} /> Previous
              </button>
              <span className="text-sm text-gray-500">
                Page {page} of {Math.ceil(data.total / 20)}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
                className="flex items-center gap-1 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}