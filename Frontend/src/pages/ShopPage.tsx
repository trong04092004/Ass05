import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, loadProducts, productFallbackImage, productImageForService, services, toNumberPrice } from '../catalog'
import type { ProductServiceKey, ShopProduct } from '../catalog'
import { fetchMyRealtimeRecommendations, trackInteractionEvent, type RecommendationItem } from '../ai'
import { getCustomerId } from '../customerSession'

type SortMode = 'featured' | 'price-asc' | 'price-desc' | 'newest'

export function ShopPage() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [products, setProducts] = useState<ShopProduct[]>([])
    const [selectedServices, setSelectedServices] = useState<string[]>(services.map((s) => s.key))
    const [search, setSearch] = useState('')
    const [sortBy, setSortBy] = useState<SortMode>('featured')
    const [maxPrice, setMaxPrice] = useState(5000)
    const [page, setPage] = useState(1)
    const [realtimeRecs, setRealtimeRecs] = useState<RecommendationItem[]>([])
    const [loadingRealtimeRecs, setLoadingRealtimeRecs] = useState(false)
    const customerId = getCustomerId()
    const serviceByKey = useMemo(() => new Map(services.map((service) => [service.key, service])), [])

    useEffect(() => {
        void loadCatalog()
    }, [])

    const loadCatalog = async () => {
        setLoading(true)
        setError('')

        const results = await Promise.allSettled(
            services.map(async (service) => {
                const data = await loadProducts(service)
                return data.map((item) => ({
                    ...item,
                    serviceKey: service.key,
                    serviceName: service.name,
                    normalizedPrice: toNumberPrice(item.price),
                }))
            }),
        )

        const merged: ShopProduct[] = []
        const failed: string[] = []

        results.forEach((result, idx) => {
            if (result.status === 'fulfilled') {
                merged.push(...result.value)
            } else {
                failed.push(services[idx].name)
            }
        })

        setProducts(merged)

        const computedMax = Math.max(500, ...merged.map((p) => p.normalizedPrice))
        setMaxPrice(Math.ceil(computedMax / 100) * 100)

        if (failed.length > 0) {
            setError(`Không thể tải: ${failed.join(', ')}`)
        }

        setLoading(false)
    }

    const effectiveMaxPrice = useMemo(() => {
        if (products.length === 0) {
            return 5000
        }
        return Math.max(500, ...products.map((p) => p.normalizedPrice))
    }, [products])

    const filtered = useMemo(() => {
        const normalizedSearch = search.trim().toLowerCase()

        const byFilter = products.filter((item) => {
            if (!selectedServices.includes(item.serviceKey)) {
                return false
            }
            if (item.normalizedPrice > maxPrice) {
                return false
            }
            if (!normalizedSearch) {
                return true
            }
            return (
                item.name.toLowerCase().includes(normalizedSearch) ||
                (item.brand || '').toLowerCase().includes(normalizedSearch) ||
                item.serviceName.toLowerCase().includes(normalizedSearch)
            )
        })

        const sorted = [...byFilter]
        if (sortBy === 'price-asc') {
            sorted.sort((a, b) => a.normalizedPrice - b.normalizedPrice)
        } else if (sortBy === 'price-desc') {
            sorted.sort((a, b) => b.normalizedPrice - a.normalizedPrice)
        } else {
            sorted.sort((a, b) => b.id - a.id)
        }

        return sorted
    }, [products, selectedServices, maxPrice, search, sortBy])

    const pageSize = 8
    const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
    const currentPage = Math.min(page, totalPages)

    const pageItems = useMemo(() => {
        const start = (currentPage - 1) * pageSize
        return filtered.slice(start, start + pageSize)
    }, [filtered, currentPage])

    useEffect(() => {
        setPage(1)
    }, [search, selectedServices, sortBy, maxPrice])

    useEffect(() => {
        const q = search.trim()
        if (!customerId || q.length < 2) {
            return
        }

        const timer = window.setTimeout(() => {
            void trackInteractionEvent({
                event_type: 'search',
                query: q,
                metadata: {
                    source: 'shop_page',
                    selected_services: selectedServices,
                },
            })
        }, 500)

        return () => window.clearTimeout(timer)
    }, [customerId, search, selectedServices])

    useEffect(() => {
        if (!customerId) {
            setRealtimeRecs([])
            setLoadingRealtimeRecs(false)
            return
        }

        setLoadingRealtimeRecs(true)
        const timer = window.setTimeout(() => {
            void fetchMyRealtimeRecommendations({
                limit: 4,
            })
                .then((items) => {
                    setRealtimeRecs(items)
                })
                .finally(() => {
                    setLoadingRealtimeRecs(false)
                })
        }, 450)

        return () => window.clearTimeout(timer)
    }, [customerId, search, selectedServices, sortBy, maxPrice])

    const toggleService = (serviceKey: string) => {
        setSelectedServices((prev) => {
            if (prev.includes(serviceKey)) {
                const next = prev.filter((key) => key !== serviceKey)
                return next.length === 0 ? prev : next
            }
            return [...prev, serviceKey]
        })
    }

    const handleImageError = (name: string, serviceKey: ProductServiceKey) => (event: React.SyntheticEvent<HTMLImageElement>) => {
        const target = event.currentTarget
        target.onerror = null
        target.src = productFallbackImage(name, serviceKey)
    }

    return (
        <section className="shop-wrap">
            <header className="shop-header">
                <h1>Aeon Commerce</h1>
                <p>
                    Bộ sưu tập được tuyển chọn gồm thiết bị điện tử, thời trang tối giản và sản phẩm trang trí nhà
                    dành cho phong cách sống hiện đại.
                </p>
            </header>

            <div className="shop-content">
                <aside className="shop-sidebar">
                    <div className="filter-block">
                        <h3>Danh mục</h3>
                        <label>
                            <input
                                type="checkbox"
                                checked={selectedServices.length === services.length}
                                onChange={() => setSelectedServices(services.map((s) => s.key))}
                            />
                            <span>Tất cả bộ sưu tập</span>
                        </label>
                        {services.map((service) => (
                            <label key={service.key}>
                                <input
                                    type="checkbox"
                                    checked={selectedServices.includes(service.key)}
                                    onChange={() => toggleService(service.key)}
                                />
                                <span>{service.name}</span>
                            </label>
                        ))}
                    </div>

                    <div className="filter-block">
                        <h3>Khoảng giá</h3>
                        <input
                            type="range"
                            min={0}
                            max={Math.ceil(effectiveMaxPrice)}
                            value={Math.min(maxPrice, Math.ceil(effectiveMaxPrice))}
                            onChange={(e) => setMaxPrice(Number(e.target.value))}
                        />
                        <div className="range-labels">
                            <span>$0</span>
                            <span>{formatPrice(maxPrice)}</span>
                        </div>
                    </div>
                </aside>

                <div className="shop-grid-area">
                    <div className="shop-toolbar">
                        <div>
                            <strong>Hiển thị {filtered.length} sản phẩm</strong>
                        </div>
                        <input
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Tìm kiếm sản phẩm..."
                            className="shop-search"
                        />
                        <select value={sortBy} onChange={(e) => setSortBy(e.target.value as SortMode)}>
                            <option value="featured">Nổi bật</option>
                            <option value="price-asc">Giá: Thấp đến cao</option>
                            <option value="price-desc">Giá: Cao đến thấp</option>
                            <option value="newest">Mới nhất</option>
                        </select>
                    </div>

                    {customerId && (loadingRealtimeRecs || realtimeRecs.length > 0) && (
                        <section className="shop-realtime-panel" aria-live="polite">
                            <div className="section-head shop-realtime-head">
                                <div>
                                    <h2>Gợi ý realtime cho bạn</h2>
                                    <p className="section-note">
                                        Cập nhật liên tục theo hành vi tìm kiếm và xem sản phẩm gần nhất.
                                    </p>
                                </div>
                            </div>

                            {loadingRealtimeRecs && <p className="state-line">Đang cập nhật gợi ý realtime...</p>}

                            {!loadingRealtimeRecs && realtimeRecs.length > 0 && (
                                <div className="shop-grid shop-grid-compact">
                                    {realtimeRecs.map((item) => (
                                        <article className="shop-card" key={`${item.product_service}-${item.product_id}`}>
                                            <Link
                                                className="shop-card-media"
                                                to={`/product/${item.product_service}/${item.product_id}`}
                                                onClick={() => {
                                                    void trackInteractionEvent({
                                                        event_type: 'click',
                                                        product_service: item.product_service,
                                                        product_id: item.product_id,
                                                        metadata: { source: 'shop_page_realtime' },
                                                    })
                                                }}
                                            >
                                                <img
                                                    src={item.image_url || productFallbackImage(item.name, item.product_service as ProductServiceKey)}
                                                    alt={item.name}
                                                />
                                            </Link>
                                            <div className="shop-card-meta">
                                                <h4>{item.name}</h4>
                                                <span>{formatPrice(item.price)}</span>
                                            </div>
                                            <p>{item.reason?.[0] || 'Đề xuất phù hợp theo hành vi gần đây của bạn.'}</p>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </section>
                    )}

                    {loading && <p className="state-line">Đang tải danh mục sản phẩm...</p>}
                    {!loading && error && <p className="state-line error">{error}</p>}

                    <div className="shop-grid">
                        {pageItems.map((item) => (
                            <article className="shop-card" key={`${item.serviceKey}-${item.id}`}>
                                <Link
                                    className="shop-card-media"
                                    to={`/product/${item.serviceKey}/${item.id}`}
                                    onClick={() => {
                                        if (!customerId) {
                                            return
                                        }
                                        void trackInteractionEvent({
                                            event_type: 'click',
                                            product_service: item.serviceKey,
                                            product_id: item.id,
                                            metadata: { source: 'shop_page' },
                                        })
                                    }}
                                >
                                    <img src={productImageForService(item, serviceByKey.get(item.serviceKey))} alt={item.name} onError={handleImageError(item.name, item.serviceKey)} />
                                </Link>
                                <div className="shop-card-meta">
                                    <h4>{item.name}</h4>
                                    <span>{formatPrice(item.price)}</span>
                                </div>
                                <p>{item.description || `Sản phẩm thuộc danh mục ${item.serviceName}.`}</p>
                            </article>
                        ))}
                    </div>

                    <div className="pagination">
                        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}>
                            ‹
                        </button>
                        {Array.from({ length: totalPages }).slice(0, 5).map((_, idx) => {
                            const number = idx + 1
                            return (
                                <button
                                    key={number}
                                    className={number === currentPage ? 'active' : ''}
                                    onClick={() => setPage(number)}
                                >
                                    {number}
                                </button>
                            )
                        })}
                        <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
                            ›
                        </button>
                    </div>
                </div>
            </div>
        </section>
    )
}
