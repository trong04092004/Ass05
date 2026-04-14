from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ViewHistory
from .models import SearchHistory
from .models import RecommendationCache
from .models import InteractionEvent, KnowledgeNode, KnowledgeEdge, BehaviorModelSnapshot, RAGDocument
from .serializers import (
    ViewHistorySerializer,
    SearchHistorySerializer,
    RecommendationCacheSerializer,
    InteractionEventSerializer,
    KnowledgeNodeSerializer,
    KnowledgeEdgeSerializer,
    BehaviorModelSnapshotSerializer,
    RAGDocumentSerializer,
    BuildGraphSerializer,
    TrainBehaviorSerializer,
    RetrainScheduleSerializer,
    RecommendRequestSerializer,
    ChatRequestSerializer,
)
from .services import (
    auto_switch_behavior_model,
    build_graph,
    chat_with_rag,
    get_active_behavior_model_snapshot,
    ingest_interaction_event,
    recommend_products,
    reindex_rag_vectors,
    retrain_and_auto_switch,
    sync_interactions_to_neo4j,
    train_behavior_model,
    build_text_embedding,
)

class ViewHistoryViewSet(viewsets.ModelViewSet):
    queryset = ViewHistory.objects.all()
    serializer_class = ViewHistorySerializer

class SearchHistoryViewSet(viewsets.ModelViewSet):
    queryset = SearchHistory.objects.all()
    serializer_class = SearchHistorySerializer

class RecommendationCacheViewSet(viewsets.ModelViewSet):
    queryset = RecommendationCache.objects.all()
    serializer_class = RecommendationCacheSerializer


class InteractionEventViewSet(viewsets.ModelViewSet):
    queryset = InteractionEvent.objects.all()
    serializer_class = InteractionEventSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = ingest_interaction_event(serializer.validated_data)
        output = self.get_serializer(event)
        return Response(output.data, status=status.HTTP_201_CREATED)


class KnowledgeNodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KnowledgeNode.objects.all()
    serializer_class = KnowledgeNodeSerializer


class KnowledgeEdgeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KnowledgeEdge.objects.select_related('source', 'target').all()
    serializer_class = KnowledgeEdgeSerializer


class BehaviorModelSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BehaviorModelSnapshot.objects.all()
    serializer_class = BehaviorModelSnapshotSerializer


class RAGDocumentViewSet(viewsets.ModelViewSet):
    queryset = RAGDocument.objects.all()
    serializer_class = RAGDocumentSerializer

    def perform_create(self, serializer):
        content = serializer.validated_data.get('content', '')
        title = serializer.validated_data.get('title', '')
        vector = build_text_embedding(f"{title} {content}")
        serializer.save(token_count=len(content.split()), embedding_hint=vector, embedding=vector)

    def perform_update(self, serializer):
        title = serializer.validated_data.get('title', serializer.instance.title)
        content = serializer.validated_data.get('content', serializer.instance.content)
        vector = build_text_embedding(f"{title} {content}")
        serializer.save(token_count=len(content.split()), embedding_hint=vector, embedding=vector)


class AIOrchestratorViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], url_path='build-graph')
    def build_graph_action(self, request):
        serializer = BuildGraphSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        result = build_graph(
            customer_id=payload.get('customer_id'),
            full_rebuild=payload.get('full_rebuild', False),
        )
        return Response(result)

    @action(detail=False, methods=['post'], url_path='train-behavior')
    def train_behavior(self, request):
        serializer = TrainBehaviorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snapshot = train_behavior_model(
            model_type=serializer.validated_data.get('model_type', 'markov'),
            min_transitions=serializer.validated_data.get('min_transitions', 1),
            epochs=serializer.validated_data.get('epochs', 3),
        )
        return Response(BehaviorModelSnapshotSerializer(snapshot).data)

    @action(detail=False, methods=['post'], url_path='recommend')
    def recommend(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        results = recommend_products(
            customer_id=serializer.validated_data['customer_id'],
            limit=serializer.validated_data.get('limit', 10),
        )
        return Response({'results': results})

    @action(detail=False, methods=['post'], url_path='chat')
    def chat(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = chat_with_rag(
            message=serializer.validated_data['message'],
            customer_id=serializer.validated_data.get('customer_id'),
            top_k=serializer.validated_data.get('top_k', 5),
        )
        return Response(result)

    @action(detail=False, methods=['post'], url_path='reindex-rag')
    def reindex_rag(self, request):
        result = reindex_rag_vectors()
        return Response(result)

    @action(detail=False, methods=['post'], url_path='sync-neo4j')
    def sync_neo4j(self, request):
        customer_id = request.data.get('customer_id')
        full_rebuild = bool(request.data.get('full_rebuild', False))
        result = sync_interactions_to_neo4j(customer_id=customer_id, full_rebuild=full_rebuild)
        return Response(result)

    @action(detail=False, methods=['post'], url_path='retrain-auto-switch')
    def retrain_auto_switch(self, request):
        serializer = RetrainScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = retrain_and_auto_switch(
            models=tuple(serializer.validated_data.get('models', ['gru4rec', 'transformer', 'gnn'])),
            min_transitions=serializer.validated_data.get('min_transitions', 1),
            epochs=serializer.validated_data.get('epochs', 3),
        )
        return Response(result)

    @action(detail=False, methods=['post'], url_path='auto-switch')
    def auto_switch(self, request):
        best = auto_switch_behavior_model(min_samples=1)
        if not best:
            return Response({'active': None, 'status': 'no_candidate'})
        return Response({'active': {'model_name': best.model_name, 'version': best.version}, 'status': 'ok'})

    @action(detail=False, methods=['get'], url_path='active-model')
    def active_model(self, request):
        snapshot = get_active_behavior_model_snapshot()
        if not snapshot:
            return Response({'active': None})
        return Response(
            {
                'active': {
                    'model_name': snapshot.model_name,
                    'version': snapshot.version,
                    'metrics': snapshot.metrics_json,
                }
            }
        )

