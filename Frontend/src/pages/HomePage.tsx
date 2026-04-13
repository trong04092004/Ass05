import { useEffect, useMemo, useState } from 'react'
import { formatPrice, loadProducts, productFallbackImage, productImageForService, productInlinePlaceholder, services } from '../catalog'
import type { Product, ServiceConfig } from '../catalog'

type ApiResult = {
    loading: boolean
    error: string
    data: Product[]
}

type ArrivalCard = {
    id: string
    category: string
    name: string
    price: string
    image: string
    badge?: string
}

const fallbackArrivals: ArrivalCard[] = [
    {
        id: 'axis-01',
        category: 'ĐỒNG HỒ',
        name: 'Monolith Axis-01',
        price: '$1,240',
        image: productInlinePlaceholder('Monolith Axis-01'),
        badge: 'NEW',
    },
    {
        id: 'kinetic-strider',
        category: 'GIÀY DÉP',
        name: 'Kinetic Strider',
        price: '$180',
        image: productInlinePlaceholder('Kinetic Strider'),
    },
    {
        id: 'void-s1',
        category: 'ÂM THANH',
        name: 'Void S1 Studio',
        price: '$450',
        image: productInlinePlaceholder('Void S1 Studio'),
    },
    {
        id: 'vellum-low-top',
        category: 'THIẾT YẾU',
        name: 'Vellum Low-Top',
        price: '$210',
        image: productInlinePlaceholder('Vellum Low-Top'),
    },
]

export function HomePage() {
    const [active] = useState<ServiceConfig>(services[0])
    const [result, setResult] = useState<ApiResult>({ loading: false, error: '', data: [] })

    const arrivals = useMemo<ArrivalCard[]>(() => {
        if (!result.data.length) {
            return fallbackArrivals
        }
        return result.data.slice(0, 4).map((item, index) => ({
            id: `${active.key}-${item.id}`,
            category: (item.brand || active.name).toUpperCase(),
            name: item.name,
            price: formatPrice(item.price),
            image: productImageForService(item, active),
            badge: index === 0 ? 'NEW' : undefined,
        }))
    }, [active.key, active.name, result.data])

    useEffect(() => {
        void fetchHomeArrivals(services[0])
    }, [])

    const fetchHomeArrivals = async (service: ServiceConfig) => {
        setResult({ loading: true, error: '', data: [] })
        try {
            const data = await loadProducts(service)
            setResult({ loading: false, error: '', data })
        } catch (e) {
            const message = e instanceof Error ? e.message : 'Failed to load data'
            setResult({ loading: false, error: message, data: [] })
        }
    }

    const handleImageError = (name: string) => (event: React.SyntheticEvent<HTMLImageElement>) => {
        const target = event.currentTarget
        target.onerror = null
        target.src = productFallbackImage(name, active.key)
    }

    return (
        <>
            <header className="hero hero-editorial">
                <img
                    className="hero-bg"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuC-dmyJtPJ1otYR6R34poFW0m-8UZT14bVmHIvtFtT5s-qewz_AcQwXVljA2fdu-KrVSzx_7ya3ZDjkQL687gTt9ll3-0SXEvTF-gbz5NsYKABWT_dqbMoQKENMm0ABMuUtQioqE7bBq74O5j-GE_vraJqmutI207m1Kglb_q9R2Y6OD63l7H-X-jvwA8uK6SGxLMRrpaertmh3NkQKnW9U09i6vzce6EQm5VfslrWi2p3FWPjBf-yPLhB4MkwgN8_-aeADAR50VsYn"
                    alt="Architectural interior"
                />
                <div className="hero-overlay" />
                <div className="hero-content">
                    <p className="edition">Phiên bản số 01</p>
                    <h1>
                        Kiến trúc
                        <br />
                        của Thương mại
                    </h1>
                    <div className="hero-cta-row">
                        <a className="primary-btn" href="/shop">Mua sắm bộ sưu tập</a>
                        <p className="hero-sub">Tinh tuyển những sản phẩm cao cấp với góc nhìn chuẩn xác trong thiết kế và công năng bền vững theo thời gian.</p>
                    </div>
                </div>
            </header>

            <section className="section curated-spheres">
                <div className="section-head">
                    <div>
                        <h2>Không gian tinh tuyển</h2>
                        <p className="section-note">Được tuyển chọn bởi đội ngũ thẩm mỹ dành cho lối sống hiện đại.</p>
                    </div>
                    <div className="catalog-link-wrap">
                        <a className="catalog-link" href="/shop">
                            Xem tất cả danh mục <span aria-hidden="true">→</span>
                        </a>
                    </div>
                </div>

                <div className="sphere-grid">
                    <article className="sphere-card sphere-card-large">
                        <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuAhQ_dQdtCMTGvgRaSbVqoQywj_IlY529-7pylfPvdbFJX3jLtfIH2eEDkVmhOKX1i3j7-BmW8Ylb5E5IoooS6UrlCe-wlCQqbgLYTo0IEZpkhgrNFnBWJ1p9VElmoXLRwTTjPmoqbbTs7Fa1cAJg2km45SEqbiTZurMVk0_2LiVa5dyAuKCQFNExQyyFEOS_7_JKp7VyEhg-rRLjOkrjoyoa6dIfMEkdsgfBK8WFj2enkInFC5RtAbPHOgqPBY49AjzuxLUwh7a2ql" alt="Apparel" />
                        <div className="sphere-overlay">
                            <h3>Thời trang</h3>
                            <p>Trang phục tối giản, bền bỉ và linh hoạt cho nhịp sống hằng ngày.</p>
                            <span>Khám phá bộ sưu tập</span>
                        </div>
                    </article>

                    <article className="sphere-card sphere-card-small">
                        <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBa6cW1PP5f7BVgl6pC5MNMSEVO4eMuSlKBiIkWd_n-z-XasdGkKdpjit-nElkKeAYn4W-ytTRF_QfW0tPaR7h0AYiAVw62coOeAqBxFOvJeJ0YrSck6QWc6-bJIBeXIs56RZOOUgGIynX3PNBkGp1xE5YF9AES3Nb9PqLW-m-zH0Z47AzBshZ7lPmhBG891_LD5nM0aBrTxwFtdbGF0rqTjPctGVUPHgH8nG0ksBDifCZsnukcUkltfoNQ7CLmiCX0-YD-fJAfasQT" alt="Electronics" />
                        <div className="sphere-overlay">
                            <h3>Điện tử</h3>
                            <span>Xem công nghệ</span>
                        </div>
                    </article>

                    <article className="sphere-card sphere-card-wide">
                        <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuAmXYtn3qIjzNH_UexasBUzuUPnQqp2hjnYd8fCuAPnkdb6b-cEHKZ4punAgdEgRkJypuX7YacuIS5Uc3wPvd9K-tY8PZkPR8IzttcSLVxow1iDZsiMl_gSNkghAUrgPT02NzbtgtvLxu-v5SPSTTEfgIEQBTkR_2gYMuZ9i_lj9lE6JzhhQUWMBcjA7J2z5u5uxL_zu5PeqjjNoHxcDEDC5ZO3M3zhtL3J6K7rX8J--vItiJzcpPG9UKdhRiNJ27hVe1XQ6AUIwb3s" alt="Home Decor" />
                        <div className="sphere-overlay sphere-overlay-center">
                            <h3>Trang trí nhà</h3>
                            <button type="button">Tinh chỉnh không gian</button>
                        </div>
                    </article>
                </div>
            </section>

            <section className="section arrivals editorial-arrivals">
                <div className="section-head arrivals-head">
                    <div>
                        <span>Mới cập nhật</span>
                        <h2>Sản phẩm mới về</h2>
                    </div>
                </div>

                {result.loading && <p className="state-line">Đang tải sản phẩm từ {active.name}...</p>}
                {!result.loading && result.error && (
                    <p className="state-line error">Không thể kết nối tới {active.name}: {result.error}</p>
                )}
                {!result.loading && !result.error && arrivals.length === 0 && (
                    <p className="state-line">Hiện chưa có sản phẩm nào trong {active.name}.</p>
                )}

                {arrivals.length > 0 && (
                    <div className="arrivals-grid">
                        {arrivals.map((item) => (
                            <article key={item.id} className="product-card">
                                <div className="product-media">
                                    <img src={item.image} alt={item.name} onError={handleImageError(item.name)} />
                                    {item.badge && <span className="product-badge">{item.badge}</span>}
                                    <button type="button" className="product-action" aria-label={`Add ${item.name} to cart`}>+</button>
                                </div>
                                <p className="product-brand">{item.category}</p>
                                <h3>{item.name}</h3>
                                <p className="product-price">{item.price}</p>
                            </article>
                        ))}
                    </div>
                )}
            </section>

            <section className="section journal-highlight">
                <div className="journal-media">
                    <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4AgaJWnMqbN0DjRaBrp83PVyZO_MqQLVb3BdaEbZyQyDiZanDLkGmd4_-VlPSKDvuI7C3LEoUT8f8VKn4jovl1IF_fTtuXngLt8u0q1dTny-FmyGqK2IBCyKd5FNC-W6q76xUVZzCKLysO1eM-mhZKx5hZ_q8Rbd5pJjmoX770XToiZWtxVn3CCC4mL8DyudNAUJcrH_vvxlFm-YCDW5zuxY-8q8LAVlwLOnYzBIyoUFhG0YC84eb-8k4scHj43UUZOgSDdtrNNSf" alt="Journal spotlight" />
                    <div className="journal-quote">
                        <p>"The object is the anchor of the environment. Its quality dictates the room's energy."</p>
                        <span>Elara Voss, Chief Curator</span>
                    </div>
                </div>
                <div className="journal-copy">
                    <span>Tạp chí Aeon</span>
                    <h2>Triết lý sống tinh gọn</h2>
                    <p>
                        Chúng tôi tin rằng những món đồ xung quanh bạn nên tối giản, hữu dụng và có chủ đích rõ ràng. Trong số tạp chí này,
                        chúng tôi khám phá giao điểm giữa kiến trúc hiện đại và thiết bị gia dụng giàu công năng.
                    </p>
                    <ul>
                        <li>
                            <strong>01</strong>
                            <div>
                                <h4>Kết cấu của sự tĩnh lặng</h4>
                                <p>Cách chất liệu chạm tay ảnh hưởng đến trải nghiệm công nghệ trong không gian sống.</p>
                            </div>
                        </li>
                        <li>
                            <strong>02</strong>
                            <div>
                                <h4>Bàn tay phía sau sản phẩm</h4>
                                <p>Theo dấu tay nghề thủ công đứng sau bộ sưu tập Axis.</p>
                            </div>
                        </li>
                    </ul>
                    <a href="/journal">Đọc tạp chí</a>
                </div>
            </section>

            <section className="registry-strip">
                <div className="registry-word" aria-hidden="true">AEON</div>
                <div className="registry-content">
                    <h2>Tham gia danh sách ưu tiên</h2>
                    <p>Nhận quyền truy cập sớm vào các bộ sưu tập mới và góc nhìn thiết kế từ đội ngũ Aeon.</p>
                    <form className="registry-form" onSubmit={(event) => event.preventDefault()}>
                        <input type="email" placeholder="Địa chỉ email" aria-label="Địa chỉ email" />
                        <button type="submit">Đăng ký</button>
                    </form>
                </div>
            </section>
        </>
    )
}
