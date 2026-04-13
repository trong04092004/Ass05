export type AuthPayload = {
    customer_id?: number
    name?: string
    email?: string
    role?: string
    token?: string
    access?: string
    refresh?: string
    error?: string
}

const ACCESS_KEY = 'backoffice_access_token'
const ROLE_KEY = 'backoffice_role'

export function saveBackofficeSession(payload: AuthPayload) {
    const access = payload.access || payload.token || ''
    if (access) {
        localStorage.setItem(ACCESS_KEY, access)
    }
    if (payload.role) {
        localStorage.setItem(ROLE_KEY, payload.role)
    }
}

export function getBackofficeAccessToken(): string {
    return localStorage.getItem(ACCESS_KEY) || ''
}

export function clearBackofficeSession() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(ROLE_KEY)
}
