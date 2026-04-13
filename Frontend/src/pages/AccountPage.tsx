import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../catalog'
import { authHeaders, gatewayBase, getCustomerId } from '../customerSession'

type Customer = {
    id: number
    name: string
    email: string
    phone?: string
    role?: string
}

type Address = {
    id: number
    label: string
    street: string
    district?: string
    city?: string
    is_default?: boolean
}

type Order = {
    id: number
    status: string
    total_amount: string | number
    created_at?: string
}

export function AccountPage() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [success, setSuccess] = useState('')
    const [customer, setCustomer] = useState<Customer | null>(null)
    const [addresses, setAddresses] = useState<Address[]>([])
    const [orders, setOrders] = useState<Order[]>([])

    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [phone, setPhone] = useState('')

    const [label, setLabel] = useState('Nhà')
    const [street, setStreet] = useState('')
    const [district, setDistrict] = useState('')
    const [city, setCity] = useState('TP. Hồ Chí Minh')
    const [isDefault, setIsDefault] = useState(false)

    const customerId = getCustomerId()

    useEffect(() => {
        if (!customerId) {
            navigate('/auth/login')
            return
        }
        void loadData(customerId)
    }, [customerId])

    const loadData = async (cid: number) => {
        setLoading(true)
        setError('')
        try {
            const [customerResp, addressResp, orderResp] = await Promise.all([
                fetch(`${gatewayBase}/api/customers/${cid}/`, { credentials: 'include', headers: authHeaders(false) }),
                fetch(`${gatewayBase}/api/customers/${cid}/addresses/`, { credentials: 'include', headers: authHeaders(false) }),
                fetch(`${gatewayBase}/api/orders/customer/${cid}/`, { credentials: 'include', headers: authHeaders(false) }),
            ])

            if (!customerResp.ok) {
                throw new Error('Không tải được hồ sơ người dùng.')
            }

            const customerJson = (await customerResp.json()) as Customer
            setCustomer(customerJson)
            setName(customerJson.name || '')
            setEmail(customerJson.email || '')
            setPhone(customerJson.phone || '')

            const addressJson = (addressResp.ok ? ((await addressResp.json()) as Address[]) : []) || []
            setAddresses(addressJson)

            const orderJson = (orderResp.ok ? ((await orderResp.json()) as Order[]) : []) || []
            setOrders(orderJson)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Lỗi tải dữ liệu tài khoản.')
        } finally {
            setLoading(false)
        }
    }

    const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!customerId) {
            return
        }

        setSuccess('')
        setError('')
        const response = await fetch(`${gatewayBase}/api/customers/${customerId}/`, {
            method: 'PUT',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify({ name, email, phone }),
        })

        if (!response.ok) {
            setError('Không cập nhật được hồ sơ.')
            return
        }

        setSuccess('Cập nhật hồ sơ thành công.')
        await loadData(customerId)
    }

    const addAddress = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!customerId) {
            return
        }

        setSuccess('')
        setError('')
        const response = await fetch(`${gatewayBase}/api/customers/${customerId}/addresses/`, {
            method: 'POST',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify({
                customer: customerId,
                label,
                street,
                district,
                city,
                is_default: isDefault,
            }),
        })

        if (!response.ok) {
            setError('Không thêm được địa chỉ mới.')
            return
        }

        setLabel('Nhà')
        setStreet('')
        setDistrict('')
        setCity('TP. Hồ Chí Minh')
        setIsDefault(false)
        setSuccess('Đã thêm địa chỉ mới.')
        await loadData(customerId)
    }

    return (
        <section className="account-page">
            <div className="section-head">
                <div>
                    <h2>Tài khoản cá nhân</h2>
                    <p className="section-note">Quản lý hồ sơ, địa chỉ và lịch sử đơn hàng.</p>
                </div>
                <Link className="catalog-link" to="/shop">Về Shop</Link>
            </div>

            {loading && <p className="state-line">Đang tải tài khoản...</p>}
            {error && <p className="state-line error">{error}</p>}
            {success && <p className="state-line">{success}</p>}

            <div className="account-grid">
                <article className="ops-card">
                    <h3>Thông tin cơ bản</h3>
                    <form className="ops-form" onSubmit={saveProfile}>
                        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Họ tên" required />
                        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" type="email" required />
                        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Số điện thoại" />
                        <button type="submit">Lưu hồ sơ</button>
                    </form>
                    {customer && <p className="section-note">Mã khách hàng: {customer.id}</p>}
                </article>

                <article className="ops-table-card account-orders">
                    <div className="ops-table-head">
                        <h3>Đơn hàng gần đây</h3>
                        <span>{orders.length} đơn</span>
                    </div>
                    <div className="ops-table-wrap">
                        <table className="ops-table">
                            <thead>
                                <tr>
                                    <th>Mã đơn</th>
                                    <th>Ngày tạo</th>
                                    <th>Trạng thái</th>
                                    <th>Tổng tiền</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map((order) => (
                                    <tr key={order.id}>
                                        <td>#{order.id}</td>
                                        <td>{order.created_at ? new Date(order.created_at).toLocaleString('vi-VN') : '-'}</td>
                                        <td>{order.status}</td>
                                        <td>{formatPrice(order.total_amount)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </article>

                <article className="ops-card">
                    <h3>Thêm địa chỉ mới</h3>
                    <form className="ops-form" onSubmit={addAddress}>
                        <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Nhãn địa chỉ" required />
                        <input value={street} onChange={(e) => setStreet(e.target.value)} placeholder="Số nhà, đường" required />
                        <input value={district} onChange={(e) => setDistrict(e.target.value)} placeholder="Quận/Huyện" />
                        <input value={city} onChange={(e) => setCity(e.target.value)} placeholder="Tỉnh/Thành" />
                        <label className="ops-checkbox">
                            <input checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} type="checkbox" />
                            <span>Đặt làm mặc định</span>
                        </label>
                        <button type="submit">Lưu địa chỉ</button>
                    </form>
                </article>

                <article className="ops-table-card">
                    <div className="ops-table-head">
                        <h3>Danh sách địa chỉ</h3>
                        <span>{addresses.length} địa chỉ</span>
                    </div>
                    <div className="address-list">
                        {addresses.map((address) => (
                            <div className="address-item" key={address.id}>
                                <strong>{address.label}</strong>
                                <p>{address.street}</p>
                                <p>{address.district || ''} {address.city || ''}</p>
                                {address.is_default && <span>Mặc định</span>}
                            </div>
                        ))}
                    </div>
                </article>
            </div>
        </section>
    )
}
