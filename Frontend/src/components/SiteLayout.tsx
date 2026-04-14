import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearBackofficeSession } from '../backofficeAuth'
import { clearCustomerSession, gatewayBase, getCustomerAccessToken, getCustomerId } from '../customerSession'
import { ChatbotWidget } from './ChatbotWidget'

export function SiteLayout() {
    const navigate = useNavigate()
    const isAuthenticated = Boolean(getCustomerId() || getCustomerAccessToken())

    const handleLogout = async () => {
        try {
            await fetch(`${gatewayBase}/api/auth/logout/`, {
                method: 'POST',
                credentials: 'include',
            })
        } catch {
            // Ignore network errors here; local cleanup still signs user out on client.
        }

        clearCustomerSession()
        clearBackofficeSession()

        document.cookie = 'auth_role=; Max-Age=0; path=/'
        document.cookie = 'customer_id=; Max-Age=0; path=/'

        navigate('/auth/login')
    }

    return (
        <div className="app-shell">
            <nav className="top-nav">
                <div className="brand">Aeon Commerce</div>
                <div className="top-links">
                    <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')} end>
                        Home
                    </NavLink>
                    <NavLink to="/shop" className={({ isActive }) => (isActive ? 'active' : '')}>
                        Shop
                    </NavLink>
                    <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>
                        Giới thiệu
                    </NavLink>
                    <NavLink to="/journal" className={({ isActive }) => (isActive ? 'active' : '')}>
                        Tạp chí
                    </NavLink>
                </div>
                <div className="top-tools">
                    {isAuthenticated ? (
                        <button type="button" className="logout-btn" onClick={() => void handleLogout()}>
                            Đăng xuất
                        </button>
                    ) : (
                        <Link to="/auth/login" className="login-link-btn">
                            Đăng nhập
                        </Link>
                    )}
                    {isAuthenticated && (
                        <>
                            <Link to="/account" aria-label="account" className="account-link-btn">
                                <span className="material-symbols-outlined">account_circle</span>
                            </Link>
                            <Link to="/checkout" aria-label="cart" className="account-link-btn cart-button">
                                <span className="material-symbols-outlined">shopping_bag</span>
                                <span className="cart-dot" aria-hidden="true" />
                            </Link>
                        </>
                    )}
                </div>
            </nav>

            <main className="page-main">
                <Outlet />
            </main>

            <footer className="site-footer">
                <div className="footer-column footer-brand">
                    <h4>Aeon Commerce</h4>
                    <p>Thiết lập chuẩn mực mới cho trải nghiệm mua sắm hiện đại với định hướng tinh tuyển và bền vững.</p>
                </div>
                <div className="footer-column">
                    <h5>Bộ sưu tập</h5>
                    <a href="/shop">Hàng mới về</a>
                    <a href="/shop">Góc làm việc tại nhà</a>
                    <a href="/shop">Thiết bị cá nhân</a>
                    <a href="/shop">Thời trang</a>
                </div>
                <div className="footer-column">
                    <h5>Thông tin</h5>
                    <a href="#">Vận chuyển</a>
                    <a href="#">Đổi trả</a>
                    <a href="#">Chính sách bảo mật</a>
                    <a href="#">Điều khoản dịch vụ</a>
                </div>
                <div className="footer-column">
                    <h5>Kết nối</h5>
                    <div className="footer-icons">
                        <span className="material-symbols-outlined">public</span>
                        <span className="material-symbols-outlined">mail</span>
                        <span className="material-symbols-outlined">share</span>
                    </div>
                    <p className="copyright">© 2026 Aeon Commerce. Tinh tuyển có chủ đích.</p>
                </div>
            </footer>

            <ChatbotWidget />
        </div>
    )
}
