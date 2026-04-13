export type ServiceConfig = {
    key: string
    name: string
    url: string
    endpoint: string
}

export type Product = {
    id: number
    name: string
    sku: string
    brand?: string
    description?: string
    price: string | number
    stock?: number
    stock_quantity?: number
    image_url?: string | null
}

export type ShopProduct = Product & {
    serviceKey: string
    serviceName: string
    normalizedPrice: number
}

export type ProductServiceKey = ServiceConfig['key']

const IMAGE_QUERY_BASE = 'https://loremflickr.com/1200/900'

const SERVICE_CONTEXT_TAGS: Record<ProductServiceKey, string[]> = {
    book: ['book', 'reading'],
    electronics: ['technology', 'gadget'],
    fashion: ['fashion', 'clothing'],
    toy: ['toy', 'kids'],
    grocery: ['food', 'grocery'],
    furniture: ['furniture', 'interior'],
    beauty: ['cosmetics', 'skincare'],
    sports: ['fitness', 'sport'],
    pet: ['pet', 'animal'],
    stationery: ['stationery', 'office'],
}

const TERM_REPLACEMENTS: Array<[string, string[]]> = [
    ['nước tương', ['soy', 'sauce']],
    ['mật ong', ['honey']],
    ['bơ đậu phộng', ['peanut', 'butter']],
    ['keo dán', ['glue', 'stick']],
    ['kéo học sinh', ['scissors']],
    ['mũ lưỡi trai', ['cap', 'hat']],
    ['thảm yoga', ['yoga', 'mat']],
    ['găng tay tập gym', ['gym', 'gloves']],
    ['bàn phím', ['keyboard']],
    ['chuột máy tính', ['computer', 'mouse']],
    ['ổ cứng', ['external', 'hard', 'drive']],
]

const STOP_WORDS = new Set([
    'va', 'voi', 'cho', 'cua', 'the', 'la', 'co', 'khong', 'it', 'nhieu', 'dang', 'mau', 'hop', 'chai', 'hu', 'goi', 'cai',
    'và', 'với', 'cho', 'của', 'thể', 'là', 'có', 'không', 'ít', 'nhiều', 'dạng', 'màu', 'hộp', 'chai', 'hũ', 'gói', 'cái',
])

function removeVietnameseTones(input: string): string {
    return input
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd')
        .replace(/Đ/g, 'D')
}

function buildTagsFromName(name: string, serviceKey?: ProductServiceKey): string[] {
    const normalized = removeVietnameseTones((name || '').toLowerCase())

    for (const [needle, replacement] of TERM_REPLACEMENTS) {
        if (normalized.includes(needle)) {
            const serviceTags = serviceKey ? SERVICE_CONTEXT_TAGS[serviceKey] : []
            return [...replacement, ...serviceTags].slice(0, 5)
        }
    }

    const wordTags = normalized
        .replace(/[^a-z0-9\s]/g, ' ')
        .split(/\s+/)
        .filter((token) => token.length >= 3 && !STOP_WORDS.has(token))
        .slice(0, 3)

    const serviceTags = serviceKey ? SERVICE_CONTEXT_TAGS[serviceKey] : []
    const merged = [...wordTags, ...serviceTags]
    return Array.from(new Set(merged)).slice(0, 5)
}

function contextualImageByName(name: string, serviceKey?: ProductServiceKey): string {
    const tags = buildTagsFromName(name, serviceKey)
    const query = tags.length > 0 ? tags.join(',') : 'product,shopping'
    return `${IMAGE_QUERY_BASE}/${query}`
}

export function productFallbackImage(name: string, serviceKey?: ProductServiceKey): string {
    return toImageProxyUrl(contextualImageByName(name, serviceKey))
}

export function productInlinePlaceholder(_name: string): string {
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='640' height='820' viewBox='0 0 640 820'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'><stop offset='0%' stop-color='#eef2ff'/><stop offset='100%' stop-color='#dbe7ff'/></linearGradient></defs><rect width='640' height='820' fill='url(#g)'/><g fill='none' stroke='#9bb2e6' stroke-width='6'><rect x='88' y='120' width='464' height='580' rx='22'/><path d='M120 612h400'/><circle cx='320' cy='390' r='86'/><path d='M260 390l40 40 80-84'/></g></svg>`
    return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`
}

const runtimeHost = typeof window !== 'undefined' ? window.location.hostname : 'localhost'
const resolvedHost = runtimeHost === 'localhost' ? '127.0.0.1' : runtimeHost
const serviceBase = (port: number) => `http://${resolvedHost}:${port}`

export const services: ServiceConfig[] = [
    { key: 'book', name: 'Sách', url: serviceBase(18000), endpoint: '/api/books/' },
    { key: 'electronics', name: 'Điện tử', url: serviceBase(18012), endpoint: '/products/' },
    { key: 'fashion', name: 'Thời trang', url: serviceBase(18013), endpoint: '/products/' },
    { key: 'toy', name: 'Đồ chơi', url: serviceBase(18014), endpoint: '/products/' },
    { key: 'grocery', name: 'Tạp hóa', url: serviceBase(18015), endpoint: '/products/' },
    { key: 'furniture', name: 'Nội thất', url: serviceBase(18016), endpoint: '/products/' },
    { key: 'beauty', name: 'Làm đẹp', url: serviceBase(18017), endpoint: '/products/' },
    { key: 'sports', name: 'Thể thao', url: serviceBase(18018), endpoint: '/products/' },
    { key: 'pet', name: 'Thú cưng', url: serviceBase(18019), endpoint: '/products/' },
    { key: 'stationery', name: 'Văn phòng phẩm', url: serviceBase(18020), endpoint: '/products/' },
]

export async function loadProducts(service: ServiceConfig): Promise<Product[]> {
    const resp = await fetch(`${service.url}${service.endpoint}`)
    if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
    }
    const json = await resp.json()

    const rows = Array.isArray(json) ? json : Array.isArray(json?.results) ? json.results : []

    return rows.map((row: Record<string, unknown>, index: number) => {
        const id = typeof row.id === 'number' ? row.id : index + 1
        const title = typeof row.title === 'string' ? row.title.trim() : ''
        const name = typeof row.name === 'string' ? row.name.trim() : title
        const isbn = typeof row.isbn === 'string' ? row.isbn.trim() : ''
        const sku = typeof row.sku === 'string' ? row.sku.trim() : isbn || `${service.key.toUpperCase()}-${id}`
        const description = typeof row.description === 'string' ? row.description : ''

        return {
            id,
            name,
            sku,
            brand: typeof row.brand === 'string' ? row.brand : (typeof row.author === 'string' ? row.author : service.name),
            description,
            price: typeof row.price === 'string' || typeof row.price === 'number' ? row.price : 0,
            stock: typeof row.stock === 'number' ? row.stock : undefined,
            stock_quantity: typeof row.stock_quantity === 'number' ? row.stock_quantity : undefined,
            image_url: typeof row.image_url === 'string' ? row.image_url : null,
        }
    })
}

export function toNumberPrice(value: string | number): number {
    const asNumber = typeof value === 'number' ? value : Number.parseFloat(value)
    return Number.isFinite(asNumber) ? asNumber : 0
}

export function formatPrice(value: string | number): string {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND',
        maximumFractionDigits: 0,
    }).format(toNumberPrice(value))
}

export function productImage(item: Product): string {
    return productImageForService(item)
}

function normalizeImageUrl(raw: string, service?: ServiceConfig): string {
    if (!raw) {
        return ''
    }

    if (raw.startsWith('data:') || raw.startsWith('blob:')) {
        return raw
    }

    if (/^https?:\/\//i.test(raw)) {
        return raw
    }

    if (raw.startsWith('//')) {
        const protocol = typeof window !== 'undefined' ? window.location.protocol : 'http:'
        return `${protocol}${raw}`
    }

    if (service) {
        const base = service.url.replace(/\/+$/, '')
        const path = raw.startsWith('/') ? raw : `/${raw}`
        return `${base}${path}`
    }

    return raw
}

function toImageProxyUrl(url: string): string {
    if (!url || /^data:|^blob:/i.test(url)) {
        return url
    }

    try {
        const parsed = new URL(url)
        const host = parsed.hostname.toLowerCase()
        const localHost = runtimeHost.toLowerCase()

        // Keep local/static service images direct; proxy external CDNs to avoid hotlink failures.
        if (host === 'localhost' || host === '127.0.0.1' || host === localHost) {
            return url
        }

        return `https://images.weserv.nl/?url=${encodeURIComponent(url)}&w=900&output=jpg`
    } catch {
        return url
    }
}

function isUntrustedImageUrl(url: string): boolean {
    if (!url) {
        return true
    }

    const lowered = url.toLowerCase()
    return (
        lowered.includes('picsum.photos') ||
        lowered.includes('placehold.co') ||
        lowered.includes('placeholder.com') ||
        lowered.includes('via.placeholder.com')
    )
}

export function productImageForService(item: Product, service?: ServiceConfig): string {
    const raw = (item.image_url || '').trim()
    const normalized = normalizeImageUrl(raw, service)
    const contextualImage = contextualImageByName(item.name || '', service?.key)

    if (normalized && !isUntrustedImageUrl(normalized)) {
        return toImageProxyUrl(normalized)
    }

    return toImageProxyUrl(contextualImage)
}
