from datetime import timedelta
import os
import json
from urllib.request import urlopen
from urllib.error import URLError


from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import InteractionEvent, RAGDocument
from app.services import (
    build_graph,
    ingest_interaction_event,
    reindex_rag_vectors,
    sync_interactions_to_neo4j,
    train_behavior_model,
)

SEED_SOURCE = 'bootstrap_v1'

FAQ_DOCS = [
    {
        'doc_type': 'policy',
        'title': 'Chính sách đổi trả',
        'content': (
            'Khách hàng được đổi trả trong 7 ngày kể từ ngày nhận hàng nếu sản phẩm lỗi nhà sản xuất '
            'hoặc không đúng mô tả. Sản phẩm cần còn đầy đủ phụ kiện và hóa đơn.'
        ),
    },
    {
        'doc_type': 'policy',
        'title': 'Chính sách giao hàng',
        'content': (
            'Đơn hàng nội thành dự kiến 1-2 ngày, liên tỉnh 3-5 ngày. Đơn hàng đều có mã vận đơn để theo dõi.'
        ),
    },
    {
        'doc_type': 'policy',
        'title': 'Chính sách thanh toán',
        'content': (
            'Hệ thống hỗ trợ COD, chuyển khoản ngân hàng và thẻ. Thanh toán online được xác nhận qua cổng bảo mật.'
        ),
    },
    {
        'doc_type': 'faq',
        'title': 'Gợi ý quà tặng theo ngân sách',
        'content': (
            'Nếu ngân sách dưới 500k, ưu tiên bộ sách bán chạy, đồ gia dụng tiện ích, hoặc quà tặng chăm sóc cá nhân. '
            'AI sẽ ưu tiên các sản phẩm có lịch sử tương tác cao với từng nhóm khách.'
        ),
    },
]


def _load_real_book_ids(limit=3):
    book_service_url = os.environ.get('BOOK_SERVICE_URL', 'http://book-service:8000').rstrip('/')
    fallback_ids = [658, 659, 660]
    try:
        with urlopen(f"{book_service_url}/books/", timeout=5) as resp:
            body = resp.read().decode('utf-8')
        rows = json.loads(body)
        if not isinstance(rows, list):
            return fallback_ids[:limit]

        ids = [int(item.get('id')) for item in rows if item.get('id') is not None]
        ids = [pid for pid in ids if pid > 0]
        unique_ids = []
        for pid in ids:
            if pid not in unique_ids:
                unique_ids.append(pid)
        if not unique_ids:
            return fallback_ids[:limit]
        return unique_ids[:limit]
    except (URLError, ValueError, TypeError):
        return fallback_ids[:limit]


def _seed_events_for_customer(customer_id, base_time, product_ids):
    p1 = product_ids[0]
    p2 = product_ids[1] if len(product_ids) > 1 else product_ids[0]
    p3 = product_ids[2] if len(product_ids) > 2 else product_ids[0]
    return [
        {
            'customer_id': customer_id,
            'event_type': 'search',
            'query': 'quà tặng sinh nhật dưới 500k',
            'metadata': {'seed_source': SEED_SOURCE, 'step': 1},
            'occurred_at': base_time - timedelta(minutes=35),
        },
        {
            'customer_id': customer_id,
            'event_type': 'view',
            'product_service': 'book',
            'product_id': p1,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 2},
            'occurred_at': base_time - timedelta(minutes=30),
        },
        {
            'customer_id': customer_id,
            'event_type': 'click',
            'product_service': 'book',
            'product_id': p1,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 3},
            'occurred_at': base_time - timedelta(minutes=29),
        },
        {
            'customer_id': customer_id,
            'event_type': 'view',
            'product_service': 'book',
            'product_id': p2,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 4},
            'occurred_at': base_time - timedelta(minutes=24),
        },
        {
            'customer_id': customer_id,
            'event_type': 'cart',
            'product_service': 'book',
            'product_id': p2,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 5},
            'occurred_at': base_time - timedelta(minutes=22),
        },
        {
            'customer_id': customer_id,
            'event_type': 'purchase',
            'product_service': 'book',
            'product_id': p2,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 6},
            'occurred_at': base_time - timedelta(minutes=20),
        },
        {
            'customer_id': customer_id,
            'event_type': 'view',
            'product_service': 'book',
            'product_id': p3,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 7},
            'occurred_at': base_time - timedelta(minutes=15),
        },
        {
            'customer_id': customer_id,
            'event_type': 'cart',
            'product_service': 'book',
            'product_id': p3,
            'metadata': {'seed_source': SEED_SOURCE, 'step': 8},
            'occurred_at': base_time - timedelta(minutes=13),
        },
        {
            'customer_id': customer_id,
            'event_type': 'chat',
            'query': 'tôi muốn quà tặng cho bạn gái',
            'metadata': {'seed_source': SEED_SOURCE, 'step': 9},
            'occurred_at': base_time - timedelta(minutes=10),
        },
    ]


class Command(BaseCommand):
    help = 'Seed bootstrap AI data: user behavior events + RAG FAQ documents.'

    def add_arguments(self, parser):
        parser.add_argument('--customer-id', type=int, default=1)

    def handle(self, *args, **options):
        customer_id = options['customer_id']
        now = timezone.now()
        seed_product_ids = _load_real_book_ids(limit=3)

        # Keep seed idempotent by replacing prior seed rows.
        deleted_events, _ = InteractionEvent.objects.filter(metadata__seed_source=SEED_SOURCE).delete()
        self.stdout.write(self.style.WARNING(f'Removed old seed events: {deleted_events}'))

        docs_upserted = 0
        for doc in FAQ_DOCS:
            _, _created = RAGDocument.objects.update_or_create(
                title=doc['title'],
                defaults={
                    'doc_type': doc['doc_type'],
                    'content': doc['content'],
                    'metadata': {'seed_source': SEED_SOURCE},
                },
            )
            docs_upserted += 1

        events = []
        events.extend(_seed_events_for_customer(customer_id, now, seed_product_ids))
        events.extend(_seed_events_for_customer(customer_id + 1, now - timedelta(minutes=5), seed_product_ids))
        events.extend(_seed_events_for_customer(customer_id + 2, now - timedelta(minutes=8), seed_product_ids))

        ingested = 0
        for payload in events:
            ingest_interaction_event(payload)
            ingested += 1

        graph_result = build_graph(full_rebuild=True)
        markov = train_behavior_model(model_type='markov', min_transitions=1, epochs=1)
        rag_result = reindex_rag_vectors()
        neo4j_result = sync_interactions_to_neo4j(full_rebuild=True)

        self.stdout.write(self.style.SUCCESS('AI bootstrap seeding completed.'))
        self.stdout.write(f'customer_id_seeded={customer_id}')
        self.stdout.write(f'seed_product_ids={seed_product_ids}')
        self.stdout.write(f'faq_docs_upserted={docs_upserted}')
        self.stdout.write(f'events_ingested={ingested}')
        self.stdout.write(f'graph_result={graph_result}')
        self.stdout.write(f'active_model={markov.model_name}:{markov.version}')
        self.stdout.write(f'rag_reindex={rag_result}')
        self.stdout.write(f'neo4j_sync={neo4j_result}')
