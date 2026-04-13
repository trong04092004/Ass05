import { useEffect, useMemo, useState } from 'react'
import { clearBackofficeSession, getBackofficeAccessToken } from '../backofficeAuth'

type Promotion = {
    id: number
    name: string
    discount_percent: number
    book_id?: number | null
    start_date?: string | null
    end_date?: string | null
    created_at: string
}

type SupplyOrder = {
    id: number
    book_id: number
    quantity: number
    supplier: string
    note: string
    created_at: string
}

type StaffRecord = {
    id: number
    user: number
    role: 'ADMIN' | 'MANAGER' | 'STAFF'
    employee_code: string
    department: string
    is_active: boolean
}

type Category = {
    id: number
    name: string
    slug: string
    description?: string
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

type ProductServiceKey = 'book' | 'electronics' | 'fashion' | 'toy' | 'grocery' | 'furniture' | 'beauty' | 'sports' | 'pet' | 'stationery'

type ProductRow = {
    id: number
    serviceKey: ProductServiceKey
    serviceName: string
    name: string
    sku: string
    price: string | number
    stock: number
}

type ManagerCapabilities = {
    promotions: boolean
    supply: boolean
    staff: boolean
    categories: boolean
    orders: boolean
    products: boolean
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

const statusLabelMap: Record<string, string> = {
    pending: 'Pending',
    processing: 'Processing',
    shipping: 'Shipping',
    completed: 'Delivered',
    cancelled: 'Cancelled',
}

function formatMoney(value: string | number | undefined) {
    const n = Number.parseFloat(String(value ?? 0)) || 0
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n)
}

function toDateLabel(raw?: string) {
    if (!raw) {
        return '-'
    }
    const parsed = new Date(raw)
    if (Number.isNaN(parsed.getTime())) {
        return '-'
    }
    return parsed.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
}

export function ManagerDashboardPage() {
    const [promotions, setPromotions] = useState<Promotion[]>([])
    const [supplyOrders, setSupplyOrders] = useState<SupplyOrder[]>([])
    const [staffRows, setStaffRows] = useState<StaffRecord[]>([])
    const [categories, setCategories] = useState<Category[]>([])
    const [products, setProducts] = useState<ProductRow[]>([])
    const [orders, setOrders] = useState<OrderRow[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const [promoName, setPromoName] = useState('')
    const [promoDiscount, setPromoDiscount] = useState('')
    const [promoBookId, setPromoBookId] = useState('')
    const [promoStart, setPromoStart] = useState('')
    const [promoEnd, setPromoEnd] = useState('')
    const [categoryName, setCategoryName] = useState('')
    const [categoryDescription, setCategoryDescription] = useState('')
    const [newProductServiceKey, setNewProductServiceKey] = useState<ProductServiceKey>('electronics')
    const [newProductName, setNewProductName] = useState('')
    const [newProductSku, setNewProductSku] = useState('')
    const [newProductBrand, setNewProductBrand] = useState('')
    const [newProductPrice, setNewProductPrice] = useState('')
    const [newProductStock, setNewProductStock] = useState('')
    const [newProductDescription, setNewProductDescription] = useState('')
    const [newProductImageUrl, setNewProductImageUrl] = useState('')
    const [orderQuery, setOrderQuery] = useState('')
    const [statusDrafts, setStatusDrafts] = useState<Record<number, string>>({})
    const [capabilities, setCapabilities] = useState<ManagerCapabilities>({
        promotions: false,
        supply: false,
        staff: false,
        categories: false,
        orders: false,
        products: false,
    })

    const accessToken = getBackofficeAccessToken()

    const authHeaders = useMemo(() => {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' }
        if (accessToken) {
            headers.Authorization = `Bearer ${accessToken}`
        }
        return headers
    }, [accessToken])

    const fetchManagerData = async () => {
        setLoading(true)
        setError('')
        const deniedOrAuth = new Set([401, 403])
        const issues: string[] = []

        const [promoResult, supplyResult, staffResult, categoryResult, orderResult] = await Promise.allSettled([
            fetch(`${gatewayBase}/api/promotions/`, { headers: authHeaders, credentials: 'include' }),
            fetch(`${gatewayBase}/api/supply-orders/`, { headers: authHeaders, credentials: 'include' }),
            fetch(`${gatewayBase}/api/staff/`, { headers: authHeaders, credentials: 'include' }),
            fetch(`${gatewayBase}/api/categories/`, { headers: authHeaders, credentials: 'include' }),
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

        let canPromotions = false
        let canSupply = false
        let canStaff = false
        let canCategories = false
        let canOrders = false
        let canProducts = false

        if (promoResult.status === 'fulfilled') {
            if (promoResult.value.ok) {
                const promoJson = (await promoResult.value.json()) as Promotion[]
                setPromotions(Array.isArray(promoJson) ? promoJson : [])
                canPromotions = true
            } else {
                setPromotions([])
                if (!deniedOrAuth.has(promoResult.value.status)) {
                    issues.push('Khong tai duoc du lieu khuyen mai.')
                }
            }
        } else {
            setPromotions([])
            issues.push('Loi ket noi khuyen mai.')
        }

        if (supplyResult.status === 'fulfilled') {
            if (supplyResult.value.ok) {
                const supplyJson = (await supplyResult.value.json()) as SupplyOrder[]
                setSupplyOrders(Array.isArray(supplyJson) ? supplyJson : [])
                canSupply = true
            } else {
                setSupplyOrders([])
                if (!deniedOrAuth.has(supplyResult.value.status)) {
                    issues.push('Khong tai duoc du lieu phieu nhap kho.')
                }
            }
        } else {
            setSupplyOrders([])
            issues.push('Loi ket noi phieu nhap kho.')
        }

        if (staffResult.status === 'fulfilled') {
            if (staffResult.value.ok) {
                const staffJson = (await staffResult.value.json()) as StaffRecord[]
                setStaffRows(Array.isArray(staffJson) ? staffJson : [])
                canStaff = true
            } else {
                setStaffRows([])
                if (!deniedOrAuth.has(staffResult.value.status)) {
                    issues.push('Khong tai duoc du lieu staff-service.')
                }
            }
        } else {
            setStaffRows([])
            issues.push('Loi ket noi staff-service.')
        }

        if (categoryResult.status === 'fulfilled') {
            if (categoryResult.value.ok) {
                const categoryJson = (await categoryResult.value.json()) as Category[]
                setCategories(Array.isArray(categoryJson) ? categoryJson : [])
                canCategories = true
            } else {
                setCategories([])
                if (!deniedOrAuth.has(categoryResult.value.status)) {
                    issues.push('Khong tai duoc du lieu danh muc.')
                }
            }
        } else {
            setCategories([])
            issues.push('Loi ket noi danh muc.')
        }

        if (orderResult.status === 'fulfilled') {
            if (orderResult.value.ok) {
                const orderJson = (await orderResult.value.json()) as OrderRow[]
                const safeOrders = Array.isArray(orderJson) ? orderJson : []
                setOrders(safeOrders)
                setStatusDrafts(
                    safeOrders.reduce<Record<number, string>>((acc, row) => {
                        acc[row.id] = row.status || 'pending'
                        return acc
                    }, {}),
                )
                canOrders = true
            } else {
                setOrders([])
                setStatusDrafts({})
                if (!deniedOrAuth.has(orderResult.value.status)) {
                    issues.push('Khong tai duoc du lieu don hang.')
                }
            }
        } else {
            setOrders([])
            setStatusDrafts({})
            issues.push('Loi ket noi don hang.')
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
                    return {
                        id: Number(row.id || 0),
                        serviceKey: service.key,
                        serviceName: service.label,
                        name: rawName || rawTitle || 'Untitled',
                        sku: typeof row.sku === 'string' ? row.sku : `${service.key.toUpperCase()}-${String(row.id || '')}`,
                        price: typeof row.price === 'number' || typeof row.price === 'string' ? row.price : 0,
                        stock: Number(row.stock ?? row.stock_quantity ?? 0),
                    }
                }),
            )
        }
        setProducts(aggregatedProducts)

        setCapabilities({
            promotions: canPromotions,
            supply: canSupply,
            staff: canStaff,
            categories: canCategories,
            orders: canOrders,
            products: canProducts,
        })
        setError(issues.join(' '))
        setLoading(false)
    }

    useEffect(() => {
        void fetchManagerData()
    }, [])

    const handleCreatePromotion = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setError('')

        const payload = {
            name: promoName.trim(),
            discount_percent: Number(promoDiscount),
            book_id: promoBookId ? Number(promoBookId) : null,
            start_date: promoStart || null,
            end_date: promoEnd || null,
        }

        try {
            const response = await fetch(`${gatewayBase}/api/promotions/`, {
                method: 'POST',
                headers: authHeaders,
                credentials: 'include',
                body: JSON.stringify(payload),
            })
            if (!response.ok) {
                const data = await response.json()
                throw new Error(data?.error || 'Tao khuyen mai that bai.')
            }

            setPromoName('')
            setPromoDiscount('')
            setPromoBookId('')
            setPromoStart('')
            setPromoEnd('')
            await fetchManagerData()
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Tao khuyen mai that bai.'
            setError(message)
        }
    }

    const handleLogout = () => {
        clearBackofficeSession()
        window.location.href = '/admin/login'
    }

    const slugify = (raw: string) =>
        raw
            .toLowerCase()
            .trim()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/(^-|-$)/g, '')

    const handleCreateCategory = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setError('')

        const name = categoryName.trim()
        if (!name) {
            setError('Ten danh muc khong duoc de trong.')
            return
        }

        try {
            const response = await fetch(`${gatewayBase}/api/categories/`, {
                method: 'POST',
                headers: authHeaders,
                credentials: 'include',
                body: JSON.stringify({
                    name,
                    slug: slugify(name),
                    description: categoryDescription.trim(),
                }),
            })
            if (!response.ok) {
                throw new Error('Tao danh muc that bai.')
            }
            setCategoryName('')
            setCategoryDescription('')
            await fetchManagerData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Tao danh muc that bai.')
        }
    }

    const handleDeleteCategory = async (categoryId: number) => {
        setError('')
        try {
            const response = await fetch(`${gatewayBase}/api/categories/${categoryId}/`, {
                method: 'DELETE',
                headers: authHeaders,
                credentials: 'include',
            })
            if (!response.ok && response.status !== 204) {
                throw new Error('Xoa danh muc that bai.')
            }
            await fetchManagerData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Xoa danh muc that bai.')
        }
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
            await fetchManagerData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Tao san pham that bai.')
        }
    }

    const updateOrderStatus = async (orderId: number) => {
        const nextStatus = statusDrafts[orderId] || ''
        if (!nextStatus) {
            return
        }
        setError('')
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
            await fetchManagerData()
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Cap nhat trang thai don that bai.')
        }
    }

    const filteredOrders = useMemo(() => {
        const q = orderQuery.trim().toLowerCase()
        if (!q) {
            return orders
        }
        return orders.filter((row) => {
            return (
                String(row.id).includes(q)
                || String(row.customer_id).includes(q)
                || (row.status || '').toLowerCase().includes(q)
            )
        })
    }, [orders, orderQuery])

    const totalRevenue = useMemo(
        () => orders.reduce((sum, row) => sum + (Number.parseFloat(String(row.total_amount ?? 0)) || 0), 0),
        [orders],
    )
    const pendingCount = useMemo(() => orders.filter((row) => row.status === 'pending').length, [orders])
    const shippingCount = useMemo(() => orders.filter((row) => row.status === 'shipping').length, [orders])

    return (
        <div className="bo-shell">
            <aside className="bo-sidebar">
                <div className="bo-brand">
                    <h1>Admin Ledger</h1>
                    <p>Management Console</p>
                </div>
                <nav className="bo-nav">
                    {capabilities.orders && (
                        <a className="active" href="#orders">
                            <span className="material-symbols-outlined">package</span>
                            <span>Orders</span>
                        </a>
                    )}
                    {capabilities.products && (
                        <a href="#products-overview">
                            <span className="material-symbols-outlined">inventory_2</span>
                            <span>Products</span>
                        </a>
                    )}
                    {(capabilities.promotions || capabilities.categories || capabilities.supply || capabilities.staff) && (
                        <a href="#manager-tools">
                            <span className="material-symbols-outlined">monitoring</span>
                            <span>Tools</span>
                        </a>
                    )}
                </nav>
                <div className="bo-user-card">
                    <img src="https://images.unsplash.com/photo-1542190891-2093d38760f2?auto=format&fit=crop&w=200&q=80" alt="Manager" />
                    <div>
                        <strong>Marcus Thorne</strong>
                        <small>Senior Manager</small>
                    </div>
                </div>
            </aside>

            <main className="bo-main">
                <header className="bo-header">
                    <div>
                        <h2>Order Management</h2>
                        <p>Review and process the latest transactions.</p>
                    </div>
                    <div className="bo-header-actions">
                        {capabilities.orders && (
                            <label className="bo-search">
                                <span className="material-symbols-outlined">search</span>
                                <input
                                    type="text"
                                    value={orderQuery}
                                    onChange={(event) => setOrderQuery(event.target.value)}
                                    placeholder="Search orders..."
                                />
                            </label>
                        )}
                        <button type="button" className="bo-primary-btn" onClick={() => void fetchManagerData()}>
                            <span className="material-symbols-outlined">sync</span>
                            Refresh
                        </button>
                        <button type="button" className="bo-outline-btn" onClick={handleLogout}>
                            Logout
                        </button>
                    </div>
                </header>

                {loading && <p className="state-line">Dang tai du lieu quan ly...</p>}
                {error && <p className="state-line error">{error}</p>}
                {!capabilities.orders && !capabilities.promotions && !capabilities.categories && !capabilities.supply && !capabilities.staff && !capabilities.products && !loading && (
                    <p className="state-line">Khong co module nao duoc cap quyen cho tai khoan nay.</p>
                )}

                {capabilities.orders && (
                    <section className="bo-kpi-grid">
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-blue"><span className="material-symbols-outlined">shopping_bag</span></div>
                            <p>Total Orders</p>
                            <strong>{orders.length}</strong>
                        </article>
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-green"><span className="material-symbols-outlined">schedule</span></div>
                            <p>Pending</p>
                            <strong>{pendingCount}</strong>
                        </article>
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-orange"><span className="material-symbols-outlined">local_shipping</span></div>
                            <p>In Transit</p>
                            <strong>{shippingCount}</strong>
                        </article>
                        <article className="bo-kpi-card">
                            <div className="bo-kpi-icon icon-teal"><span className="material-symbols-outlined">payments</span></div>
                            <p>Revenue</p>
                            <strong>{formatMoney(totalRevenue)}</strong>
                        </article>
                    </section>
                )}

                {capabilities.orders && (
                    <section id="orders" className="bo-table-wrap">
                        <div className="bo-table-head">
                            <h3>All Orders</h3>
                            <span>{filteredOrders.length} records</span>
                        </div>
                        <div className="bo-scroll">
                            <table className="bo-table">
                                <thead>
                                    <tr>
                                        <th>Order ID</th>
                                        <th>Customer</th>
                                        <th>Date</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredOrders.slice(0, 12).map((row) => (
                                        <tr key={row.id}>
                                            <td>#ORD-{row.id}</td>
                                            <td>Customer #{row.customer_id}</td>
                                            <td>{toDateLabel(row.created_at)}</td>
                                            <td>{formatMoney(row.total_amount)}</td>
                                            <td>
                                                <span className={badgeClassMap[row.status] || 'bo-badge'}>
                                                    {statusLabelMap[row.status] || row.status}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="bo-inline-actions">
                                                    <select
                                                        value={statusDrafts[row.id] || row.status}
                                                        onChange={(event) =>
                                                            setStatusDrafts((prev) => ({ ...prev, [row.id]: event.target.value }))
                                                        }
                                                    >
                                                        {statusOptions.map((status) => (
                                                            <option value={status} key={status}>
                                                                {status}
                                                            </option>
                                                        ))}
                                                    </select>
                                                    <button type="button" onClick={() => void updateOrderStatus(row.id)}>
                                                        Update
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {capabilities.products && (
                    <section id="products-overview" className="bo-table-wrap">
                        <div className="bo-table-head">
                            <h3>Cross-service Products</h3>
                            <span>{products.length} products</span>
                        </div>
                        <div className="bo-scroll">
                            <table className="bo-table">
                                <thead>
                                    <tr>
                                        <th>Service</th>
                                        <th>Product</th>
                                        <th>SKU</th>
                                        <th>Price</th>
                                        <th>Stock</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {products.slice(0, 30).map((product) => (
                                        <tr key={`${product.serviceKey}-${product.id}`}>
                                            <td>{product.serviceName}</td>
                                            <td>{product.name}</td>
                                            <td>{product.sku}</td>
                                            <td>{formatMoney(product.price)}</td>
                                            <td>{product.stock}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>
                )}

                {(capabilities.promotions || capabilities.categories || capabilities.products) && (
                    <section id="manager-tools" className="bo-admin-grid">
                        {capabilities.promotions && (
                            <article className="bo-panel">
                                <h3>Create Promotion</h3>
                                <form className="bo-form bo-form-grid" onSubmit={handleCreatePromotion}>
                                    <input required value={promoName} onChange={(e) => setPromoName(e.target.value)} placeholder="Promotion name" type="text" />
                                    <input required value={promoDiscount} onChange={(e) => setPromoDiscount(e.target.value)} placeholder="Discount %" type="number" min="0" max="100" />
                                    <input value={promoBookId} onChange={(e) => setPromoBookId(e.target.value)} placeholder="Book ID (optional)" type="number" min="1" />
                                    <input value={promoStart} onChange={(e) => setPromoStart(e.target.value)} type="date" />
                                    <input value={promoEnd} onChange={(e) => setPromoEnd(e.target.value)} type="date" />
                                    <button type="submit" className="bo-primary-btn">Create</button>
                                </form>
                            </article>
                        )}

                        {capabilities.categories && (
                            <article className="bo-panel">
                                <h3>Create Category</h3>
                                <form className="bo-form bo-form-grid" onSubmit={handleCreateCategory}>
                                    <input required value={categoryName} onChange={(e) => setCategoryName(e.target.value)} placeholder="Category name" type="text" />
                                    <input value={categoryDescription} onChange={(e) => setCategoryDescription(e.target.value)} placeholder="Description" type="text" />
                                    <button type="submit" className="bo-primary-btn">Save category</button>
                                </form>
                            </article>
                        )}

                        {capabilities.products && (
                            <article className="bo-panel">
                                <h3>Add Product (Non-book)</h3>
                                <form className="bo-form bo-form-grid" onSubmit={handleCreateProduct}>
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
                                    <input value={newProductDescription} onChange={(e) => setNewProductDescription(e.target.value)} placeholder="Description" type="text" />
                                    <button type="submit" className="bo-primary-btn">Create product</button>
                                </form>
                            </article>
                        )}
                    </section>
                )}

                {(capabilities.categories || capabilities.promotions || capabilities.supply || capabilities.staff || capabilities.products) && (
                    <section className="bo-split-grid">
                        {capabilities.categories && (
                            <article className="bo-table-wrap">
                                <div className="bo-table-head">
                                    <h3>Categories</h3>
                                    <span>{categories.length}</span>
                                </div>
                                <div className="bo-scroll">
                                    <table className="bo-table">
                                        <thead>
                                            <tr>
                                                <th>ID</th>
                                                <th>Name</th>
                                                <th>Slug</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {categories.map((category) => (
                                                <tr key={category.id}>
                                                    <td>{category.id}</td>
                                                    <td>{category.name}</td>
                                                    <td>{category.slug}</td>
                                                    <td>
                                                        <button
                                                            type="button"
                                                            className="bo-danger-btn"
                                                            onClick={() => void handleDeleteCategory(category.id)}
                                                        >
                                                            Delete
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </article>
                        )}

                        {(capabilities.promotions || capabilities.supply || capabilities.staff || capabilities.products) && (
                            <article className="bo-table-wrap">
                                <div className="bo-table-head">
                                    <h3>Promotions & Supply</h3>
                                    <span>{promotions.length} / {supplyOrders.length}</span>
                                </div>
                                <div className="bo-metrics-stack">
                                    {capabilities.products && (
                                        <div className="bo-mini-stat">
                                            <span>Total Products</span>
                                            <strong>{products.length}</strong>
                                        </div>
                                    )}
                                    {capabilities.promotions && (
                                        <div className="bo-mini-stat">
                                            <span>Promotions</span>
                                            <strong>{promotions.length}</strong>
                                        </div>
                                    )}
                                    {capabilities.supply && (
                                        <div className="bo-mini-stat">
                                            <span>Supply Orders</span>
                                            <strong>{supplyOrders.length}</strong>
                                        </div>
                                    )}
                                    {capabilities.staff && (
                                        <>
                                            <div className="bo-mini-stat">
                                                <span>Active Staff</span>
                                                <strong>{staffRows.filter((row) => row.is_active).length}</strong>
                                            </div>
                                            <div className="bo-mini-stat">
                                                <span>Total Staff</span>
                                                <strong>{staffRows.length}</strong>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </article>
                        )}
                    </section>
                )}
            </main>
        </div>
    )
}
