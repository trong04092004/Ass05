import { useEffect, useMemo, useState } from 'react'
import { clearBackofficeSession, getBackofficeAccessToken } from '../backofficeAuth'
import { getAuthRoleFromCookie } from '../auth'

type SupplyOrder = {
    id: number
    product_service?: ProductServiceKey
    product_id?: number
    book_id?: number
    quantity: number
    supplier: string
    note: string
    created_at: string
}

type ProductServiceKey = 'book' | 'electronics' | 'fashion' | 'toy' | 'grocery' | 'furniture' | 'beauty' | 'sports' | 'pet' | 'stationery'

type ProductRow = {
    id: number
    serviceKey: ProductServiceKey
    serviceName: string
    name: string
    sku: string
    brand: string
    author?: string
    category?: string
    price: string | number
    stock: number
    description?: string
    image_url?: string
}

type OrderRow = {
    id: number
    status: string
    customer_id: number
    address?: string
    phone?: string
    total_amount?: string | number
    created_at?: string
}

type StaffCapabilities = {
    products: boolean
    supply: boolean
    orders: boolean
}

const productServiceOptions: Array<{ key: ProductServiceKey, label: string }> = [
    { key: 'book', label: 'Sach' },
    { key: 'electronics', label: 'Dien tu' },
    { key: 'fashion', label: 'Thoi trang' },
    { key: 'toy', label: 'Do choi' },
    { key: 'grocery', label: 'Tap hoa' },
    { key: 'furniture', label: 'Noi that' },
    { key: 'beauty', label: 'Lam dep' },
    { key: 'sports', label: 'The thao' },
    { key: 'pet', label: 'Thu cung' },
    { key: 'stationery', label: 'Van phong pham' },
]

const nonBookServiceOptions = productServiceOptions.filter((service) => service.key !== 'book')

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const gatewayHost = runtimeHost === 'localhost' ? '127.0.0.1' : runtimeHost
const gatewayBase = `http://${gatewayHost}:18000`

const statusOptions = ['pending', 'processing', 'shipping', 'completed', 'cancelled']

const badgeClassMap: Record<string, string> = {
    pending: 'bo-badge bo-badge-pending',
    processing: 'bo-badge bo-badge-processing',
    shipping: 'bo-badge bo-badge-shipping',
    completed: 'bo-badge bo-badge-completed',
    cancelled: 'bo-badge bo-badge-cancelled',
}

function formatMoney(value: string | number | undefined) {
    const n = Number.parseFloat(String(value ?? 0)) || 0
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n)
}

function formatDateLabel(raw?: string) {
    if (!raw) {
        return '-'
    }
    const parsed = new Date(raw)
    if (Number.isNaN(parsed.getTime())) {
        return '-'
    }
    return parsed.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

function stockLevelClass(stock: number) {
    if (stock <= 5) {
        return 'danger'
    }
    if (stock <= 20) {
        return 'warning'
    }
    return 'ok'
}

function stockPercent(stock: number) {
    return Math.max(6, Math.min(100, Math.round((stock / 80) * 100)))
}

export function StaffDashboardPage() {
    const [supplyOrders, setSupplyOrders] = useState<SupplyOrder[]>([])
    const [products, setProducts] = useState<ProductRow[]>([])
    const [orders, setOrders] = useState<OrderRow[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const [supplyBookId, setSupplyBookId] = useState('')
    const [supplyServiceKey, setSupplyServiceKey] = useState<ProductServiceKey>('book')
    const [supplyQty, setSupplyQty] = useState('')
    const [supplySupplier, setSupplySupplier] = useState('')
    const [supplyNote, setSupplyNote] = useState('')
    const [newProductServiceKey, setNewProductServiceKey] = useState<ProductServiceKey>('electronics')
    const [newProductName, setNewProductName] = useState('')
    const [newProductSku, setNewProductSku] = useState('')
    const [newProductBrand, setNewProductBrand] = useState('')
    const [newProductPrice, setNewProductPrice] = useState('')
    const [newProductStock, setNewProductStock] = useState('')
    const [newProductDescription, setNewProductDescription] = useState('')
    const [newProductImageUrl, setNewProductImageUrl] = useState('')
    const [editingProductId, setEditingProductId] = useState<number | null>(null)
    const [editingProductService, setEditingProductService] = useState<ProductServiceKey | null>(null)
    const [editingPrice, setEditingPrice] = useState('')
    const [editingStock, setEditingStock] = useState('')
    const [statusDrafts, setStatusDrafts] = useState<Record<number, string>>({})
    const [capabilities, setCapabilities] = useState<StaffCapabilities>({
        products: false,
        supply: false,
        orders: false,
    })

    const accessToken = getBackofficeAccessToken()

    const authHeaders = useMemo(() => {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (accessToken) {
            headers.Authorization = `Bearer ${accessToken}`
        }
        return headers
    }, [accessToken])

    const fetchDashboardData = async () => {
        setLoading(true)
        setError('')
        const deniedOrAuth = new Set([401, 403])
        const issues: string[] = []

        const [supplyResult, ordersResult] = await Promise.allSettled([
            fetch(`${gatewayBase}/api/supply-orders/`, { headers: authHeaders, credentials: 'include' }),
            fetch(`${gatewayBase}/api/orders/`, { headers: authHeaders, credentials: 'include' }),
        ])

        const productResults = await Promise.allSettled(
            productServiceOptions.map((service) => {
                const endpoint = service.key === 'book'
                    ? `${gatewayBase}/api/books/`
                    : `${gatewayBase}/api/products/${service.key}/`
                return fetch(endpoint, { headers: authHeaders, credentials: 'include' })
            }),
        )

        let canSupply = false
        let canProducts = false
        let canOrders = false

        if (supplyResult.status === 'fulfilled') {
            if (supplyResult.value.ok) {
                const supplyJson = (await supplyResult.value.json()) as SupplyOrder[]
                setSupplyOrders(Array.isArray(supplyJson) ? supplyJson : [])
                canSupply = true
            } else {
                setSupplyOrders([])
                if (!deniedOrAuth.has(supplyResult.value.status)) {
                    issues.push('Khong tai duoc du lieu supply-orders.')
                }
            }
        } else {
            setSupplyOrders([])
            issues.push('Loi ket noi supply-orders.')
        }

        const aggregatedProducts: ProductRow[] = []
        for (let idx = 0; idx < productResults.length; idx += 1) {
            const service = productServiceOptions[idx]
            const result = productResults[idx]
            if (result.status !== 'fulfilled') {
                issues.push(`Loi ket noi san pham (${service.label}).`)
                continue
            }

            if (!result.value.ok) {
                if (!deniedOrAuth.has(result.value.status)) {
                    issues.push(`Khong tai duoc du lieu san pham (${service.label}).`)
                }
                continue
            }

            const rows = (await result.value.json()) as Array<Record<string, unknown>>
            const safeRows = Array.isArray(rows) ? rows : []
            canProducts = true

            aggregatedProducts.push(
                ...safeRows.map((row) => {
                    const rawName = typeof row.name === 'string' ? row.name : ''
                    const rawTitle = typeof row.title === 'string' ? row.title : ''
                    const rawBrand = typeof row.brand === 'string' ? row.brand : ''
                    const rawAuthor = typeof row.author === 'string' ? row.author : ''
                    return {
                        id: Number(row.id || 0),
                        serviceKey: service.key,
                        serviceName: service.label,
                        name: rawName || rawTitle || 'Untitled',
                        sku: typeof row.sku === 'string' ? row.sku : `${service.key.toUpperCase()}-${String(row.id || '')}`,
                        brand: rawBrand || rawAuthor || service.label,
                        author: rawAuthor || undefined,
                        category: typeof row.category === 'string' ? row.category : undefined,
                        price: typeof row.price === 'number' || typeof row.price === 'string' ? row.price : 0,
                        stock: Number(row.stock ?? row.stock_quantity ?? 0),
                        description: typeof row.description === 'string' ? row.description : undefined,
                        image_url: typeof row.image_url === 'string' ? row.image_url : undefined,
                    }
                }),
            )
        }
        setProducts(aggregatedProducts)

        if (ordersResult.status === 'fulfilled') {
            if (ordersResult.value.ok) {
                const ordersJson = (await ordersResult.value.json()) as OrderRow[]
                const safeOrders = Array.isArray(ordersJson) ? ordersJson : []
                setOrders(safeOrders)
                setStatusDrafts(
                    safeOrders.reduce<Record<number, string>>((acc, row) => {
                        acc[row.id] = row.status
                        return acc
                    }, {}),
                )
                canOrders = true
            } else {
                setOrders([])
                setStatusDrafts({})
                if (!deniedOrAuth.has(ordersResult.value.status)) {
                    issues.push('Khong tai duoc du lieu don hang.')
                }
            }
        } else {
            setOrders([])
            setStatusDrafts({})
            issues.push('Loi ket noi don hang.')
        }

        setCapabilities({ products: canProducts, supply: canSupply, orders: canOrders })
        setError(issues.join(' '))
        setLoading(false)
    }

    useEffect(() => {
        void fetchDashboardData()
    }, [])

    const handleCreateSupplyOrder = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setError('')

        const payload = {
            product_service: supplyServiceKey,
            product_id: Number(supplyBookId),
            book_id: supplyServiceKey === 'book' ? Number(supplyBookId) : null,
            quantity: Number(supplyQty),
            supplier: supplySupplier.trim(),
            note: supplyNote.trim(),
        }

        try {
            const response = await fetch(`${gatewayBase}/api/supply-orders/`, {
                method: 'POST',
                headers: authHeaders,
                credentials: 'include',
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                const data = await response.json()
                throw new Error(data?.detail || 'Tao phieu nhap that bai.')
            }
            setSupplyBookId('')
            setSupplyQty('')
            setSupplySupplier('')
            setSupplyNote('')
            await fetchDashboardData()
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Tao phieu nhap that bai.'
            setError(message)
        }
    }

    const handleLogout = () => {
        clearBackofficeSession()
        window.location.href = '/admin/login'
    }

    const handleCreateProduct = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setError('')

        const payload = {
            name: newProductName.trim(),
            sku: newProductSku.trim(),
            brand: newProductBrand.trim(),
            description: newProductDescription.trim(),
            price: Number(newProductPrice),
            stock: Number(newProductStock),
            image_url: newProductImageUrl.trim() || null,
        }

        try {
            const response = await fetch(`${gatewayBase}/api/products/${newProductServiceKey}/`, {
                method: 'POST',
                credentials: 'include',
                headers: authHeaders,
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                throw new Error('Tao san pham that bai.')
            }
            setNewProductName('')
            setNewProductSku('')
            setNewProductBrand('')
            setNewProductPrice('')
            setNewProductStock('')
            setNewProductDescription('')
            setNewProductImageUrl('')
            await fetchDashboardData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Tao san pham that bai.')
        }
    }

    const beginEditProduct = (product: ProductRow) => {
        setEditingProductId(product.id)
        setEditingProductService(product.serviceKey)
        setEditingPrice(String(product.price))
        setEditingStock(String(product.stock))
    }

    const submitProductUpdate = async (product: ProductRow) => {
        setError('')
        try {
            const endpoint = product.serviceKey === 'book'
                ? `${gatewayBase}/api/books/${product.id}/`
                : `${gatewayBase}/api/products/${product.serviceKey}/${product.id}/`

            const payload = product.serviceKey === 'book'
                ? {
                    title: product.name,
                    author: product.author || product.brand,
                    category: product.category || '',
                    description: product.description || '',
                    price: Number(editingPrice),
                    stock: Number(editingStock),
                }
                : {
                    name: product.name,
                    sku: product.sku,
                    brand: product.brand,
                    description: product.description || '',
                    image_url: product.image_url || '',
                    price: Number(editingPrice),
                    stock: Number(editingStock),
                }

            const response = await fetch(endpoint, {
                method: 'PUT',
                credentials: 'include',
                headers: authHeaders,
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                throw new Error('Cap nhat san pham that bai.')
            }
            setEditingProductId(null)
            setEditingProductService(null)
            await fetchDashboardData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Cap nhat san pham that bai.')
        }
    }

    const updateOrderStatus = async (orderId: number) => {
        setError('')
        const nextStatus = statusDrafts[orderId] || ''
        if (!nextStatus) {
            return
        }
        try {
            const response = await fetch(`${gatewayBase}/api/orders/${orderId}/`, {
                method: 'PATCH',
                credentials: 'include',
                headers: authHeaders,
                body: JSON.stringify({ status: nextStatus }),
            })
            if (!response.ok) {
                throw new Error('Cap nhat trang thai don that bai.')
            }
            await fetchDashboardData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Cap nhat trang thai don that bai.')
        }
    }

    const role = getAuthRoleFromCookie()
    const lowStockCount = useMemo(() => products.filter((product) => product.stock <= 5).length, [products])
    const inventoryValue = useMemo(
        () => products.reduce((sum, product) => sum + (Number.parseFloat(String(product.price)) || 0) * (product.stock || 0), 0),
        [products],
    )

    return (
        <div className="bo-shell">
            <aside className="bo-sidebar">
                <div className="bo-brand">
                    <h1>Admin Ledger</h1>
                    <p>Management Console</p>
                </div>
                <nav className="bo-nav">
                    {capabilities.products && (
                        <a className="active" href="#products">
                            <span className="material-symbols-outlined">inventory_2</span>
                            <span>Products</span>
                        </a>
                    )}
                    {capabilities.orders && (
                        <a href="#order-control">
                            <span className="material-symbols-outlined">receipt_long</span>
                            <span>Orders</span>
                        </a>
                    )}
                    {capabilities.supply && (
                        <a href="#operations">
                            <span className="material-symbols-outlined">inventory</span>
                            <span>Supply</span>
                        </a>
                    )}
                </nav>
                <div className="bo-user-card">
                    <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=200&q=80" alt="Staff" />
                    <div>
                        <strong>Marcus Vane</strong>
                        <small>{role || 'staff'} workspace</small>
                    </div>
                </div>
            </aside>

            <main className="bo-main">
                <header className="bo-header">
                    <div>
                        <h2>Product Inventory</h2>
                        <p>Curate products and maintain stock precision for operations.</p>
                    </div>
                    <div className="bo-header-actions">
                        <button type="button" className="bo-primary-btn" onClick={() => void fetchDashboardData()}>
                            <span className="material-symbols-outlined">sync</span>
                            Sync
                        </button>
                        <button type="button" className="bo-outline-btn" onClick={handleLogout}>
                            Logout
                        </button>
                    </div>
                </header>

                {loading && <p className="state-line">Dang tai du lieu van hanh...</p>}
                {error && <p className="state-line error">{error}</p>}

                {!capabilities.products && !capabilities.supply && !capabilities.orders && !loading && (
                    <p className="state-line">Khong co module nao duoc cap quyen cho tai khoan nay.</p>
                )}

                {capabilities.products && (
                    <section className="bo-kpi-grid bo-kpi-grid-staff">
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-blue"><span className="material-symbols-outlined">inventory</span></div>
                            <p>Total Products</p>
                            <strong>{products.length}</strong>
                        </article>
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-red"><span className="material-symbols-outlined">warning</span></div>
                            <p>Low Stock Alerts</p>
                            <strong>{lowStockCount}</strong>
                        </article>
                        <article className="bo-kpi-card bo-kpi-card-dark">
                            <div className="bo-kpi-icon icon-soft"><span className="material-symbols-outlined">verified</span></div>
                            <p>Inventory Value</p>
                            <strong>{formatMoney(inventoryValue)}</strong>
                        </article>
                    </section>
                )}

                {capabilities.products && (
                    <section id="products" className="bo-table-wrap">
                        <div className="bo-table-head">
                            <h3>Product Catalog</h3>
                            <span>{products.length} products</span>
                        </div>
                        <div className="bo-scroll">
                            <table className="bo-table">
                                <thead>
                                    <tr>
                                        <th>Service</th>
                                        <th>Product</th>
                                        <th>SKU/Brand</th>
                                        <th>Price</th>
                                        <th>Stock Level</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products.slice(0, 36).map((product) => {
                                        const isEditing = editingProductId === product.id && editingProductService === product.serviceKey
                                        const levelClass = stockLevelClass(product.stock)
                                        return (
                                            <tr key={`${product.serviceKey}-${product.id}`}>
                                                <td>{product.serviceName}</td>
                                                <td className="bo-product-name">
                                                    <strong>{product.name}</strong>
                                                    <small>#{product.id}</small>
                                                </td>
                                                <td>{product.sku || product.brand || '-'}</td>
                                                <td>
                                                    {isEditing ? (
                                                        <input
                                                            type="number"
                                                            min="0"
                                                            value={editingPrice}
                                                            onChange={(e) => setEditingPrice(e.target.value)}
                                                        />
                                                    ) : (
                                                        formatMoney(product.price)
                                                    )}
                                                </td>
                                                <td>
                                                    <div className="bo-stock-wrap">
                                                        <div className="bo-stock-track">
                                                            <span className={`bo-stock-fill ${levelClass}`} style={{ width: `${stockPercent(product.stock)}%` }} />
                                                        </div>
                                                        {isEditing ? (
                                                            <input
                                                                type="number"
                                                                min="0"
                                                                value={editingStock}
                                                                onChange={(e) => setEditingStock(e.target.value)}
                                                            />
                                                        ) : (
                                                            <small>{product.stock} units</small>
                                                        )}
                                                    </div>
                                                </td>
                                                <td>
                                                    {isEditing ? (
                                                        <button type="button" onClick={() => void submitProductUpdate(product)}>
                                                            Save
                                                        </button>
                                                    ) : (
                                                        <button type="button" onClick={() => beginEditProduct(product)}>
                                                            Edit
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {(capabilities.supply || capabilities.products) && (
                    <section id="operations" className="bo-admin-grid">
                        {capabilities.supply && (
                            <article className="bo-panel">
                                <h3>Create Supply Order</h3>
                                <form className="bo-form" onSubmit={handleCreateSupplyOrder}>
                                    <select value={supplyServiceKey} onChange={(e) => setSupplyServiceKey(e.target.value as ProductServiceKey)}>
                                        {productServiceOptions.map((service) => (
                                            <option key={service.key} value={service.key}>{service.label}</option>
                                        ))}
                                    </select>
                                    <input required value={supplyBookId} onChange={(e) => setSupplyBookId(e.target.value)} placeholder="Product ID" type="number" min="1" />
                                    <input required value={supplyQty} onChange={(e) => setSupplyQty(e.target.value)} placeholder="Quantity" type="number" min="1" />
                                    <input value={supplySupplier} onChange={(e) => setSupplySupplier(e.target.value)} placeholder="Supplier" type="text" />
                                    <textarea value={supplyNote} onChange={(e) => setSupplyNote(e.target.value)} placeholder="Note" rows={3} />
                                    <button type="submit" className="bo-primary-btn">Create order</button>
                                </form>
                            </article>
                        )}

                        {capabilities.products && (
                            <article className="bo-panel">
                                <h3>Add Product (Non-book)</h3>
                                <form className="bo-form" onSubmit={handleCreateProduct}>
                                    <select value={newProductServiceKey} onChange={(e) => setNewProductServiceKey(e.target.value as ProductServiceKey)}>
                                        {nonBookServiceOptions.map((service) => (
                                            <option key={service.key} value={service.key}>{service.label}</option>
                                        ))}
                                    </select>
                                    <input required value={newProductName} onChange={(e) => setNewProductName(e.target.value)} placeholder="Product name" type="text" />
                                    <input required value={newProductSku} onChange={(e) => setNewProductSku(e.target.value)} placeholder="SKU" type="text" />
                                    <input value={newProductBrand} onChange={(e) => setNewProductBrand(e.target.value)} placeholder="Brand" type="text" />
                                    <input required value={newProductPrice} onChange={(e) => setNewProductPrice(e.target.value)} placeholder="Price" type="number" min="0" />
                                    <input required value={newProductStock} onChange={(e) => setNewProductStock(e.target.value)} placeholder="Stock" type="number" min="0" />
                                    <input value={newProductImageUrl} onChange={(e) => setNewProductImageUrl(e.target.value)} placeholder="Image URL" type="url" />
                                    <textarea value={newProductDescription} onChange={(e) => setNewProductDescription(e.target.value)} placeholder="Description" rows={3} />
                                    <button type="submit" className="bo-primary-btn">Create product</button>
                                </form>
                            </article>
                        )}
                    </section>
                )}

                {(capabilities.supply || capabilities.orders) && (
                    <section className="bo-split-grid">
                        {capabilities.supply && (
                            <article className="bo-table-wrap">
                                <div className="bo-table-head">
                                    <h3>Recent Supply Orders</h3>
                                    <span>{supplyOrders.length}</span>
                                </div>
                                <div className="bo-scroll">
                                    <table className="bo-table">
                                        <thead>
                                            <tr>
                                                <th>ID</th>
                                                <th>Service</th>
                                                <th>Product ID</th>
                                                <th>Quantity</th>
                                                <th>Supplier</th>
                                                <th>Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {supplyOrders.slice(0, 14).map((row) => (
                                                <tr key={row.id}>
                                                    <td>{row.id}</td>
                                                    <td>{row.product_service || 'book'}</td>
                                                    <td>{row.product_id ?? row.book_id ?? '-'}</td>
                                                    <td>{row.quantity}</td>
                                                    <td>{row.supplier || '-'}</td>
                                                    <td>{formatDateLabel(row.created_at)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </article>
                        )}

                        {capabilities.orders && (
                            <article className="bo-table-wrap">
                                <div id="order-control" className="bo-table-head">
                                    <h3>Order Status Control</h3>
                                    <span>{orders.length}</span>
                                </div>
                                <div className="bo-scroll">
                                    <table className="bo-table">
                                        <thead>
                                            <tr>
                                                <th>Order</th>
                                                <th>Customer</th>
                                                <th>Status</th>
                                                <th>Update</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {orders.slice(0, 14).map((order) => (
                                                <tr key={order.id}>
                                                    <td>#ORD-{order.id}</td>
                                                    <td>{order.customer_id}</td>
                                                    <td>
                                                        <div className="bo-inline-actions">
                                                            <span className={badgeClassMap[order.status] || 'bo-badge'}>{order.status}</span>
                                                            <select
                                                                value={statusDrafts[order.id] || order.status}
                                                                onChange={(e) =>
                                                                    setStatusDrafts((prev) => ({ ...prev, [order.id]: e.target.value }))
                                                                }
                                                            >
                                                                {statusOptions.map((status) => (
                                                                    <option value={status} key={status}>
                                                                        {status}
                                                                    </option>
                                                                ))}
                                                            </select>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <button type="button" onClick={() => void updateOrderStatus(order.id)}>
                                                            Apply
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </article>
                        )}
                    </section>
                )}

            </main>
        </div>
    )
}
