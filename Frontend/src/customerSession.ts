export type CustomerAuthPayload = {
    customer_id?: number
    name?: string
    email?: string
    role?: string
    token?: string
    access?: string
    refresh?: string
}

const CUSTOMER_ACCESS_KEY = 'customer_access_token'
const CUSTOMER_ID_KEY = 'customer_id'
const CUSTOMER_NAME_KEY = 'customer_name'
const CUSTOMER_EMAIL_KEY = 'customer_email'
const CUSTOMER_ROLE_KEY = 'customer_role'

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const gatewayHost = runtimeHost === 'localhost' ? '127.0.0.1' : runtimeHost
export const gatewayBase = `http://${gatewayHost}:18000`

function readCookie(name: string): string {
    if (typeof document === 'undefined') {
        return ''
    }
    const found = document.cookie
        .split(';')
        .map((v) => v.trim())
        .find((v) => v.startsWith(`${name}=`))
    return found ? decodeURIComponent(found.split('=')[1] || '') : ''
}

export function saveCustomerSession(payload: CustomerAuthPayload) {
    const accessToken = payload.access || payload.token || ''
    if (accessToken) {
        localStorage.setItem(CUSTOMER_ACCESS_KEY, accessToken)
    }

    if (typeof payload.customer_id === 'number') {
        localStorage.setItem(CUSTOMER_ID_KEY, String(payload.customer_id))
    }
    if (payload.name) {
        localStorage.setItem(CUSTOMER_NAME_KEY, payload.name)
    }
    if (payload.email) {
        localStorage.setItem(CUSTOMER_EMAIL_KEY, payload.email)
    }
    if (payload.role) {
        localStorage.setItem(CUSTOMER_ROLE_KEY, payload.role)
    }
}

export function getCustomerAccessToken(): string {
    return localStorage.getItem(CUSTOMER_ACCESS_KEY) || ''
}

export function getCustomerId(): number | null {
    const fromStorage = localStorage.getItem(CUSTOMER_ID_KEY)
    const fromCookie = readCookie('customer_id')
    const raw = fromStorage || fromCookie
    const parsed = Number.parseInt(raw || '', 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null
}

export function getCustomerRole(): string {
    const fromStorage = localStorage.getItem(CUSTOMER_ROLE_KEY) || ''
    if (fromStorage) {
        return fromStorage
    }
    return readCookie('auth_role')
}

export function clearCustomerSession() {
    localStorage.removeItem(CUSTOMER_ACCESS_KEY)
    localStorage.removeItem(CUSTOMER_ID_KEY)
    localStorage.removeItem(CUSTOMER_NAME_KEY)
    localStorage.removeItem(CUSTOMER_EMAIL_KEY)
    localStorage.removeItem(CUSTOMER_ROLE_KEY)
}

export function authHeaders(contentType = true): Record<string, string> {
    const headers: Record<string, string> = {}
    const token = getCustomerAccessToken()
    if (token) {
        headers.Authorization = `Bearer ${token}`
    }
    if (contentType) {
        headers['Content-Type'] = 'application/json'
    }
    return headers
}
