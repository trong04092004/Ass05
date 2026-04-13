import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'

export type AuthRole = 'customer' | 'staff' | 'manager' | ''

export function getAuthRoleFromCookie(): AuthRole {
    if (typeof document === 'undefined') {
        return ''
    }

    const roleCookie = document.cookie
        .split(';')
        .map((entry) => entry.trim())
        .find((entry) => entry.startsWith('auth_role='))

    if (!roleCookie) {
        return ''
    }

    const value = decodeURIComponent(roleCookie.split('=')[1] || '')
    if (value === 'customer' || value === 'staff' || value === 'manager') {
        return value
    }
    return ''
}

export function getBackofficeRole(): AuthRole {
    if (typeof window === 'undefined') {
        return ''
    }

    const role = localStorage.getItem('backoffice_role') || ''
    if (role === 'customer' || role === 'staff' || role === 'manager') {
        return role
    }
    return ''
}

type RoleRouteProps = {
    allow: Array<'staff' | 'manager'>
    children: ReactNode
}

export function RoleRoute({ allow, children }: RoleRouteProps) {
    const role = getAuthRoleFromCookie() || getBackofficeRole()
    if (!allow.includes(role as 'staff' | 'manager')) {
        return <Navigate to="/admin/login" replace />
    }
    return <>{children}</>
}
