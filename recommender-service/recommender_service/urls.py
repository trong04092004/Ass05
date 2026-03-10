from django.contrib import admin
from django.views.generic import RedirectView
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from app.views import ViewHistoryViewSet,SearchHistoryViewSet,RecommendationCacheViewSet

router = DefaultRouter()
router.register(r'view-history', ViewHistoryViewSet, basename='viewhistory')
router.register(r'search-history', SearchHistoryViewSet, basename='searchhistory')
router.register(r'recommendations', RecommendationCacheViewSet, basename='recommendation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/api/docs/'), name='root'),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

