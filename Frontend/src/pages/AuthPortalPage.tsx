import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { gatewayBase } from '../customerSession'

type AuthScope = 'customer' | 'admin'
type AuthMode = 'login' | 'register'

type AuthPortalPageProps = {
    scope: AuthScope
    mode: AuthMode
}

type AuthPayload = {
    customer_id?: number
    name?: string
    email?: string
    role?: string
    token?: string
    access?: string
    refresh?: string
    error?: string
}

export function AuthPortalPage({ scope, mode }: AuthPortalPageProps) {
    const navigate = useNavigate()
    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [role, setRole] = useState<'staff' | 'manager'>('staff')
    const [remember, setRemember] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const isRegister = mode === 'register'
    const isAdminScope = scope === 'admin'

    const title = isRegister ? 'Create Account' : 'Welcome Back'
    const subtitle = isAdminScope
        ? 'Cổng xác thực dành riêng cho staff và manager.'
        : 'Please enter your details to access your account.'

    const endpoint = getEndpoint(scope, mode)

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        setError('')
        setLoading(true)

        const payload: Record<string, string> = {
            email: email.trim(),
            password,
        }

        if (isRegister) {
            payload.name = name.trim()
        }

        if (isAdminScope && isRegister) {
            payload.role = role
        }

        try {
            const response = await fetch(`${gatewayBase}${endpoint}`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            })

            const data = (await response.json()) as AuthPayload
            if (!response.ok) {
                setError(data.error || 'Đăng nhập thất bại. Vui lòng thử lại.')
                return
            }

            if (data.role === 'manager') {
                navigate('/manager/dashboard')
                return
            }

            if (data.role === 'staff') {
                navigate('/staff/workspace')
                return
            }

            navigate('/shop')
        } catch {
            setError('Không thể kết nối hệ thống xác thực.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="auth-shell">
            <section className="auth-showcase" aria-hidden="true">
                <img
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCCHgWS6NGIg7H21GSj1zdw9T8riRKgkelPinjiZGthuN9d-40vg04iyOxuaIiIJGKo8aKHvmaz3SibrTT-ZhFQWH2rXkbV_jZ1IZ3gmZwZ3dkifTTQ4GJZ_OrXL18Mo0ogwj4dD713ko3_Z8OGGx2N96qqrJRcWvKqojRjw1ABoBFVdrco3Ez8tOutlQ5OC5GJBwutMjd3yPNgGhDSqgZHud1IgbQj4Lpoi6vIY1fVJ28fF_MMotx3NfxhP0GYKenDIl2d48P9Atq5"
                    alt="Minimal architecture"
                />
                <div className="auth-showcase-overlay" />

                <div className="auth-showcase-content">
                    <h1>The Curated Ledger</h1>
                    <div>
                        <p>
                            An Archive of <strong>Exceptional</strong>
                            <br />
                            Living.
                        </p>
                        <span>
                            {isAdminScope
                                ? 'Quản lý vận hành với giao diện kiến trúc dành cho đội ngũ nội bộ.'
                                : 'Access your private dashboard and manage your collection with our architectural-grade interface.'}
                        </span>
                    </div>
                    <div className="auth-showcase-stats">
                        <div>
                            <strong>12k+</strong>
                            <small>Active Members</small>
                        </div>
                        <div>
                            <strong>04</strong>
                            <small>Global Hubs</small>
                        </div>
                    </div>
                </div>
            </section>

            <section className="auth-form-pane">
                <div className="auth-form-wrap">
                    <div className="auth-scope-switch">
                        <Link className={scope === 'customer' ? 'active' : ''} to={mode === 'login' ? '/auth/login' : '/auth/register'}>
                            Người dùng
                        </Link>
                        <Link className={scope === 'admin' ? 'active' : ''} to={mode === 'login' ? '/admin/login' : '/admin/register'}>
                            Manager & Staff
                        </Link>
                    </div>

                    <header>
                        <h2>{title}</h2>
                        <p>{subtitle}</p>
                    </header>

                    <div className="auth-social-grid">
                        <button type="button">
                            <span className="material-symbols-outlined">google</span>
                            <span>Google</span>
                        </button>
                        <button type="button">
                            <span className="material-symbols-outlined">ios</span>
                            <span>Apple</span>
                        </button>
                    </div>

                    <div className="auth-divider">
                        <span>{isRegister ? 'or create with email' : 'or continue with email'}</span>
                    </div>

                    <form className="auth-form" onSubmit={handleSubmit}>
                        {isRegister && (
                            <label>
                                <span>Full Name</span>
                                <input
                                    required
                                    value={name}
                                    onChange={(event) => setName(event.target.value)}
                                    placeholder="Your full name"
                                    type="text"
                                />
                            </label>
                        )}

                        <label>
                            <span>Email Address</span>
                            <input
                                required
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="name@curatedledger.com"
                                type="email"
                            />
                        </label>

                        <label>
                            <span>Password</span>
                            <input
                                required
                                minLength={6}
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="••••••••"
                                type="password"
                            />
                        </label>

                        {isAdminScope && isRegister && (
                            <label>
                                <span>Vai trò</span>
                                <select value={role} onChange={(event) => setRole(event.target.value as 'staff' | 'manager')}>
                                    <option value="staff">Staff</option>
                                    <option value="manager">Manager</option>
                                </select>
                            </label>
                        )}

                        <label className="auth-remember-row">
                            <input
                                checked={remember}
                                onChange={(event) => setRemember(event.target.checked)}
                                type="checkbox"
                            />
                            <span>Remember me for 30 days</span>
                        </label>

                        {error && <p className="auth-error">{error}</p>}

                        <button className="auth-submit" disabled={loading} type="submit">
                            {loading ? 'Đang xử lý...' : isRegister ? 'Register' : 'Sign In'}
                            <span className="material-symbols-outlined">arrow_forward</span>
                        </button>
                    </form>

                    <footer className="auth-footer-link">
                        {isRegister ? (
                            <p>
                                Đã có tài khoản?
                                <Link to={isAdminScope ? '/admin/login' : '/auth/login'}> Đăng nhập</Link>
                            </p>
                        ) : (
                            <p>
                                Chưa có tài khoản?
                                <Link to={isAdminScope ? '/admin/register' : '/auth/register'}> Đăng ký ngay</Link>
                            </p>
                        )}
                    </footer>
                </div>
            </section>
        </main>
    )
}

function getEndpoint(scope: AuthScope, mode: AuthMode): string {
    if (scope === 'admin' && mode === 'register') {
        return '/api/auth/admin/register/'
    }
    if (scope === 'admin' && mode === 'login') {
        return '/api/auth/admin/login/'
    }
    if (scope === 'customer' && mode === 'register') {
        return '/api/auth/register/'
    }
    return '/api/auth/login/'
}