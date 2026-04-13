import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../catalog'
import { authHeaders, clearCustomerSession, gatewayBase, getCustomerId } from '../customerSession'

type CartItem = {
    id: number
    cart: number
    book_id?: number
    product_id?: number
    product_service?: string
    quantity: number
}

type ProductLike = {
    id: number
    title?: string
    name?: string
    brand?: string
    price?: string | number
    image_url?: string
}

type Address = {
    id: number
    label: string
    street: string
    district?: string
    city?: string
    is_default?: boolean
}

type EnrichedCartItem = CartItem & {
    serviceKey: string
    productId: number
    title: string
    unitPrice: number
    imageUrl: string
}

export function CheckoutPage() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [items, setItems] = useState<EnrichedCartItem[]>([])
    const [addresses, setAddresses] = useState<Address[]>([])
    const [selectedAddress, setSelectedAddress] = useState('')
    const [phone, setPhone] = useState('')
    const [paymentMethod, setPaymentMethod] = useState('cod')
    const [shippingMethod, setShippingMethod] = useState('standard')
    const [placing, setPlacing] = useState(false)
    const [warning, setWarning] = useState('')

    const customerId = getCustomerId()

    useEffect(() => {
        if (!customerId) {
            navigate('/auth/login')
            return
        }
        void loadCheckoutData(customerId)
    }, [customerId])

    const handleUnauthorized = () => {
        clearCustomerSession()
        setError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.')
        navigate('/auth/login')
    }

    const loadCheckoutData = async (cid: number, pruneInvalid = true, resetWarning = true) => {
        setLoading(true)
        setError('')
        if (resetWarning) {
            setWarning('')
        }
        try {
            const [cartResp, addressResp, customerResp] = await Promise.all([
                fetch(`${gatewayBase}/api/cart/${cid}/`, { credentials: 'include', headers: authHeaders(false) }),
                fetch(`${gatewayBase}/api/customers/${cid}/addresses/`, { credentials: 'include', headers: authHeaders(false) }),
                fetch(`${gatewayBase}/api/customers/${cid}/`, { credentials: 'include', headers: authHeaders(false) }),
            ])

            if (cartResp.status === 401 || addressResp.status === 401 || customerResp.status === 401) {
                handleUnauthorized()
                return
            }

            if (!cartResp.ok) {
                throw new Error('Không tải được giỏ hàng.')
            }

            const rawCart = (await cartResp.json()) as CartItem[]
            const cartRows = Array.isArray(rawCart) ? rawCart : []

            const detailed = await Promise.all(
                cartRows.map(async (item) => {
                    const serviceKey = (item.product_service || (item.book_id ? 'book' : '')).toLowerCase()
                    const productId = item.product_id || item.book_id || 0

                    if (!serviceKey || !productId) {
                        return {
                            ...item,
                            title: `Sản phẩm #${item.id}`,
                            serviceKey: 'unknown',
                            productId: item.id,
                            unitPrice: 0,
                            imageUrl: '',
                            invalid: true,
                        }
                    }

                    const endpoint = serviceKey === 'book'
                        ? `${gatewayBase}/api/books/${productId}/`
                        : `${gatewayBase}/api/products/${serviceKey}/${productId}/`

                    const productResp = await fetch(endpoint, {
                        credentials: 'include',
                    })
                    if (!productResp.ok) {
                        return {
                            ...item,
                            title: `Sản phẩm #${serviceKey}-${productId}`,
                            serviceKey,
                            productId,
                            unitPrice: 0,
                            imageUrl: '',
                            invalid: true,
                        }
                    }
                    const product = (await productResp.json()) as ProductLike
                    const title = product.title || product.name || `Sản phẩm #${serviceKey}-${productId}`
                    const unitPrice = Number.parseFloat(String(product.price || 0)) || 0
                    return {
                        ...item,
                        serviceKey,
                        productId,
                        title,
                        unitPrice,
                        imageUrl: product.image_url || '',
                        invalid: false,
                    }
                }),
            )

            const invalidRows = detailed.filter((item) => item.invalid)
            if (invalidRows.length > 0 && pruneInvalid) {
                await Promise.all(
                    invalidRows.map((item) =>
                        fetch(`${gatewayBase}/api/cart-items/${item.id}/`, {
                            method: 'DELETE',
                            credentials: 'include',
                            headers: authHeaders(false),
                        }),
                    ),
                )
                setWarning(`Đã tự xóa ${invalidRows.length} sản phẩm giỏ hàng không còn hợp lệ.`)
                await loadCheckoutData(cid, false, false)
                return
            }

            setItems(detailed.filter((item) => !item.invalid))

            const addrRows = (addressResp.ok ? ((await addressResp.json()) as Address[]) : []) || []
            setAddresses(addrRows)
            const defaultAddr = addrRows.find((a) => a.is_default) || addrRows[0]
            setSelectedAddress(defaultAddr ? String(defaultAddr.id) : '')

            if (customerResp.ok) {
                const customerJson = (await customerResp.json()) as { phone?: string }
                setPhone(customerJson.phone || '')
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Không tải được dữ liệu thanh toán.'
            setError(message)
        } finally {
            setLoading(false)
        }
    }

    const subtotal = useMemo(() => items.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0), [items])
    const shippingFee = shippingMethod === 'express' ? 25000 : 0
    const tax = subtotal * 0.08
    const total = subtotal + shippingFee + tax

    const selectedAddressText = useMemo(() => {
        const found = addresses.find((a) => String(a.id) === selectedAddress)
        if (!found) {
            return ''
        }
        const district = found.district || ''
        const city = found.city || ''
        return `${found.street}, ${district}, ${city}`.replace(/,\s+,/g, ',').replace(/,\s*$/, '')
    }, [addresses, selectedAddress])

    const paymentOptions = [
        { key: 'cod', label: 'COD', detail: 'Thanh toan khi nhan hang' },
        { key: 'bank', label: 'Bank Transfer', detail: 'Chuyen khoan ngan hang' },
        { key: 'card', label: 'Credit Card', detail: 'The Visa/Mastercard/JCB' },
    ] as const

    const updateQty = async (itemId: number, qty: number) => {
        if (!customerId) {
            return
        }
        const response = await fetch(`${gatewayBase}/api/cart-items/${itemId}/`, {
            method: 'PATCH',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify({ quantity: qty }),
        })
        if (response.status === 401) {
            handleUnauthorized()
            return
        }
        if (!response.ok) {
            setError('Không thể cập nhật số lượng.')
            return
        }
        await loadCheckoutData(customerId)
    }

    const removeItem = async (itemId: number) => {
        if (!customerId) {
            return
        }
        const response = await fetch(`${gatewayBase}/api/cart-items/${itemId}/`, {
            method: 'DELETE',
            credentials: 'include',
            headers: authHeaders(false),
        })
        if (response.status === 401) {
            handleUnauthorized()
            return
        }
        if (!response.ok && response.status !== 204) {
            setError('Không thể xóa sản phẩm.')
            return
        }
        await loadCheckoutData(customerId)
    }

    const placeOrder = async () => {
        if (!customerId) {
            navigate('/auth/login')
            return
        }
        if (items.length === 0) {
            setError('Giỏ hàng trống.')
            return
        }
        if (items.some((item) => item.unitPrice <= 0)) {
            setError('Giỏ hàng có sản phẩm chưa hợp lệ. Vui lòng làm mới và kiểm tra lại.')
            return
        }
        if (!selectedAddressText) {
            setError('Vui lòng chọn địa chỉ giao hàng.')
            return
        }

        setPlacing(true)
        setError('')
        try {
            const response = await fetch(`${gatewayBase}/api/orders/`, {
                method: 'POST',
                credentials: 'include',
                headers: authHeaders(),
                body: JSON.stringify({
                    customer_id: customerId,
                    payment_method: paymentMethod,
                    shipping_method: shippingMethod,
                    address: selectedAddressText,
                    phone,
                }),
            })

            if (response.status === 401) {
                handleUnauthorized()
                return
            }

            if (!response.ok) {
                const json = (await response.json()) as { error?: string }
                throw new Error(json.error || 'Đặt hàng thất bại.')
            }

            navigate('/account')
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Đặt hàng thất bại.')
        } finally {
            setPlacing(false)
        }
    }

    return (
        <section className="checkout-page">
            <div className="section-head">
                <div>
                    <h2>Review Your Order</h2>
                    <p className="section-note">Xác nhận sản phẩm và hoàn tất thanh toán.</p>
                </div>
                <Link className="catalog-link" to="/shop">Tiếp tục mua sắm</Link>
            </div>

            {loading && <p className="state-line">Đang tải giỏ hàng...</p>}
            {error && <p className="state-line error">{error}</p>}
            {warning && <p className="state-line">{warning}</p>}

            <div className="checkout-grid">
                <div>
                    <div className="checkout-items">
                        {!loading && items.length === 0 && (
                            <article className="checkout-item-card">
                                <div>
                                    <h4>Giỏ hàng đang trống</h4>
                                    <p>Hãy thêm sản phẩm để tiếp tục thanh toán.</p>
                                </div>
                            </article>
                        )}
                        {items.map((item) => (
                            <article key={item.id} className="checkout-item-card">
                                <div className="checkout-item-image">
                                    {item.imageUrl ? <img src={item.imageUrl} alt={item.title} /> : <div />}
                                </div>
                                <div>
                                    <h4>{item.title}</h4>
                                    <p>{formatPrice(item.unitPrice)}</p>
                                    <div className="qty-row compact">
                                        <button type="button" onClick={() => void updateQty(item.id, Math.max(1, item.quantity - 1))}>-</button>
                                        <span>{item.quantity}</span>
                                        <button type="button" onClick={() => void updateQty(item.id, item.quantity + 1)}>+</button>
                                    </div>
                                </div>
                                <button className="link-danger" type="button" onClick={() => void removeItem(item.id)}>Xóa</button>
                            </article>
                        ))}
                    </div>

                    <div className="checkout-methods">
                        <h3>Shipping Method</h3>
                        <div className="checkout-method-grid">
                            {[
                                { key: 'standard', label: 'Standard', price: 'Miễn phí' },
                                { key: 'express', label: 'Express', price: '25.000 đ' },
                            ].map((method) => (
                                <button
                                    key={method.key}
                                    type="button"
                                    className={shippingMethod === method.key ? 'active' : ''}
                                    onClick={() => setShippingMethod(method.key)}
                                >
                                    <strong>{method.label}</strong>
                                    <span>{method.price}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                <aside className="checkout-side">
                    <h3>Shipping Address</h3>
                    <select value={selectedAddress} onChange={(e) => setSelectedAddress(e.target.value)}>
                        <option value="">Chọn địa chỉ</option>
                        {addresses.map((address) => (
                            <option value={address.id} key={address.id}>
                                {address.label} - {address.street}
                            </option>
                        ))}
                    </select>
                    <input
                        className="checkout-phone-input"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="Số điện thoại"
                        type="tel"
                    />

                    <h3>Payment Method</h3>
                    <div className="checkout-radio-list">
                        {paymentOptions.map((option) => {
                            const id = `payment-${option.key}`
                            const active = paymentMethod === option.key
                            return (
                                <label key={option.key} htmlFor={id} className={`checkout-payment-option${active ? ' active' : ''}`}>
                                    <input
                                        id={id}
                                        name="payment_method"
                                        type="radio"
                                        checked={active}
                                        onChange={() => setPaymentMethod(option.key)}
                                    />
                                    <span className="checkout-payment-copy">
                                        <strong>{option.label}</strong>
                                        <small>{option.detail}</small>
                                    </span>
                                </label>
                            )
                        })}
                    </div>

                    <div className="checkout-summary">
                        <div><span>Subtotal</span><strong>{formatPrice(subtotal)}</strong></div>
                        <div><span>Shipping</span><strong>{formatPrice(shippingFee)}</strong></div>
                        <div><span>Tax</span><strong>{formatPrice(tax)}</strong></div>
                        <div className="total"><span>Total</span><strong>{formatPrice(total)}</strong></div>
                    </div>

                    <button className="primary-btn btn-wide" type="button" onClick={() => void placeOrder()} disabled={placing}>
                        {placing ? 'Đang xử lý...' : 'Complete Purchase'}
                    </button>
                </aside>
            </div>
        </section>
    )
}
