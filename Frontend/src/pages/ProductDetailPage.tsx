import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { formatPrice, productFallbackImage, productImageForService, services } from '../catalog'
import type { Product, ServiceConfig } from '../catalog'
import { authHeaders, gatewayBase, getCustomerId } from '../customerSession'
import { trackInteractionEvent } from '../ai'

type ProductWithService = Product & {
    serviceKey: string
}

type SpecItem = {
    label: string
    value: string
}

function normalizeServiceKey(serviceKey?: string): string {
    const normalized = String(serviceKey || 'book').trim().toLowerCase().replace('_', '-')
    const aliases: Record<string, string> = {
        books: 'book',
        'book-service': 'book',
        'electronics-service': 'electronics',
        'fashion-service': 'fashion',
        'toy-service': 'toy',
        'toy-service-v2': 'toy',
        'grocery-service': 'grocery',
        'furniture-service': 'furniture',
        'beauty-service': 'beauty',
        'sports-service': 'sports',
        'pet-service': 'pet',
        'stationery-service': 'stationery',
    }
    return aliases[normalized] || normalized || 'book'
}

function pickRawValue(raw: Record<string, unknown> | null, keys: string[]): string {
    if (!raw) {
        return ''
    }

    for (const key of keys) {
        const value = raw[key]
        if (typeof value === 'string' && value.trim()) {
            return value.trim()
        }
        if (typeof value === 'number' && Number.isFinite(value)) {
            return String(value)
        }
    }

    return ''
}

function inferToneFromName(name: string): string {
    const normalized = name.toLowerCase()
    if (normalized.includes('đen')) {
        return 'Đen hiện đại'
    }
    if (normalized.includes('trắng')) {
        return 'Trắng tối giản'
    }
    if (normalized.includes('xanh')) {
        return 'Xanh trẻ trung'
    }
    return 'Tông trung tính'
}

function buildSpecs(serviceKey: string, product: ProductWithService, raw: Record<string, unknown> | null): SpecItem[] {
    const authorOrBrand = product.brand || 'Đang cập nhật'

    const byService: Record<string, SpecItem[]> = {
        book: [
            { label: 'Tác giả', value: pickRawValue(raw, ['author']) || authorOrBrand },
            { label: 'Nhà xuất bản', value: pickRawValue(raw, ['publisher', 'publishing_house']) || 'NXB tổng hợp' },
            { label: 'Số trang', value: `${pickRawValue(raw, ['pages', 'page_count']) || '220'} trang` },
            { label: 'Ngôn ngữ', value: pickRawValue(raw, ['language']) || 'Tiếng Việt' },
            { label: 'Mã ISBN', value: pickRawValue(raw, ['isbn']) || product.sku || 'Đang cập nhật' },
        ],
        electronics: [
            { label: 'RAM', value: pickRawValue(raw, ['ram', 'memory']) || '8 GB' },
            { label: 'Lưu trữ', value: pickRawValue(raw, ['storage', 'rom', 'ssd']) || '256 GB SSD' },
            { label: 'Pin', value: pickRawValue(raw, ['battery', 'battery_life']) || 'Đến 10 giờ sử dụng' },
            { label: 'Kết nối', value: pickRawValue(raw, ['connectivity']) || 'Wi-Fi 6 / Bluetooth 5.2' },
            { label: 'Bảo hành', value: pickRawValue(raw, ['warranty']) || '12 tháng chính hãng' },
        ],
        fashion: [
            { label: 'Chất liệu', value: pickRawValue(raw, ['material']) || 'Cotton co giãn 2 chiều' },
            { label: 'Form dáng', value: pickRawValue(raw, ['fit', 'style']) || 'Regular fit' },
            { label: 'Màu sắc', value: pickRawValue(raw, ['color']) || inferToneFromName(product.name) },
            { label: 'Kích cỡ', value: pickRawValue(raw, ['size', 'size_range']) || 'S - M - L - XL' },
            { label: 'Bảo quản', value: pickRawValue(raw, ['care']) || 'Giặt nhẹ dưới 30°C' },
        ],
        toy: [
            { label: 'Độ tuổi phù hợp', value: pickRawValue(raw, ['age_group', 'age_range']) || '3+ tuổi' },
            { label: 'Chất liệu', value: pickRawValue(raw, ['material']) || 'Nhựa ABS an toàn' },
            { label: 'Số chi tiết', value: pickRawValue(raw, ['pieces']) || '120 chi tiết' },
            { label: 'Chứng nhận', value: pickRawValue(raw, ['safety', 'safety_certification']) || 'Đạt chuẩn an toàn trẻ em' },
            { label: 'Kỹ năng phát triển', value: pickRawValue(raw, ['skills']) || 'Tư duy logic và sáng tạo' },
        ],
        grocery: [
            { label: 'Khối lượng', value: pickRawValue(raw, ['weight', 'volume']) || '500 g' },
            { label: 'Hạn sử dụng', value: pickRawValue(raw, ['expiry', 'expiration_date']) || '12 tháng' },
            { label: 'Thành phần', value: pickRawValue(raw, ['ingredients']) || 'Thành phần tự nhiên, rõ nguồn gốc' },
            { label: 'Xuất xứ', value: pickRawValue(raw, ['origin']) || 'Việt Nam' },
            { label: 'Bảo quản', value: pickRawValue(raw, ['storage']) || 'Nơi khô ráo, thoáng mát' },
        ],
        furniture: [
            { label: 'Chất liệu', value: pickRawValue(raw, ['material']) || 'Gỗ công nghiệp phủ chống ẩm' },
            { label: 'Kích thước', value: pickRawValue(raw, ['dimensions']) || '120 x 60 x 75 cm' },
            { label: 'Tải trọng', value: pickRawValue(raw, ['load_capacity']) || '80 kg' },
            { label: 'Màu hoàn thiện', value: pickRawValue(raw, ['color']) || inferToneFromName(product.name) },
            { label: 'Lắp đặt', value: pickRawValue(raw, ['assembly']) || 'Dễ lắp ráp trong 20 phút' },
        ],
        beauty: [
            { label: 'Loại da phù hợp', value: pickRawValue(raw, ['skin_type']) || 'Mọi loại da' },
            { label: 'Dung tích', value: pickRawValue(raw, ['volume', 'weight']) || '50 ml' },
            { label: 'Hoạt chất chính', value: pickRawValue(raw, ['active_ingredients', 'ingredients']) || 'Niacinamide + Hyaluronic Acid' },
            { label: 'Cách dùng', value: pickRawValue(raw, ['usage']) || 'Sử dụng sáng và tối sau toner' },
            { label: 'Hạn dùng', value: pickRawValue(raw, ['expiry']) || '24 tháng từ NSX' },
        ],
        sports: [
            { label: 'Môn phù hợp', value: pickRawValue(raw, ['sport_type']) || 'Gym / Cardio' },
            { label: 'Chất liệu', value: pickRawValue(raw, ['material']) || 'Polyester thoáng khí' },
            { label: 'Trọng lượng', value: pickRawValue(raw, ['weight']) || 'Nhẹ, dễ mang theo' },
            { label: 'Cấp độ', value: pickRawValue(raw, ['level']) || 'Người mới đến trung cấp' },
            { label: 'Bảo hành', value: pickRawValue(raw, ['warranty']) || '6 tháng' },
        ],
        pet: [
            { label: 'Đối tượng', value: pickRawValue(raw, ['pet_type']) || 'Chó và mèo' },
            { label: 'Độ tuổi', value: pickRawValue(raw, ['age_range']) || 'Trên 6 tháng tuổi' },
            { label: 'Hương vị/Chất liệu', value: pickRawValue(raw, ['flavor', 'material']) || 'Dễ tiếp nhận, thân thiện thú cưng' },
            { label: 'Khối lượng', value: pickRawValue(raw, ['weight']) || '1 kg' },
            { label: 'Dinh dưỡng', value: pickRawValue(raw, ['nutrition']) || 'Cân bằng vitamin và khoáng chất' },
        ],
        stationery: [
            { label: 'Kích thước', value: pickRawValue(raw, ['paper_size', 'size']) || 'A5' },
            { label: 'Số trang', value: `${pickRawValue(raw, ['page_count', 'pages']) || '120'} trang` },
            { label: 'Định lượng giấy', value: pickRawValue(raw, ['grammage']) || '80 gsm' },
            { label: 'Loại mực phù hợp', value: pickRawValue(raw, ['ink_type']) || 'Gel / Bi nước' },
            { label: 'Ứng dụng', value: pickRawValue(raw, ['usage']) || 'Ghi chú học tập và công việc' },
        ],
    }

    return byService[serviceKey] || [
        { label: 'Thương hiệu', value: authorOrBrand },
        { label: 'SKU', value: product.sku || 'Đang cập nhật' },
        { label: 'Danh mục', value: serviceKey },
        { label: 'Tình trạng', value: (product.stock ?? product.stock_quantity ?? 0) > 0 ? 'Còn hàng' : 'Tạm hết hàng' },
    ]
}

function buildHighlights(serviceKey: string, product: ProductWithService): string[] {
    const byService: Record<string, string[]> = {
        book: [
            'Nội dung dễ tiếp cận, phù hợp đọc nhanh mỗi ngày.',
            'Bản in rõ nét, trình bày mạch lạc.',
            'Phù hợp làm quà tặng tri thức và phát triển bản thân.',
        ],
        electronics: [
            'Tối ưu hiệu năng cho học tập và làm việc đa nhiệm.',
            'Thiết kế hiện đại, dễ phối hợp với góc làm việc.',
            'Độ bền cao, vận hành ổn định trong thời gian dài.',
        ],
        fashion: [
            'Form dáng tôn dáng, dễ phối nhiều phong cách.',
            'Chất vải thoáng và êm, phù hợp dùng hằng ngày.',
            `Tông màu ${inferToneFromName(product.name).toLowerCase()} giúp outfit cân bằng.`,
        ],
        toy: [
            'Khuyến khích trẻ phát triển tư duy logic qua trải nghiệm chơi.',
            'Thiết kế bo góc an toàn, thân thiện với trẻ nhỏ.',
            'Có thể chơi cùng gia đình để tăng tương tác.',
        ],
        grocery: [
            'Dễ sử dụng trong bữa ăn hằng ngày.',
            'Nguồn gốc rõ ràng, thuận tiện tích trữ.',
            'Phù hợp cho cả gia đình và nhu cầu nấu nướng linh hoạt.',
        ],
        furniture: [
            'Thiết kế tinh gọn, tối ưu diện tích không gian sống.',
            'Bề mặt hoàn thiện dễ lau chùi, dễ bảo quản.',
            'Tông màu hiện đại giúp đồng bộ nội thất.',
        ],
        beauty: [
            'Kết cấu nhẹ, dễ thẩm thấu và dùng hằng ngày.',
            'Phù hợp routine chăm sóc da cơ bản đến nâng cao.',
            'Hiệu quả ổn định khi duy trì đúng tần suất.',
        ],
        sports: [
            'Thiết kế hỗ trợ chuyển động linh hoạt và thoải mái.',
            'Phù hợp cho luyện tập tại nhà hoặc phòng gym.',
            'Dễ kết hợp trong lịch tập cường độ vừa và cao.',
        ],
        pet: [
            'Thân thiện với thú cưng, dễ làm quen khi sử dụng.',
            'Hỗ trợ duy trì sức khỏe và thói quen tích cực.',
            'Phù hợp cho chăm sóc hằng ngày tại nhà.',
        ],
        stationery: [
            'Bề mặt giấy ổn định, hạn chế lem mực khi ghi nhanh.',
            'Phù hợp ghi chép học tập, họp và lên kế hoạch.',
            'Thiết kế tối giản, gọn nhẹ khi mang theo.',
        ],
    }

    return byService[serviceKey] || [
        'Thiết kế thực dụng, dễ dùng cho nhu cầu hằng ngày.',
        'Mức giá cân đối so với giá trị sử dụng.',
        'Phù hợp nhiều bối cảnh sử dụng khác nhau.',
    ]
}

export function ProductDetailPage() {
    const { serviceKey, productId } = useParams()
    const normalizedServiceKey = normalizeServiceKey(serviceKey)
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [product, setProduct] = useState<ProductWithService | null>(null)
    const [rawDetail, setRawDetail] = useState<Record<string, unknown> | null>(null)
    const [related, setRelated] = useState<ProductWithService[]>([])
    const [quantity, setQuantity] = useState(1)
    const [adding, setAdding] = useState(false)
    const [info, setInfo] = useState('')

    const service = useMemo<ServiceConfig | undefined>(
        () => services.find((s) => s.key === normalizedServiceKey),
        [normalizedServiceKey],
    )

    useEffect(() => {
        void loadDetail()
    }, [serviceKey, productId])

    useEffect(() => {
        const customerId = getCustomerId()
        if (!customerId || !product) {
            return
        }

        void trackInteractionEvent({
            event_type: 'view',
            product_service: normalizedServiceKey,
            product_id: product.id,
            metadata: { source: 'product_detail_page' },
        })
    }, [normalizedServiceKey, product])

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

            const detailEndpoint = normalizedServiceKey === 'book'
                ? `${gatewayBase}/api/books/${productId}/`
                : `${gatewayBase}/api/products/${normalizedServiceKey}/${productId}/`
            const listEndpoint = normalizedServiceKey === 'book'
                ? `${gatewayBase}/api/books/`
                : `${gatewayBase}/api/products/${normalizedServiceKey}/`

            const listResp = await fetch(listEndpoint, {
                credentials: 'include',
            })
            const listJson = listResp.ok ? ((await listResp.json()) as Array<Record<string, unknown>>) : []
            const rows = (Array.isArray(listJson) ? listJson : []).map((item) => normalizeProduct(item))

            const detailResp = await fetch(detailEndpoint, {
                credentials: 'include',
            })
            let detailJson: Product
            if (detailResp.ok) {
                const detailRaw = (await detailResp.json()) as Record<string, unknown>
                setRawDetail(detailRaw)
                detailJson = normalizeProduct(detailRaw)
            } else {
                const fallback = rows.find((item) => String(item.id) === String(productId)) || rows[0]
                if (!fallback) {
                    throw new Error(`Không tải được sản phẩm (${detailResp.status})`)
                }
                setRawDetail(null)
                detailJson = fallback
            }

            const detail = { ...detailJson, serviceKey: normalizedServiceKey }
            setProduct(detail)
            setRelated(
                rows
                    .filter((item) => item.id !== detail.id)
                    .slice(0, 4)
                    .map((item) => ({ ...item, serviceKey: normalizedServiceKey })),
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
                    product_service: normalizedServiceKey,
                    product_id: product.id,
                    ...(normalizedServiceKey === 'book' ? { book_id: product.id } : {}),
                    quantity,
                }),
            })

            if (!response.ok) {
                const json = (await response.json()) as { error?: string }
                throw new Error(json.error || 'Không thêm được vào giỏ hàng.')
            }

            await trackInteractionEvent({
                event_type: 'cart',
                product_service: normalizedServiceKey,
                product_id: product.id,
                metadata: { quantity },
            })
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
    const specs = buildSpecs(normalizedServiceKey, product, rawDetail)
    const highlights = buildHighlights(normalizedServiceKey, product)

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
                </div>

                <aside className="product-detail-info">
                    <p className="edition">Premium Edition</p>
                    <h1>{product.name}</h1>
                    <p className="price">{formatPrice(product.price)}</p>
                    <p className="desc">{product.description || `Sản phẩm thuộc danh mục ${service?.name || 'Sản phẩm'} với thiết kế tối giản.`}</p>

                    <div className="product-specs">
                        <h3>Đặc tả theo danh mục</h3>
                        <div className="product-spec-grid">
                            {specs.map((item) => (
                                <article className="product-spec-item" key={item.label}>
                                    <span>{item.label}</span>
                                    <strong>{item.value}</strong>
                                </article>
                            ))}
                        </div>
                    </div>

                    <div className="product-feature-wrap">
                        <h3>Đặc điểm nổi bật</h3>
                        <ul className="product-feature-list">
                            {highlights.map((text, idx) => (
                                <li key={`${product.id}-${idx}`}>{text}</li>
                            ))}
                        </ul>
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
