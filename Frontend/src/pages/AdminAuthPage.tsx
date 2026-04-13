import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { AuthPayload } from '../backofficeAuth'
import { saveBackofficeSession } from '../backofficeAuth'

type AdminAuthPageProps = {
    mode: 'login' | 'register'
}

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const gatewayHost = runtimeHost === 'localhost' ? '127.0.0.1' : runtimeHost
const gatewayBase = `http://${gatewayHost}:18000`

export function AdminAuthPage({ mode }: AdminAuthPageProps) {
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [role, setRole] = useState<'staff' | 'manager'>('staff')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const isRegister = mode === 'register'

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setLoading(true)
        setError('')

        const payload: Record<string, string> = {
            email: email.trim(),
            password,
        }

        if (isRegister) {
            payload.name = name.trim()
            payload.role = role
        }

        const endpoint = isRegister ? '/api/auth/admin/register/' : '/api/auth/admin/login/'

        try {
            const response = await fetch(`${gatewayBase}${endpoint}`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            const data = (await response.json()) as AuthPayload
            if (!response.ok) {
                setError(data.error || 'Đăng nhập thất bại. Vui lòng thử lại.')
                return
            }

            saveBackofficeSession(data)

            if (data.role === 'manager') {
                navigate('/manager/dashboard')
                return
            }

            navigate('/staff/dashboard')
        } catch {
            setError('Không thể kết nối hệ thống xác thực.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="auth-shell auth-shell-admin">
            <section className="auth-showcase" aria-hidden="true">
                <img
                    src="https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1800&q=80"
                    alt="Operations center"
                />
                <div className="auth-showcase-overlay" />
                <div className="auth-showcase-content">
                    <h1>Aeon Control Room</h1>
                    <div>
                        <p>
                            Cổng vận hành
                            <br />
                            Staff & Manager
                        </p>
                        <span>Giao diện riêng cho đội ngũ nội bộ xử lý nhân sự, khuyến mãi và phiếu nhập kho.</span>
                    </div>
                    <div className="auth-showcase-stats">
                        <div>
                            <strong>02</strong>
                            <small>Dashboard tách biệt</small>
                        </div>
                        <div>
                            <strong>100%</strong>
                            <small>Role-based Access</small>
                        </div>
                    </div>
                </div>
            </section>

            <section className="auth-form-pane">
                <div className="auth-form-wrap">
                    <header>
                        <h2>{isRegister ? 'Đăng ký tài khoản nội bộ' : 'Đăng nhập cổng nội bộ'}</h2>
                        <p>Trang riêng cho nhân viên và quản lý. Tài khoản customer không đăng nhập tại đây.</p>
                    </header>

                    <div className="auth-divider auth-divider-top">
                        <span>{isRegister ? 'tạo tài khoản nội bộ' : 'xác thực nội bộ'}</span>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {isRegister && (
                            <label>
                                <span>Họ và tên</span>
                                <input
                                    required
                                    value={name}
                                    onChange={(event) => setName(event.target.value)}
                                    placeholder="Nhân sự nội bộ"
                                    type="text"
                                />
                            </label>
                        )}

                        <label>
                            <span>Email nội bộ</span>
                            <input
                                required
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="staff@aeon.local"
                                type="email"
                            />
                        </label>

                        <label>
                            <span>Mật khẩu</span>
                            <input
                                required
                                minLength={6}
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="••••••••"
                                type="password"
                            />
                        </label>

                        {isRegister && (
                            <label>
                                <span>Vai trò</span>
                                <select value={role} onChange={(event) => setRole(event.target.value as 'staff' | 'manager')}>
                                    <option value="staff">Staff</option>
                                    <option value="manager">Manager</option>
                                </select>
                            </label>
                        )}

                        {error && <p className="auth-error">{error}</p>}

                        <button className="auth-submit" disabled={loading} type="submit">
                            {loading ? 'Đang xử lý...' : isRegister ? 'Đăng ký nội bộ' : 'Đăng nhập nội bộ'}
                            <span className="material-symbols-outlined">arrow_forward</span>
                        </button>
                    </form>

                    <footer className="auth-footer-link">
                        {isRegister ? (
                            <p>
                                Đã có tài khoản?
                                <Link to="/admin/login"> Đăng nhập</Link>
                            </p>
                        ) : (
                            <p>
                                Chưa có tài khoản?
                                <Link to="/admin/register"> Đăng ký</Link>
                            </p>
                        )}
                        <p className="auth-secondary-link">
                            Người dùng mua sắm?
                            <Link to="/auth/login"> Chuyển sang cổng người dùng</Link>
                        </p>
                    </footer>
                </div>
            </section>
        </main>
    )
}
