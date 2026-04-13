import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { RoleRoute } from './auth'
import { SiteLayout } from './components/SiteLayout'
import { AdminAuthPage } from './pages/AdminAuthPage'
import { AboutPage } from './pages/AboutPage'
import { AccountPage } from './pages/AccountPage'
import { CheckoutPage } from './pages/CheckoutPage'
import { HomePage } from './pages/HomePage'
import { JournalPage } from './pages/JournalPage'
import { ManagerDashboardPage } from './pages/ManagerDashboardPage'
import { ProductDetailPage } from './pages/ProductDetailPage'
import { ShopPage } from './pages/ShopPage'
import { StaffDashboardPage } from './pages/StaffDashboardPage'
import { UserAuthPage } from './pages/UserAuthPage'

function App() {
    return (
        <Routes>
            <Route path="auth/login" element={<UserAuthPage mode="login" />} />
            <Route path="auth/register" element={<UserAuthPage mode="register" />} />
            <Route path="admin/login" element={<AdminAuthPage mode="login" />} />
            <Route path="admin/register" element={<AdminAuthPage mode="register" />} />

            <Route
                path="manager/dashboard"
                element={
                    <RoleRoute allow={['manager']}>
                        <ManagerDashboardPage />
                    </RoleRoute>
                }
            />
            <Route
                path="staff/dashboard"
                element={
                    <RoleRoute allow={['staff', 'manager']}>
                        <StaffDashboardPage />
                    </RoleRoute>
                }
            />
            <Route path="staff/workspace" element={<Navigate to="/staff/dashboard" replace />} />

            <Route path="/" element={<SiteLayout />}>
                <Route index element={<HomePage />} />
                <Route path="shop" element={<ShopPage />} />
                <Route path="product/:serviceKey/:productId" element={<ProductDetailPage />} />
                <Route path="checkout" element={<CheckoutPage />} />
                <Route path="account" element={<AccountPage />} />
                <Route path="about" element={<AboutPage />} />
                <Route path="journal" element={<JournalPage />} />
                <Route path="*" element={<Navigate to="/shop" replace />} />
            </Route>

            <Route path="*" element={<Navigate to="/shop" replace />} />
        </Routes>
    )
}

export default App
