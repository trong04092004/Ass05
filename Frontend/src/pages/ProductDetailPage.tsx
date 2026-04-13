import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { formatPrice, productFallbackImage, productImageForService, services } from '../catalog'
import type { Product, ServiceConfig } from '../catalog'
import { authHeaders, gatewayBase, getCustomerId } from '../customerSession'

type ProductWithService = Product & {
    serviceKey: string
}

export function ProductDetailPage() {
    const { serviceKey, productId } = useParams()
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [product, setProduct] = useState<ProductWithService | null>(null)
    const [related, setRelated] = useState<ProductWithService[]>([])
    const [quantity, setQuantity] = useState(1)
    const [selectedSize, setSelectedSize] = useState('42mm')
    const [adding, setAdding] = useState(false)
    const [info, setInfo] = useState('')

    const service = useMemo<ServiceConfig | undefined>(
        () => services.find((s) => s.key === serviceKey),
        [serviceKey],
    )

    useEffect(() => {
        void loadDetail()
    }, [serviceKey, productId])

    const loadDetail = async () => {
        if (!serviceKey || !productId) {
            setError('Thiếu thông tin sản phẩm.')
            return
        }

        setLoading(true)
        setError('')
        try {
            const normalizeProduct = (raw: Record<string, unknown>): Product => ({
                id: typeof raw.id === 'number' ? raw.id : Number(raw.id || 0),
                name: typeof raw.name === 'string' ? raw.name : (typeof raw.title === 'string' ? raw.title : 'Sản phẩm'),
                sku: typeof raw.sku === 'string' ? raw.sku : (typeof raw.isbn === 'string' ? raw.isbn : ''),
                brand: typeof raw.brand === 'string' ? raw.brand : (typeof raw.author === 'string' ? raw.author : ''),
                description: typeof raw.description === 'string' ? raw.description : '',
                price: typeof raw.price === 'number' || typeof raw.price === 'string' ? raw.price : 0,
                stock: typeof raw.stock === 'number' ? raw.stock : undefined,
                stock_quantity: typeof raw.stock_quantity === 'number' ? raw.stock_quantity : undefined,
                image_url: typeof raw.image_url === 'string' ? raw.image_url : null,
            })

            const detailEndpoint = serviceKey === 'book'
                ? `${gatewayBase}/api/books/${productId}/`
                : `${gatewayBase}/api/products/${serviceKey}/${productId}/`
            const listEndpoint = serviceKey === 'book'
                ? `${gatewayBase}/api/books/`
                : `${gatewayBase}/api/products/${serviceKey}/`

            const detailResp = await fetch(detailEndpoint, {
                credentials: 'include',
            })
            if (!detailResp.ok) {
                throw new Error(`Không tải được sản phẩm (${detailResp.status})`)
            }
            const detailRaw = (await detailResp.json()) as Record<string, unknown>
            const detailJson = normalizeProduct(detailRaw)
            const detail = { ...detailJson, serviceKey }
            setProduct(detail)

            const listResp = await fetch(listEndpoint, {
                credentials: 'include',
            })
            const listJson = listResp.ok ? ((await listResp.json()) as Array<Record<string, unknown>>) : []
            const rows = (Array.isArray(listJson) ? listJson : []).map((item) => normalizeProduct(item))
            setRelated(
                rows
                    .filter((item) => item.id !== detail.id)
                    .slice(0, 4)
                    .map((item) => ({ ...item, serviceKey })),
            )
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Lỗi tải sản phẩm.'
            setError(message)
        } finally {
            setLoading(false)
        }
    }

    const handleAddToCart = async () => {
        if (!product) {
            return
        }
        const customerId = getCustomerId()
        if (!customerId) {
            navigate('/auth/login')
            return
        }

        setAdding(true)
        setInfo('')
        try {
            const response = await fetch(`${gatewayBase}/api/cart-items/`, {
                method: 'POST',
                credentials: 'include',
                headers: authHeaders(),
                body: JSON.stringify({
                    customer_id: customerId,
                    product_service: serviceKey || 'book',
                    product_id: product.id,
                    ...(serviceKey === 'book' ? { book_id: product.id } : {}),
                    quantity,
                }),
            })

            if (!response.ok) {
                const json = (await response.json()) as { error?: string }
                throw new Error(json.error || 'Không thêm được vào giỏ hàng.')
            }
            setInfo('Đã thêm sản phẩm vào giỏ hàng.')
        } catch (err) {
            setInfo(err instanceof Error ? err.message : 'Không thêm được vào giỏ hàng.')
        } finally {
            setAdding(false)
        }
    }

    if (loading) {
        return <section className="product-detail-page"><p className="state-line">Đang tải chi tiết sản phẩm...</p></section>
    }

    if (error || !product) {
        return (
            <section className="product-detail-page">
                <p className="state-line error">{error || 'Không tìm thấy sản phẩm.'}</p>
                <Link to="/shop" className="catalog-link">Quay lại cửa hàng</Link>
            </section>
        )
    }

    const displayImage = productImageForService(product, service)

    return (
        <section className="product-detail-page">
            <div className="product-detail-grid">
                <div className="product-gallery-main">
                    <img
                        src={displayImage}
                        alt={product.name}
                        onError={(event) => {
                            const target = event.currentTarget
                            target.onerror = null
                            target.src = productFallbackImage(product.name, service?.key)
                        }}
                    />
                    <div className="product-thumbs">
                        <img src={displayImage} alt={`${product.name} 1`} />
                        <img src={related[0] ? productImageForService(related[0], service) : displayImage} alt={`${product.name} 2`} />
                        <img src={related[1] ? productImageForService(related[1], service) : displayImage} alt={`${product.name} 3`} />
                    </div>
                </div>

                <aside className="product-detail-info">
                    <p className="edition">Premium Edition</p>
                    <h1>{product.name}</h1>
                    <p className="price">{formatPrice(product.price)}</p>
                    <p className="desc">{product.description || `Sản phẩm thuộc danh mục ${service?.name || 'Sản phẩm'} với thiết kế tối giản.`}</p>

                    <div className="variant-row">
                        <span>Size</span>
                        <div className="size-buttons">
                            {['42mm', '46mm'].map((size) => (
                                <button
                                    key={size}
                                    type="button"
                                    className={size === selectedSize ? 'active' : ''}
                                    onClick={() => setSelectedSize(size)}
                                >
                                    {size}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="qty-row">
                        <button type="button" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>-</button>
                        <span>{quantity}</span>
                        <button type="button" onClick={() => setQuantity((q) => q + 1)}>+</button>
                    </div>

                    <button className="primary-btn btn-wide" type="button" onClick={() => void handleAddToCart()} disabled={adding}>
                        {adding ? 'Đang thêm...' : 'Thêm vào giỏ hàng'}
                    </button>
                    <button className="ghost-btn btn-wide" type="button" onClick={() => navigate('/checkout')}>
                        Mua ngay
                    </button>
                    {info && <p className="state-line">{info}</p>}
                </aside>
            </div>

            <div className="section-head">
                <div>
                    <h2>Sản phẩm tương tự</h2>
                </div>
                <Link className="catalog-link" to="/shop">Xem tất cả</Link>
            </div>
            <div className="shop-grid">
                {related.map((item) => (
                    <article className="shop-card" key={`${item.serviceKey}-${item.id}`}>
                        <Link to={`/product/${item.serviceKey}/${item.id}`} className="shop-card-media">
                            <img src={productImageForService(item, service)} alt={item.name} />
                        </Link>
                        <div className="shop-card-meta">
                            <h4>{item.name}</h4>
                            <span>{formatPrice(item.price)}</span>
                        </div>
                    </article>
                ))}
            </div>
        </section>
    )
}
