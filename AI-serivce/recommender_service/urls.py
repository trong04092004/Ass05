from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.views import (
    ViewHistoryViewSet,
    SearchHistoryViewSet,
    RecommendationCacheViewSet,
    InteractionEventViewSet,
    KnowledgeNodeViewSet,
    KnowledgeEdgeViewSet,
    BehaviorModelSnapshotViewSet,
    RAGDocumentViewSet,
    AIOrchestratorViewSet,
)

router = DefaultRouter()
router.register(r'view-history', ViewHistoryViewSet, basename='viewhistory')
router.register(r'search-history', SearchHistoryViewSet, basename='searchhistory')
router.register(r'recommendations', RecommendationCacheViewSet, basename='recommendation')
router.register(r'interaction-events', InteractionEventViewSet, basename='interactionevent')
router.register(r'graph/nodes', KnowledgeNodeViewSet, basename='graph-node')
router.register(r'graph/edges', KnowledgeEdgeViewSet, basename='graph-edge')
router.register(r'behavior-models', BehaviorModelSnapshotViewSet, basename='behavior-model')
router.register(r'rag-documents', RAGDocumentViewSet, basename='rag-document')
router.register(r'ai', AIOrchestratorViewSet, basename='ai-orchestrator')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/api/docs/'), name='root'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

