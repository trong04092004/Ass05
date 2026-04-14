import { authHeaders, gatewayBase, getCustomerId } from './customerSession'

export type RecommendationItem = {
    product_id: number
    product_service: string
    name: string
    price: string | number
    image_url?: string
    score: number
    reason: string[]
}

export type ChatRagResponse = {
    answer: string
    retrieved_documents: Array<{
        id: number
        title: string
        doc_type: string
        score: number
        snippet: string
    }>
    personalized_recommendations: Array<{
        product_service: string
        product_id: number
        name?: string
        price?: string | number
        image_url?: string
        score: number
        reason: string[]
    }>
    predicted_next_products: Array<{
        product_service: string
        product_id: number
        count: number
    }>
}

export async function fetchRealtimeRecommendations(
    customerId: number,
    opts?: { limit?: number, excludeService?: string, excludeProductId?: number },
): Promise<RecommendationItem[]> {
    const params = new URLSearchParams()
    params.set('limit', String(opts?.limit || 6))
    if (opts?.excludeService) {
        params.set('exclude_service', opts.excludeService)
    }
    if (opts?.excludeProductId) {
        params.set('exclude_product_id', String(opts.excludeProductId))
    }

    const resp = await fetch(
        `${gatewayBase}/api/ai/recommendations/${customerId}/?${params.toString()}`,
        {
            credentials: 'include',
            headers: authHeaders(false),
        },
    )
    if (!resp.ok) {
        return []
    }
    const json = (await resp.json()) as { results?: RecommendationItem[] }
    return Array.isArray(json.results) ? json.results : []
}

export async function fetchMyRealtimeRecommendations(
    opts?: { limit?: number, excludeService?: string, excludeProductId?: number },
): Promise<RecommendationItem[]> {
    const params = new URLSearchParams()
    params.set('limit', String(opts?.limit || 6))
    if (opts?.excludeService) {
        params.set('exclude_service', opts.excludeService)
    }
    if (opts?.excludeProductId) {
        params.set('exclude_product_id', String(opts.excludeProductId))
    }

    const resp = await fetch(
        `${gatewayBase}/api/ai/recommendations/me/?${params.toString()}`,
        {
            credentials: 'include',
            headers: authHeaders(false),
        },
    )
    if (!resp.ok) {
        return []
    }
    const json = (await resp.json()) as { results?: RecommendationItem[] }
    return Array.isArray(json.results) ? json.results : []
}

export async function trackInteractionEvent(payload: {
    event_type: 'view' | 'click' | 'search' | 'cart' | 'purchase' | 'chat'
    product_service?: string
    product_id?: number
    category_id?: number
    query?: string
    metadata?: Record<string, unknown>
}) {
    try {
        const customerId = getCustomerId()
        await fetch(`${gatewayBase}/api/ai/events/`, {
            method: 'POST',
            credentials: 'include',
            headers: authHeaders(),
            body: JSON.stringify({
                ...payload,
                ...(customerId ? { customer_id: customerId } : {}),
            }),
        })
    } catch {
        // Best-effort telemetry.
    }
}

export async function askRagChat(message: string): Promise<ChatRagResponse> {
    const response = await fetch(`${gatewayBase}/api/ai/chat/`, {
        method: 'POST',
        credentials: 'include',
        headers: authHeaders(),
        body: JSON.stringify({ message, top_k: 5 }),
    })

    if (!response.ok) {
        throw new Error('Không thể kết nối chatbot lúc này.')
    }

    return (await response.json()) as ChatRagResponse
}
