import { useEffect, useMemo, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { askRagChat, trackInteractionEvent } from '../ai'
import { getCustomerId } from '../customerSession'
import { formatPrice, productFallbackImage } from '../catalog'

type ChatRecommendation = {
    product_service: string
    product_id: number
    name?: string
    price?: string | number
    image_url?: string
    score: number
    reason: string[]
}

type Role = 'user' | 'bot'

type Message = {
    role: Role
    text: string
    ts: number
    recommendations?: ChatRecommendation[]
}

const QUICK_PROMPTS = [
    'Gợi ý sản phẩm theo ngân sách 500k',
    'Chính sách đổi trả như thế nào?',
    'Tôi muốn sản phẩm phù hợp làm quà tặng',
]

const HISTORY_KEY = 'aeon_chatbot_history_v2'

function normalizeServiceKey(serviceKey?: string): string {
    const normalized = String(serviceKey || 'book').trim().toLowerCase().replace('_', '-')
    if (!normalized) {
        return 'book'
    }

    const aliases: Record<string, string> = {
        books: 'book',
        'book-service': 'book',
        'electronics-service': 'electronics',
        'fashion-service': 'fashion',
        'toy-service': 'toy',
        'toy-service-v2': 'toy',
        'grocery-service': 'grocery',
        'furniture-service': 'furniture',
        'beauty-service': 'beauty',
        'sports-service': 'sports',
        'pet-service': 'pet',
        'stationery-service': 'stationery',
    }

    return aliases[normalized] || normalized
}

function loadHistory(): Message[] {
    try {
        const raw = localStorage.getItem(HISTORY_KEY)
        if (!raw) {
            return []
        }
        const parsed = JSON.parse(raw) as Message[]
        return Array.isArray(parsed) ? parsed.slice(-30) : []
    } catch {
        return []
    }
}

function saveHistory(messages: Message[]) {
    try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-30)))
    } catch {
        // ignore storage errors
    }
}

export function ChatbotWidget() {
    const [open, setOpen] = useState(false)
    const [input, setInput] = useState('')
    const [sending, setSending] = useState(false)
    const [messages, setMessages] = useState<Message[]>(() => {
        const existing = loadHistory()
        if (existing.length > 0) {
            return existing
        }
        return [
            {
                role: 'bot',
                text: 'Xin chào! Tôi là trợ lý mua sắm AI. Bạn cần tư vấn sản phẩm, chính sách giao hàng, hay đổi trả?',
                ts: Date.now(),
            },
        ]
    })

    const listRef = useRef<HTMLDivElement | null>(null)
    const customerId = getCustomerId()

    useEffect(() => {
        saveHistory(messages)
    }, [messages])

    useEffect(() => {
        if (!listRef.current) {
            return
        }
        listRef.current.scrollTop = listRef.current.scrollHeight
    }, [messages, open])

    const canSend = useMemo(() => input.trim().length > 0 && !sending, [input, sending])

    const appendMessage = (message: Message) => {
        setMessages((prev) => [...prev, message])
    }

    const submitMessage = async (text: string) => {
        const clean = text.trim()
        if (!clean || sending) {
            return
        }

        appendMessage({ role: 'user', text: clean, ts: Date.now() })
        setInput('')
        setSending(true)

        try {
            await trackInteractionEvent({
                event_type: 'chat',
                query: clean,
                metadata: {
                    source: 'chatbot_widget',
                    customer_id: customerId,
                },
            })

            const response = await askRagChat(clean)
            const recommendations = Array.isArray(response.personalized_recommendations)
                ? response.personalized_recommendations.slice(0, 3)
                : []
            appendMessage({
                role: 'bot',
                text: response.answer,
                ts: Date.now(),
                recommendations: recommendations.length > 0 ? recommendations : undefined,
            })
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Không thể gửi tin nhắn lúc này.'
            appendMessage({ role: 'bot', text: message, ts: Date.now() })
        } finally {
            setSending(false)
        }
    }

    const onSubmit = (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        void submitMessage(input)
    }

    return (
        <div className={`chatbot-shell${open ? ' open' : ''}`}>
            {open && (
                <section className="chatbot-panel" aria-label="AI Chatbot">
                    <header className="chatbot-header">
                        <div className="chatbot-header-main">
                            <div className="chatbot-avatar" aria-hidden="true">AI</div>
                            <div>
                                <h3>Trợ lý mua sắm AI</h3>
                                <small>Đang hoạt động • RAG + hành vi người dùng</small>
                            </div>
                        </div>
                        <button type="button" onClick={() => setOpen(false)} aria-label="Đóng chatbot">
                            ×
                        </button>
                    </header>

                    <div className="chatbot-messages" ref={listRef}>
                        {messages.map((message) => (
                            <div key={`${message.ts}-${message.role}`} className={`chat-row ${message.role}`}>
                                <div className="chat-bubble-wrap">
                                    <p>{message.text}</p>
                                    {message.recommendations && message.recommendations.length > 0 && (
                                        <div className="chat-recommend-list">
                                            {message.recommendations.map((item) => (
                                                <Link
                                                    key={`${item.product_service}-${item.product_id}`}
                                                    to={`/product/${normalizeServiceKey(item.product_service)}/${item.product_id}`}
                                                    className="chat-recommend-card"
                                                    onClick={() => setOpen(false)}
                                                >
                                                    <div className="chat-recommend-thumb-wrap">
                                                        <img
                                                            className="chat-recommend-thumb"
                                                            src={item.image_url || productFallbackImage(item.name || 'Sản phẩm', normalizeServiceKey(item.product_service))}
                                                            alt={item.name || 'Sản phẩm gợi ý'}
                                                            loading="lazy"
                                                        />
                                                    </div>

                                                    <div className="chat-recommend-content">
                                                        <div className="chat-recommend-title">{item.name || `${item.product_service} #${item.product_id}`}</div>
                                                        <div className="chat-recommend-meta">
                                                            <span>{normalizeServiceKey(item.product_service).toUpperCase()}</span>
                                                            <strong>{item.price !== undefined ? formatPrice(item.price) : 'Xem chi tiết'}</strong>
                                                        </div>
                                                        <span className="chat-recommend-cta">Xem chi tiết</span>
                                                    </div>
                                                </Link>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {sending && (
                            <div className="chat-row bot">
                                <div className="chat-bubble-wrap">
                                    <p className="chat-typing" aria-label="Đang suy nghĩ">
                                        <span />
                                        <span />
                                        <span />
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="chatbot-quick-prompts">
                        {QUICK_PROMPTS.map((prompt) => (
                            <button key={prompt} type="button" onClick={() => void submitMessage(prompt)}>
                                {prompt}
                            </button>
                        ))}
                    </div>

                    <form className="chatbot-input" onSubmit={onSubmit}>
                        <input
                            value={input}
                            onChange={(event) => setInput(event.target.value)}
                            placeholder="Nhập câu hỏi để được tư vấn..."
                            maxLength={500}
                        />
                        <button type="submit" disabled={!canSend}>
                            Gửi
                        </button>
                    </form>
                </section>
            )}

            {!open && (
                <button className="chatbot-trigger" type="button" onClick={() => setOpen(true)}>
                    AI Tư vấn
                </button>
            )}
        </div>
    )
}
