import math
import os
import re
import importlib
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime

from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    ActiveModelState,
    BehaviorModelSnapshot,
    InteractionEvent,
    KnowledgeEdge,
    KnowledgeNode,
    RecommendationCache,
    RAGDocument,
)
from .deep_learning import (
    infer_gnn_recommendations,
    infer_next_items_from_snapshot,
    sentence_embedding,
    train_gnn_recommender,
    train_gru4rec_model,
    train_transformer_model,
)

EVENT_WEIGHTS = {
    'view': 0.4,
    'click': 1.0,
    'search': 0.3,
    'cart': 2.5,
    'purchase': 5.0,
    'chat': 0.2,
}
GRAPH_BACKEND = os.getenv('GRAPH_BACKEND', 'django').lower()
CHAT_BLOCKLIST_TERMS = [
    'ignore previous instruction',
    'system prompt',
    'bypass',
    'jailbreak',
    'hack',
]

INTENT_PATTERNS = {
    'return_policy': r"doi\s*tra|do\s*i\s*tra|hoan\s*tien|bao\s*hanh",
    'shipping_policy': r"giao\s*hang|van\s*chuyen|ship",
    'payment_policy': r"thanh\s*toan|\bcod\b|chuyen\s*khoan|the\s*(tin\s*dung|ngan\s*hang|quoc\s*te|atm)",
    'recommendation': r"goi\s*y|tu\s*van|de\s*xuat|nen\s*mua|qua\s*tang",
}


def _user_node_id(customer_id):
    return f"u:{customer_id}"


def _product_node_id(product_service, product_id):
    return f"p:{product_service}:{product_id}"


def _category_node_id(category_id):
    return f"c:{category_id}"


def _query_node_id(query_text):
    normalized = query_text.strip().lower()
    return f"q:{normalized}"


def _tokenize(text):
    return re.findall(r"[a-zA-Z0-9_\-]+", (text or '').lower())


def build_text_embedding(text, dim=128):
    return sentence_embedding(text)


def _neo4j_driver():
    try:
        neo4j_module = importlib.import_module('neo4j')
    except Exception:
        return None

    GraphDatabase = getattr(neo4j_module, 'GraphDatabase', None)
    if GraphDatabase is None:
        return None
    uri = os.getenv('NEO4J_URI', '')
    user = os.getenv('NEO4J_USER', '')
    password = os.getenv('NEO4J_PASSWORD', '')
    if not uri or not user or not password:
        return None
    return GraphDatabase.driver(uri, auth=(user, password))


def _cosine_distance_cls():
    try:
        pgvector_module = importlib.import_module('pgvector.django')
    except Exception:
        return None
    return getattr(pgvector_module, 'CosineDistance', None)


def _neo4j_upsert_event(event):
    driver = _neo4j_driver()
    if driver is None:
        return False

    weight = EVENT_WEIGHTS.get(event.event_type, 0.2)
    try:
        with driver.session() as session:
            session.run(
                """
                MERGE (u:User {customer_id: $customer_id})
                """,
                customer_id=event.customer_id,
            )

            if event.query:
                session.run(
                    """
                    MERGE (u:User {customer_id: $customer_id})
                    MERGE (q:Query {value: $query})
                    MERGE (u)-[r:SEARCHED]->(q)
                    ON CREATE SET r.weight = $weight, r.count = 1
                    ON MATCH SET r.weight = r.weight + $weight, r.count = coalesce(r.count, 0) + 1
                    """,
                    customer_id=event.customer_id,
                    query=event.query.strip().lower(),
                    weight=weight,
                )

            if event.product_id is not None:
                session.run(
                    """
                    MERGE (u:User {customer_id: $customer_id})
                    MERGE (p:Product {product_key: $product_key})
                    SET p.product_id = $product_id, p.product_service = $product_service
                    MERGE (u)-[r:INTERACTED]->(p)
                    ON CREATE SET r.weight = $weight, r.count = 1
                    ON MATCH SET r.weight = r.weight + $weight, r.count = coalesce(r.count, 0) + 1
                    MERGE (u)-[e:EVENT {type: $event_type}]->(p)
                    ON CREATE SET e.weight = $weight, e.count = 1
                    ON MATCH SET e.weight = e.weight + $weight, e.count = coalesce(e.count, 0) + 1
                    """,
                    customer_id=event.customer_id,
                    product_key=f"{event.product_service}:{event.product_id}",
                    product_id=event.product_id,
                    product_service=event.product_service,
                    event_type=event.event_type,
                    weight=weight,
                )

                if event.category_id is not None:
                    session.run(
                        """
                        MERGE (p:Product {product_key: $product_key})
                        MERGE (c:Category {category_id: $category_id})
                        MERGE (p)-[:BELONGS_TO]->(c)
                        """,
                        product_key=f"{event.product_service}:{event.product_id}",
                        category_id=event.category_id,
                    )
        return True
    except Exception:
        return False
    finally:
        driver.close()


def sync_interactions_to_neo4j(customer_id=None, full_rebuild=False):
    driver = _neo4j_driver()
    if driver is None:
        return {'synced_events': 0, 'status': 'neo4j_not_configured'}

    try:
        with driver.session() as session:
            if full_rebuild:
                session.run("MATCH (n) DETACH DELETE n")

        events = InteractionEvent.objects.all().order_by('occurred_at')
        if customer_id is not None:
            events = events.filter(customer_id=customer_id)

        count = 0
        for event in events.iterator(chunk_size=1000):
            if _neo4j_upsert_event(event):
                count += 1

        with driver.session() as session:
            session.run("MATCH ()-[r:SIMILAR_TO]->() DELETE r")
            session.run(
                """
                MATCH (u:User)-[:INTERACTED]->(p:Product)
                WITH u, collect(p) AS products
                UNWIND range(0, size(products)-2) AS i
                UNWIND range(i+1, size(products)-1) AS j
                WITH products[i] AS p1, products[j] AS p2, count(*) AS common
                MERGE (p1)-[r:SIMILAR_TO]->(p2)
                SET r.score = toFloat(common)
                MERGE (p2)-[r2:SIMILAR_TO]->(p1)
                SET r2.score = toFloat(common)
                """
            )

        return {'synced_events': count, 'status': 'ok'}
    except Exception:
        return {'synced_events': 0, 'status': 'neo4j_unavailable'}
    finally:
        driver.close()


def _neo4j_recommend(customer_id, limit=10):
    driver = _neo4j_driver()
    if driver is None:
        return []

    try:
        with driver.session() as session:
            rows = list(
                session.run(
                    """
                    MATCH (u:User {customer_id: $customer_id})-[i:INTERACTED]->(p:Product)
                    OPTIONAL MATCH (p)-[s:SIMILAR_TO]->(p2:Product)
                    WITH p, i.weight AS direct_weight, p2, coalesce(s.score, 0.0) AS sim_score
                    WITH collect({service: p.product_service, pid: p.product_id, score: direct_weight, reason: 'direct_behavior'}) +
                         collect(CASE WHEN p2 IS NULL THEN NULL ELSE {service: p2.product_service, pid: p2.product_id, score: 0.35 * sim_score, reason: 'similar_graph'} END) AS rows
                    UNWIND rows AS row
                    WITH row WHERE row IS NOT NULL AND row.pid IS NOT NULL
                    WITH row.service AS service, row.pid AS pid, sum(row.score) AS score, collect(row.reason) AS reasons
                    RETURN service, pid, score, reasons
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    customer_id=customer_id,
                    limit=limit,
                )
            )

        return [
            {
                'product_service': row['service'] or 'book',
                'product_id': row['pid'],
                'score': round(float(row['score'] or 0), 4),
                'reason': sorted(set(row['reasons'] or []))[:5],
            }
            for row in rows
        ]
    except Exception:
        return []
    finally:
        driver.close()


def _get_or_create_node(node_type, external_id, properties=None):
    node, created = KnowledgeNode.objects.get_or_create(
        node_type=node_type,
        external_id=external_id,
        defaults={'properties': properties or {}},
    )
    if not created and properties:
        merged = dict(node.properties or {})
        merged.update(properties)
        node.properties = merged
        node.save(update_fields=['properties', 'updated_at'])
    return node


def _upsert_weighted_edge(source, target, relation_type, delta_weight, event_time):
    edge, created = KnowledgeEdge.objects.get_or_create(
        source=source,
        target=target,
        relation_type=relation_type,
        defaults={
            'weight': delta_weight,
            'evidence_count': 1,
            'last_event_at': event_time,
        },
    )
    if not created:
        edge.weight += delta_weight
        edge.evidence_count += 1
        edge.last_event_at = max(edge.last_event_at, event_time)
        edge.save(update_fields=['weight', 'evidence_count', 'last_event_at', 'updated_at'])
    return edge


@transaction.atomic
def ingest_interaction_event(payload):
    payload.setdefault('product_service', 'book')
    event = InteractionEvent.objects.create(**payload)
    if GRAPH_BACKEND == 'neo4j':
        _neo4j_upsert_event(event)
    _build_graph_for_event(event)
    return event


def _build_graph_for_event(event):
    user = _get_or_create_node('user', _user_node_id(event.customer_id), {'customer_id': event.customer_id})
    event_time = event.occurred_at or timezone.now()
    event_weight = EVENT_WEIGHTS.get(event.event_type, 0.2)

    if event.query:
        query = _get_or_create_node('query', _query_node_id(event.query), {'query': event.query.strip()})
        _upsert_weighted_edge(user, query, 'searched', event_weight, event_time)

    product = None
    if event.product_id is not None:
        product_service = event.product_service or 'book'
        product = _get_or_create_node(
            'product',
            _product_node_id(product_service, event.product_id),
            {'product_id': event.product_id, 'product_service': product_service},
        )
        _upsert_weighted_edge(user, product, 'interacted', event_weight, event_time)
        _upsert_weighted_edge(user, product, f"event_{event.event_type}", event_weight, event_time)

    if event.category_id is not None and product is not None:
        category = _get_or_create_node('category', _category_node_id(event.category_id), {'category_id': event.category_id})
        _upsert_weighted_edge(product, category, 'belongs_to', 1.0, event_time)


def build_graph(customer_id=None, full_rebuild=False):
    if GRAPH_BACKEND == 'neo4j':
        neo4j_result = sync_interactions_to_neo4j(customer_id=customer_id, full_rebuild=full_rebuild)
        return {
            'events_processed': neo4j_result.get('synced_events', 0),
            'similarity_edges': 0,
            'customer_id': customer_id,
            'full_rebuild': full_rebuild,
            'backend': 'neo4j',
            'status': neo4j_result.get('status', 'ok'),
        }

    if full_rebuild:
        KnowledgeEdge.objects.all().delete()
        KnowledgeNode.objects.all().delete()

    events = InteractionEvent.objects.all().order_by('occurred_at')
    if customer_id is not None:
        events = events.filter(customer_id=customer_id)

    count = 0
    for event in events.iterator(chunk_size=1000):
        _build_graph_for_event(event)
        count += 1

    similar_edges = _refresh_product_similarity()
    return {
        'events_processed': count,
        'similarity_edges': similar_edges,
        'customer_id': customer_id,
        'full_rebuild': full_rebuild,
        'backend': 'django',
    }


def _refresh_product_similarity():
    KnowledgeEdge.objects.filter(relation_type='similar_to').delete()

    interactions = KnowledgeEdge.objects.filter(relation_type='interacted').select_related('source', 'target')
    user_to_products = defaultdict(set)
    product_popularity = Counter()

    for edge in interactions:
        if edge.source.node_type == 'user' and edge.target.node_type == 'product':
            user_to_products[edge.source_id].add(edge.target_id)
            product_popularity[edge.target_id] += 1

    pair_count = Counter()
    for products in user_to_products.values():
        product_list = sorted(products)
        for idx, left in enumerate(product_list):
            for right in product_list[idx + 1:]:
                pair_count[(left, right)] += 1

    created = 0
    for (left, right), common in pair_count.items():
        denom = math.sqrt(max(product_popularity[left], 1) * max(product_popularity[right], 1))
        score = common / denom
        if score <= 0:
            continue

        left_node = KnowledgeNode.objects.get(id=left)
        right_node = KnowledgeNode.objects.get(id=right)
        _upsert_weighted_edge(left_node, right_node, 'similar_to', score, timezone.now())
        _upsert_weighted_edge(right_node, left_node, 'similar_to', score, timezone.now())
        created += 2

    return created


def _recommend_products_from_django_graph(customer_id, limit=10):
    user_node = KnowledgeNode.objects.filter(node_type='user', external_id=_user_node_id(customer_id)).first()
    if not user_node:
        return []

    interacted_edges = list(
        KnowledgeEdge.objects.filter(
            source=user_node,
            relation_type='interacted',
            target__node_type='product',
        ).select_related('target')
    )

    score_map = defaultdict(float)
    reasons = defaultdict(list)

    for edge in interacted_edges:
        pid = edge.target.properties.get('product_id')
        service = edge.target.properties.get('product_service', 'book')
        if pid is None:
            continue
        key = f"{service}:{pid}"
        score_map[key] += edge.weight
        reasons[key].append('direct_behavior')

        similar_edges = KnowledgeEdge.objects.filter(
            source=edge.target,
            relation_type='similar_to',
            target__node_type='product',
        ).select_related('target')
        for sim in similar_edges:
            sim_pid = sim.target.properties.get('product_id')
            sim_service = sim.target.properties.get('product_service', 'book')
            if sim_pid is None:
                continue
            sim_key = f"{sim_service}:{sim_pid}"
            score_map[sim_key] += 0.35 * sim.weight
            reasons[sim_key].append(f"similar_to_{service}:{pid}")

    if not score_map:
        popular = (
            KnowledgeEdge.objects.filter(relation_type='interacted', target__node_type='product')
            .select_related('target')
            .order_by('-weight')[:limit]
        )
        for edge in popular:
            pid = edge.target.properties.get('product_id')
            service = edge.target.properties.get('product_service', 'book')
            if pid is not None:
                key = f"{service}:{pid}"
                score_map[key] += edge.weight
                reasons[key].append('global_popularity')

    ranked = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:limit]
    results = []
    for key, score in ranked:
        service, pid = key.split(':', 1)
        results.append(
            {
                'product_service': service,
                'product_id': int(pid),
                'score': round(score, 4),
                'reason': sorted(set(reasons[key]))[:5],
            }
        )
    return results


def recommend_products(customer_id, limit=10):
    if GRAPH_BACKEND == 'neo4j':
        results = _neo4j_recommend(customer_id=customer_id, limit=limit)
        if not results:
            results = _recommend_products_from_django_graph(customer_id=customer_id, limit=limit)
    else:
        results = _recommend_products_from_django_graph(customer_id=customer_id, limit=limit)

    active_snapshot = get_active_behavior_model_snapshot()
    gnn_snapshot = None
    if active_snapshot and active_snapshot.model_name == 'gnn_v1':
        gnn_snapshot = active_snapshot
    else:
        gnn_snapshot = BehaviorModelSnapshot.objects.filter(model_name='gnn_v1').order_by('-trained_at').first()
    if gnn_snapshot:
        gnn_rows = infer_gnn_recommendations(gnn_snapshot.state_json, customer_id=customer_id, limit=limit)
        if gnn_rows:
            merged = {}
            for row in results:
                key = f"{row['product_service']}:{row['product_id']}"
                merged[key] = row
            for row in gnn_rows:
                key = f"{row['product_service']}:{row['product_id']}"
                if key in merged:
                    merged[key]['score'] = round(0.7 * merged[key]['score'] + 0.3 * row['score'], 4)
                    merged[key]['reason'] = sorted(set(merged[key]['reason'] + row['reason']))[:6]
                else:
                    merged[key] = row
            results = sorted(merged.values(), key=lambda r: r['score'], reverse=True)[:limit]

    # Optional LLM re-rank (trained from user_data.csv). If model artifacts are missing,
    # fall back to the existing ranking.
    try:
        from .llm_service import suggest_action_score
    except Exception:
        suggest_action_score = None

    if suggest_action_score and results:
        now = timezone.now()
        last_event = (
            InteractionEvent.objects.filter(customer_id=customer_id, product_id__isnull=False)
            .order_by('-occurred_at')
            .first()
        )

        base_action = 'view'
        base_context = 'home_page'
        if last_event:
            action_map = {
                'view': 'view',
                'click': 'view',
                'search': 'search_click',
                'cart': 'add_to_cart',
                'purchase': 'purchase',
                'chat': 'share',
            }
            context_map = {
                'view': 'product_detail',
                'click': 'category_page',
                'search': 'search_results',
                'cart': 'cart',
                'purchase': 'checkout',
                'chat': 'home_page',
            }
            base_action = action_map.get(last_event.event_type, base_action)
            base_context = context_map.get(last_event.event_type, base_context)

        for row in results:
            try:
                llm_score = float(
                    suggest_action_score(
                        {
                            'user_id': customer_id,
                            'product_id': int(row['product_id']),
                            'action': base_action,
                            'context': base_context,
                            'hour': now.hour,
                            'day_of_week': now.weekday(),
                        },
                        target_action='purchase',
                    )
                    or 0.0
                )
            except Exception:
                llm_score = 0.0

            if llm_score > 0:
                row['score'] = round(float(row.get('score', 0.0)) + (0.2 * llm_score), 4)
                row['reason'] = sorted(set((row.get('reason') or []) + ['llm_purchase_intent']))[:6]

        results = sorted(results, key=lambda r: r['score'], reverse=True)[:limit]

    RecommendationCache.objects.update_or_create(
        customer_id=customer_id,
        defaults={
            'recommended_book_ids': results,
            'reason': f'graph_hybrid_{GRAPH_BACKEND}',
        },
    )
    return results


def train_markov_behavior_model(min_transitions=1):
    events = InteractionEvent.objects.all().order_by('customer_id', 'occurred_at')

    action_transitions = defaultdict(Counter)
    product_transitions = defaultdict(Counter)
    by_customer = defaultdict(list)

    for event in events.iterator(chunk_size=2000):
        by_customer[event.customer_id].append(event)

    transition_count = 0
    for customer_events in by_customer.values():
        for idx in range(len(customer_events) - 1):
            current = customer_events[idx]
            nxt = customer_events[idx + 1]
            action_transitions[current.event_type][nxt.event_type] += 1
            transition_count += 1

            if current.product_id is not None and nxt.product_id is not None:
                current_key = f"{current.product_service}:{current.product_id}"
                next_key = f"{nxt.product_service}:{nxt.product_id}"
                product_transitions[current_key][next_key] += 1

    filtered_action = {
        key: {k: v for k, v in counter.items() if v >= min_transitions}
        for key, counter in action_transitions.items()
    }
    filtered_product = {
        key: {k: v for k, v in counter.items() if v >= min_transitions}
        for key, counter in product_transitions.items()
    }

    version = datetime.utcnow().strftime('markov_%Y%m%d%H%M%S')
    snapshot = BehaviorModelSnapshot.objects.create(
        model_name='markov_v1',
        version=version,
        state_json={
            'action_transitions': filtered_action,
            'product_transitions': filtered_product,
        },
        metrics_json={
            'customers': len(by_customer),
            'transitions': transition_count,
            'min_transitions': min_transitions,
        },
    )
    return snapshot


def train_behavior_model(model_type='markov', min_transitions=1, epochs=3):
    model_type = (model_type or 'markov').lower()
    if model_type == 'markov':
        snapshot = train_markov_behavior_model(min_transitions=min_transitions)
        set_active_behavior_model_snapshot(snapshot, reason='manual_train_markov')
        return snapshot

    if model_type == 'gru4rec':
        trained = train_gru4rec_model(epochs=epochs)
        if trained is None:
            snapshot = train_markov_behavior_model(min_transitions=min_transitions)
            set_active_behavior_model_snapshot(snapshot, reason='fallback_markov_from_gru4rec')
            return snapshot
        version = datetime.utcnow().strftime('gru4rec_%Y%m%d%H%M%S')
        snapshot = BehaviorModelSnapshot.objects.create(
            model_name='gru4rec_v1',
            version=version,
            state_json=trained['state'],
            metrics_json=trained['metrics'],
        )
        set_active_behavior_model_snapshot(snapshot, reason='manual_train_gru4rec')
        return snapshot

    if model_type == 'transformer':
        trained = train_transformer_model(epochs=epochs)
        if trained is None:
            snapshot = train_markov_behavior_model(min_transitions=min_transitions)
            set_active_behavior_model_snapshot(snapshot, reason='fallback_markov_from_transformer')
            return snapshot
        version = datetime.utcnow().strftime('transformer_%Y%m%d%H%M%S')
        snapshot = BehaviorModelSnapshot.objects.create(
            model_name='transformer_v1',
            version=version,
            state_json=trained['state'],
            metrics_json=trained['metrics'],
        )
        set_active_behavior_model_snapshot(snapshot, reason='manual_train_transformer')
        return snapshot

    if model_type == 'gnn':
        trained = train_gnn_recommender(epochs=max(10, epochs * 10))
        if trained is None:
            snapshot = train_markov_behavior_model(min_transitions=min_transitions)
            set_active_behavior_model_snapshot(snapshot, reason='fallback_markov_from_gnn')
            return snapshot
        version = datetime.utcnow().strftime('gnn_%Y%m%d%H%M%S')
        snapshot = BehaviorModelSnapshot.objects.create(
            model_name='gnn_v1',
            version=version,
            state_json=trained['state'],
            metrics_json=trained['metrics'],
        )
        set_active_behavior_model_snapshot(snapshot, reason='manual_train_gnn')
        return snapshot

    snapshot = train_markov_behavior_model(min_transitions=min_transitions)
    set_active_behavior_model_snapshot(snapshot, reason='fallback_markov_unknown_type')
    return snapshot


def _snapshot_quality_score(snapshot):
    metrics = snapshot.metrics_json or {}
    if snapshot.model_name == 'gnn_v1':
        samples = float(metrics.get('samples', 0))
        users = float(metrics.get('users', 0))
        items = float(metrics.get('items', 0))
        return (math.log1p(samples) * 0.65) + (math.log1p(users + items) * 0.35)

    if snapshot.model_name in ('gru4rec_v1', 'transformer_v1'):
        acc = float(metrics.get('train_accuracy', 0))
        samples = float(metrics.get('samples', 0))
        return (acc * 0.8) + (min(math.log1p(samples) / 10.0, 1.0) * 0.2)

    transitions = float(metrics.get('transitions', 0))
    return min(math.log1p(transitions) / 10.0, 1.0)


def set_active_behavior_model_snapshot(snapshot, reason='auto_switch'):
    state, _ = ActiveModelState.objects.get_or_create(model_family='behavior')
    metadata = dict(state.metadata or {})
    metadata.update(
        {
            'reason': reason,
            'model_name': snapshot.model_name,
            'version': snapshot.version,
            'quality_score': round(_snapshot_quality_score(snapshot), 6),
        }
    )
    state.active_behavior_snapshot = snapshot
    state.metadata = metadata
    state.save(update_fields=['active_behavior_snapshot', 'metadata', 'updated_at'])
    return state


def get_active_behavior_model_snapshot():
    state = ActiveModelState.objects.filter(model_family='behavior').select_related('active_behavior_snapshot').first()
    if state and state.active_behavior_snapshot:
        return state.active_behavior_snapshot
    return BehaviorModelSnapshot.objects.order_by('-trained_at').first()


def auto_switch_behavior_model(min_samples=1):
    candidates = [
        s for s in BehaviorModelSnapshot.objects.order_by('-trained_at')
        if float((s.metrics_json or {}).get('samples', (s.metrics_json or {}).get('transitions', 0)) or 0) >= min_samples
    ]
    if not candidates:
        return None

    best = max(candidates, key=_snapshot_quality_score)
    set_active_behavior_model_snapshot(best, reason='auto_switch_by_metric')
    return best


def retrain_and_auto_switch(models=('gru4rec', 'transformer', 'gnn'), min_transitions=1, epochs=3):
    trained = []
    for model_type in models:
        try:
            snap = train_behavior_model(model_type=model_type, min_transitions=min_transitions, epochs=epochs)
            trained.append({'model_name': snap.model_name, 'version': snap.version})
        except Exception as exc:
            trained.append({'model_name': model_type, 'error': str(exc)})

    best = auto_switch_behavior_model(min_samples=1)
    return {
        'trained': trained,
        'active': {
            'model_name': best.model_name if best else None,
            'version': best.version if best else None,
        },
    }


def predict_next_products(customer_id, limit=5):
    snapshot = get_active_behavior_model_snapshot()
    if not snapshot:
        return []

    last_event = (
        InteractionEvent.objects.filter(customer_id=customer_id, product_id__isnull=False)
        .order_by('-occurred_at')
        .first()
    )
    if not last_event:
        return []

    source_key = f"{last_event.product_service}:{last_event.product_id}"
    if snapshot.model_name in ('gru4rec_v1', 'transformer_v1'):
        return infer_next_items_from_snapshot(snapshot.state_json, source_item_key=source_key, limit=limit)

    transitions = snapshot.state_json.get('product_transitions', {})
    next_probs = transitions.get(source_key, {})
    ranked = sorted(next_probs.items(), key=lambda x: x[1], reverse=True)[:limit]
    output = []
    for node_key, count in ranked:
        service, pid = node_key.split(':', 1)
        output.append({'product_service': service, 'product_id': int(pid), 'count': count})
    return output


def _document_score(query_tokens, doc):
    doc_tokens = _tokenize(f"{doc.title} {doc.content}")
    if not doc_tokens:
        return 0.0
    doc_counter = Counter(doc_tokens)
    overlap = sum(doc_counter[token] for token in query_tokens)
    return overlap / math.sqrt(len(doc_tokens))


def retrieve_rag_documents(message, top_k=5):
    query_vector = build_text_embedding(message)
    cosine_distance_cls = _cosine_distance_cls()
    if cosine_distance_cls is not None and connection.vendor == 'postgresql':
        try:
            docs = (
                RAGDocument.objects.exclude(Q(embedding__isnull=True))
                .annotate(distance=cosine_distance_cls('embedding', query_vector))
                .order_by('distance')[:top_k]
            )
            vector_results = [
                {
                    'id': doc.id,
                    'title': doc.title,
                    'doc_type': doc.doc_type,
                    'score': round(1.0 - float(doc.distance), 4),
                    'snippet': doc.content[:280],
                }
                for doc in docs
            ]

            if vector_results:
                return vector_results
        except Exception:
            # Fall back to lexical retrieval when pgvector type/operators are unavailable.
            pass

    query_tokens = _tokenize(message)
    lexical_scored = []
    for doc in RAGDocument.objects.all().iterator(chunk_size=300):
        score = _document_score(query_tokens, doc)
        if score > 0:
            lexical_scored.append((score, doc))

    lexical_scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            'id': doc.id,
            'title': doc.title,
            'doc_type': doc.doc_type,
            'score': round(score, 4),
            'snippet': doc.content[:280],
        }
        for score, doc in lexical_scored[:top_k]
    ]


def reindex_rag_vectors():
    updated = 0
    for doc in RAGDocument.objects.all().iterator(chunk_size=500):
        vector = build_text_embedding(f"{doc.title} {doc.content}")
        RAGDocument.objects.filter(id=doc.id).update(
            token_count=len((doc.content or '').split()),
            embedding_hint=vector,
            embedding=vector,
        )
        updated += 1
    return {'documents_indexed': updated}


def _is_guardrail_blocked(message):
    lowered = (message or '').lower()
    return any(term in lowered for term in CHAT_BLOCKLIST_TERMS)


def _detect_intent(message):
    raw = str(message or '').lower()
    text = ''.join(ch for ch in unicodedata.normalize('NFD', raw) if unicodedata.category(ch) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    for intent, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, text):
            return intent
    return 'general'


def _trim_sentence(text, max_len=220):
    clean = re.sub(r"\s+", ' ', str(text or '').strip())
    if not clean:
        return ''
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 1].rstrip() + '…'


def chat_with_rag(message, customer_id=None, top_k=5):
    if _is_guardrail_blocked(message):
        return {
            'answer': 'Tôi không thể hỗ trợ yêu cầu này. Bạn hãy đặt câu hỏi về sản phẩm, mua sắm, giao hàng hoặc đổi trả.',
            'retrieved_documents': [],
            'personalized_recommendations': [],
            'predicted_next_products': [],
            'citations': [],
            'blocked': True,
        }

    docs = retrieve_rag_documents(message, top_k=top_k)
    recommendations = []
    next_products = []
    if customer_id is not None:
        recommendations = recommend_products(customer_id=customer_id, limit=5)
        next_products = predict_next_products(customer_id=customer_id, limit=5)

    intent = _detect_intent(message)

    if docs:
        top_doc = docs[0]
        title = top_doc.get('title') or 'tài liệu nội bộ'
        snippet = _trim_sentence(top_doc.get('snippet') or '')

        if intent == 'recommendation' and recommendations:
            answer = 'Mình đã hiểu nhu cầu của bạn và đã chọn các sản phẩm phù hợp ngay bên dưới. Bạn có thể mở Xem chi tiết để xem nhanh từng sản phẩm.'
        elif intent == 'return_policy':
            answer = 'Chính sách đổi trả: bạn có thể đổi/trả trong 7 ngày nếu sản phẩm lỗi hoặc không đúng mô tả, và cần giữ đủ phụ kiện/hóa đơn.'
        elif intent == 'shipping_policy':
            answer = 'Về giao hàng: nội thành thường 1-2 ngày, liên tỉnh 3-5 ngày và luôn có mã vận đơn để theo dõi.'
        elif intent == 'payment_policy':
            answer = 'Shop hỗ trợ COD, chuyển khoản ngân hàng và thanh toán thẻ. Thanh toán online được xác nhận qua cổng bảo mật.'
        else:
            answer = f"Theo {title}: {snippet}"

        citations = [
            {
                'document_id': item['id'],
                'title': item['title'],
                'score': item['score'],
            }
            for item in docs
        ]
    else:
        answer = (
            "Mình chưa thấy đủ dữ liệu để trả lời chính xác. "
            "Bạn nói rõ thêm ngân sách, danh mục hoặc mục đích mua để mình tư vấn đúng ý hơn nhé."
        )
        citations = []

    return {
        'answer': answer,
        'retrieved_documents': docs,
        'personalized_recommendations': recommendations,
        'predicted_next_products': next_products,
        'citations': citations,
        'blocked': False,
    }
