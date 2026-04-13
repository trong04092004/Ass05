import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import type { AuthPayload } from '../backofficeAuth'
import { saveCustomerSession } from '../customerSession'

type UserAuthPageProps = {
    mode: 'login' | 'register'
}

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const gatewayBase = `http://${runtimeHost}:18000`

export function UserAuthPage({ mode }: UserAuthPageProps) {
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
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
        }

        const endpoint = isRegister ? '/api/auth/register/' : '/api/auth/login/'

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

            saveCustomerSession(data)
            navigate('/shop')
        } catch {
            setError('Không thể kết nối hệ thống xác thực.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="auth-shell auth-shell-user">
            <section className="auth-showcase" aria-hidden="true">
                <img
                    src="https://images.unsplash.com/photo-1519710164239-da123dc03ef4?auto=format&fit=crop&w=1800&q=80"
                    alt="Lifestyle"
                />
                <div className="auth-showcase-overlay" />
                <div className="auth-showcase-content">
                    <h1>Aeon Commerce</h1>
                    <div>
                        <p>
                            Không gian mua sắm
                            <br />
                            cho người dùng
                        </p>
                        <span>Đăng nhập để theo dõi đơn hàng, giỏ hàng và khám phá bộ sưu tập tinh tuyển mới nhất.</span>
                    </div>
                    <div className="auth-showcase-stats">
                        <div>
                            <strong>24h</strong>
                            <small>Hỗ trợ đơn hàng</small>
                        </div>
                        <div>
                            <strong>10+</strong>
                            <small>Nhóm ngành hàng</small>
                        </div>
                    </div>
                </div>
            </section>

            <section className="auth-form-pane">
                <div className="auth-form-wrap">
                    <header>
                        <h2>{isRegister ? 'Tạo tài khoản người dùng' : 'Đăng nhập người dùng'}</h2>
                        <p>Trang riêng cho khách hàng mua sắm trên hệ thống Aeon Commerce.</p>
                    </header>

                    <div className="auth-divider auth-divider-top">
                        <span>{isRegister ? 'đăng ký bằng email' : 'đăng nhập bằng email'}</span>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {isRegister && (
                            <label>
                                <span>Họ và tên</span>
                                <input
                                    required
                                    value={name}
                                    onChange={(event) => setName(event.target.value)}
                                    placeholder="Nguyễn Văn A"
                                    type="text"
                                />
                            </label>
                        )}

                        <label>
                            <span>Email</span>
                            <input
                                required
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="ban@email.com"
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

                        {error && <p className="auth-error">{error}</p>}

                        <button className="auth-submit" disabled={loading} type="submit">
                            {loading ? 'Đang xử lý...' : isRegister ? 'Đăng ký người dùng' : 'Đăng nhập người dùng'}
                            <span className="material-symbols-outlined">arrow_forward</span>
                        </button>
                    </form>

                    <footer className="auth-footer-link">
                        {isRegister ? (
                            <p>
                                Đã có tài khoản?
                                <Link to="/auth/login"> Đăng nhập</Link>
                            </p>
                        ) : (
                            <p>
                                Chưa có tài khoản?
                                <Link to="/auth/register"> Đăng ký</Link>
                            </p>
                        )}
                        <p className="auth-secondary-link">
                            Staff / Manager?
                            <Link to="/admin/login"> Chuyển sang cổng nội bộ</Link>
                        </p>
                    </footer>
                </div>
            </section>
        </main>
    )
}
